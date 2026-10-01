from pathlib import Path

import gc

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq


# ============================================================
# PROJECT PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DATA_DIR = PROJECT_ROOT / "data" / "processed"
SUMMARY_DIR = PROCESSED_DATA_DIR / "summary"


PROCESSED_DATA_DIR.mkdir(
    parents=True,
    exist_ok=True
)

SUMMARY_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# ============================================================
# PROCESSING SETTINGS
# ============================================================

# Smaller batches reduce RAM usage.
BATCH_SIZE = 100_000


# ============================================================
# ANALYTICAL PERIOD
# ============================================================

ANALYTICAL_START = pd.Timestamp(
    "2024-01-01"
)

ANALYTICAL_END = pd.Timestamp(
    "2026-07-31 23:59:59"
)


# ============================================================
# COLUMN STANDARDIZATION
# ============================================================

COMMON_RENAME_MAP = {
    "VendorID": "vendor_id",
    "PULocationID": "pickup_location_id",
    "DOLocationID": "dropoff_location_id",
    "RatecodeID": "rate_code_id",
    "store_and_fwd_flag": "store_and_forward_flag",
    "Airport_fee": "airport_fee",
    "ehail_fee": "ehail_fee",
}


def standardize_columns(df):

    df = df.rename(
        columns=COMMON_RENAME_MAP
    )

    # --------------------------------------------------------
    # Yellow Taxi
    # --------------------------------------------------------

    if "tpep_pickup_datetime" in df.columns:

        df = df.rename(
            columns={
                "tpep_pickup_datetime": "pickup_datetime",
                "tpep_dropoff_datetime": "dropoff_datetime",
            }
        )

    # --------------------------------------------------------
    # Green Taxi
    # --------------------------------------------------------

    if "lpep_pickup_datetime" in df.columns:

        df = df.rename(
            columns={
                "lpep_pickup_datetime": "pickup_datetime",
                "lpep_dropoff_datetime": "dropoff_datetime",
            }
        )

    return df


# ============================================================
# DATA TYPE STANDARDIZATION
# ============================================================

def standardize_data_types(df):

    # --------------------------------------------------------
    # Datetime columns
    # --------------------------------------------------------

    for column in [
        "pickup_datetime",
        "dropoff_datetime",
    ]:

        if column in df.columns:

            df[column] = pd.to_datetime(
                df[column],
                errors="coerce"
            )

    # --------------------------------------------------------
    # Integer-like columns
    # --------------------------------------------------------

    integer_columns = [
        "vendor_id",
        "pickup_location_id",
        "dropoff_location_id",
        "rate_code_id",
        "payment_type",
        "trip_type",
    ]

    for column in integer_columns:

        if column in df.columns:

            df[column] = pd.to_numeric(
                df[column],
                errors="coerce"
            ).astype("Int64")

    # --------------------------------------------------------
    # Passenger count
    #
    # float64 is intentional because missing values exist.
    # --------------------------------------------------------

    if "passenger_count" in df.columns:

        df["passenger_count"] = pd.to_numeric(
            df["passenger_count"],
            errors="coerce"
        ).astype("float64")

    # --------------------------------------------------------
    # Numeric columns
    # --------------------------------------------------------

    numeric_columns = [
        "trip_distance",
        "fare_amount",
        "extra",
        "mta_tax",
        "tip_amount",
        "tolls_amount",
        "improvement_surcharge",
        "total_amount",
        "congestion_surcharge",
        "airport_fee",
        "ehail_fee",
    ]

    for column in numeric_columns:

        if column in df.columns:

            df[column] = pd.to_numeric(
                df[column],
                errors="coerce"
            ).astype("float64")

    return df


# ============================================================
# TRIP METRICS
# ============================================================

def create_trip_metrics(df):

    # --------------------------------------------------------
    # Trip duration
    # --------------------------------------------------------

    df["trip_duration_minutes"] = (
        df["dropoff_datetime"]
        - df["pickup_datetime"]
    ).dt.total_seconds() / 60

    # --------------------------------------------------------
    # Pickup calendar fields
    # --------------------------------------------------------

    df["pickup_date"] = (
        df["pickup_datetime"].dt.date
    )

    df["pickup_year"] = (
        df["pickup_datetime"].dt.year
    )

    df["pickup_month"] = (
        df["pickup_datetime"].dt.month
    )

    df["pickup_day"] = (
        df["pickup_datetime"].dt.day
    )

    df["pickup_hour"] = (
        df["pickup_datetime"].dt.hour
    )

    df["pickup_day_of_week"] = (
        df["pickup_datetime"].dt.dayofweek
    )

    df["is_weekend"] = (
        df["pickup_day_of_week"] >= 5
    )

    # --------------------------------------------------------
    # Average speed
    # --------------------------------------------------------

    df["avg_speed_mph"] = np.where(
        df["trip_duration_minutes"] > 0,
        df["trip_distance"]
        / (df["trip_duration_minutes"] / 60),
        np.nan
    )

    return df


# ============================================================
# DATA QUALITY FLAGS
# ============================================================

def create_quality_flags(df):

    # --------------------------------------------------------
    # Duration
    # --------------------------------------------------------

    df["is_negative_duration"] = (
        df["trip_duration_minutes"] < 0
    )

    df["is_zero_duration"] = (
        df["trip_duration_minutes"] == 0
    )

    # --------------------------------------------------------
    # Distance
    # --------------------------------------------------------

    df["is_negative_distance"] = (
        df["trip_distance"] < 0
    )

    df["is_zero_distance"] = (
        df["trip_distance"] == 0
    )

    # --------------------------------------------------------
    # Financial values
    # --------------------------------------------------------

    df["is_negative_fare"] = (
        df["fare_amount"] < 0
    )

    df["is_negative_total"] = (
        df["total_amount"] < 0
    )

    # --------------------------------------------------------
    # Speed
    # --------------------------------------------------------

    df["is_high_speed"] = (
        df["avg_speed_mph"] > 100
    )

    # --------------------------------------------------------
    # Timestamp validity
    #
    # IMPORTANT:
    # Pickup datetime determines the analytical period.
    #
    # A July 31 pickup with an August 1 dropoff is valid
    # and should NOT be flagged merely because the dropoff
    # occurs in August.
    #
    # These records are FLAGGED, not removed.
    # --------------------------------------------------------

    df["is_invalid_timestamp"] = (
        (df["pickup_datetime"] < ANALYTICAL_START)
        | (df["pickup_datetime"] > ANALYTICAL_END)
        | df["pickup_datetime"].isna()
    )

    return df


# ============================================================
# MEMORY-EFFICIENT ROW FILTER
# ============================================================

def remove_negative_duration_rows(df):

    """
    Remove only rows with negative trip duration.

    This implementation avoids:

        df.iloc[mask].copy()

    because that operation can trigger a large Pandas
    block-consolidation allocation.

    Instead, each column is filtered independently using
    NumPy arrays and then reconstructed into a DataFrame.
    """

    negative_duration_mask = (
        df["is_negative_duration"].to_numpy(
            dtype=bool,
            na_value=False
        )
    )

    if not negative_duration_mask.any():

        return df

    keep_mask = ~negative_duration_mask

    filtered_columns = {}

    for column in df.columns:

        values = df[column].to_numpy(
            copy=False
        )

        filtered_columns[column] = values[keep_mask]

    filtered_df = pd.DataFrame(
        filtered_columns
    )

    return filtered_df


# ============================================================
# PROCESS ONE BATCH
# ============================================================

def process_batch(
    df,
    taxi_type,
    source_file
):

    # --------------------------------------------------------
    # 1. Standardize columns
    # --------------------------------------------------------

    df = standardize_columns(df)

    # --------------------------------------------------------
    # 2. Standardize data types
    # --------------------------------------------------------

    df = standardize_data_types(df)

    # --------------------------------------------------------
    # 3. Create derived metrics
    # --------------------------------------------------------

    df = create_trip_metrics(df)

    # --------------------------------------------------------
    # 4. Create quality flags
    # --------------------------------------------------------

    df = create_quality_flags(df)

    # --------------------------------------------------------
    # 5. Add source information
    # --------------------------------------------------------

    df["taxi_type"] = taxi_type

    df["source_file"] = source_file

    # --------------------------------------------------------
    # Quality statistics BEFORE removal
    # --------------------------------------------------------

    statistics = {

        "rows_before_cleaning": len(df),

        "negative_duration": int(
            df["is_negative_duration"].sum()
        ),

        "zero_duration": int(
            df["is_zero_duration"].sum()
        ),

        "negative_distance": int(
            df["is_negative_distance"].sum()
        ),

        "zero_distance": int(
            df["is_zero_distance"].sum()
        ),

        "negative_fare": int(
            df["is_negative_fare"].sum()
        ),

        "negative_total": int(
            df["is_negative_total"].sum()
        ),

        "high_speed": int(
            df["is_high_speed"].sum()
        ),

        "invalid_timestamp": int(
            df["is_invalid_timestamp"].sum()
        ),
    }

    # --------------------------------------------------------
    # Remove negative-duration records
    #
    # We remove ONLY these records.
    # --------------------------------------------------------

    df = remove_negative_duration_rows(df)

    statistics["rows_after_cleaning"] = len(df)

    statistics["rows_removed"] = (
        statistics["rows_before_cleaning"]
        - statistics["rows_after_cleaning"]
    )

    return df, statistics


# ============================================================
# CLEAN ONE FILE
# ============================================================

def clean_file(
    input_file,
    output_file,
    taxi_type
):

    print(
        f"\nProcessing: {input_file.name}"
    )

    print(
        f"Taxi type: {taxi_type}"
    )

    parquet_file = pq.ParquetFile(
        input_file
    )

    total_rows = (
        parquet_file.metadata.num_rows
    )

    print(
        f"Original rows: {total_rows:,}"
    )

    print(
        f"Batch size: {BATCH_SIZE:,}"
    )

    # --------------------------------------------------------
    # Remove existing output
    # --------------------------------------------------------

    if output_file.exists():

        output_file.unlink()

    output_file.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    writer = None

    # --------------------------------------------------------
    # File-level statistics
    # --------------------------------------------------------

    file_statistics = {

        "source_file": input_file.name,

        "taxi_type": taxi_type,

        "rows_before_cleaning": 0,

        "rows_after_cleaning": 0,

        "rows_removed": 0,

        "negative_duration": 0,

        "zero_duration": 0,

        "negative_distance": 0,

        "zero_distance": 0,

        "negative_fare": 0,

        "negative_total": 0,

        "high_speed": 0,

        "invalid_timestamp": 0,
    }

    # --------------------------------------------------------
    # Read smaller Arrow batches
    # --------------------------------------------------------

    try:

        for batch_number, arrow_batch in enumerate(
            parquet_file.iter_batches(
                batch_size=BATCH_SIZE
            ),
            start=1
        ):

            print(
                f"Processing batch {batch_number}...",
                end="\r"
            )

            # ------------------------------------------------
            # Convert Arrow batch → Pandas
            # ------------------------------------------------

            df = arrow_batch.to_pandas()

            # Release Arrow batch immediately.
            del arrow_batch

            # ------------------------------------------------
            # Process batch
            # ------------------------------------------------

            df, statistics = process_batch(
                df=df,
                taxi_type=taxi_type,
                source_file=input_file.name
            )

            # ------------------------------------------------
            # Update statistics
            # ------------------------------------------------

            for key in file_statistics:

                if key in statistics:

                    file_statistics[key] += (
                        statistics[key]
                    )

            # ------------------------------------------------
            # Convert Pandas → Arrow
            # ------------------------------------------------

            output_table = pa.Table.from_pandas(
                df,
                preserve_index=False
            )

            # ------------------------------------------------
            # Create writer from first batch
            # ------------------------------------------------

            if writer is None:

                # Build a stable schema from the first batch.
                #
                # Prevent columns containing only nulls from
                # becoming PyArrow's NullType.

                schema_fields = []

                for field in output_table.schema:

                    if pa.types.is_null(field.type):

                        schema_fields.append(
                            pa.field(
                                field.name,
                                pa.string(),
                                nullable=True
                            )
                        )

                    else:

                        schema_fields.append(field)

                writer_schema = pa.schema(
                    schema_fields
                )

                output_table = output_table.cast(
                    writer_schema,
                    safe=False
                )

                writer = pq.ParquetWriter(
                    output_file,
                    writer_schema
                )

            else:

                # Ensure every subsequent batch uses exactly
                # the same schema as the first batch.

                output_table = output_table.cast(
                    writer.schema,
                    safe=False
                )

            # ------------------------------------------------
            # Write batch
            # ------------------------------------------------

            writer.write_table(
                output_table
            )

            # ------------------------------------------------
            # Release memory
            # ------------------------------------------------

            del df
            del output_table

            gc.collect()

    finally:

        # ----------------------------------------------------
        # Close writer even if an exception occurs.
        # ----------------------------------------------------

        if writer is not None:

            writer.close()

    print()

    # --------------------------------------------------------
    # Display file summary
    # --------------------------------------------------------

    print(
        f"Rows after cleaning: "
        f"{file_statistics['rows_after_cleaning']:,}"
    )

    print(
        f"Rows removed: "
        f"{file_statistics['rows_removed']:,}"
    )

    print(
        f"Negative-duration rows removed: "
        f"{file_statistics['negative_duration']:,}"
    )

    print(
        f"Invalid timestamps flagged: "
        f"{file_statistics['invalid_timestamp']:,}"
    )

    print(
        f"Saved: {output_file}"
    )

    return file_statistics


# ============================================================
# FIND RAW FILES
# ============================================================

def find_raw_files():

    files = []

    for taxi_type in [
        "yellow",
        "green"
    ]:

        taxi_directory = (
            RAW_DATA_DIR / taxi_type
        )

        if not taxi_directory.exists():

            continue

        taxi_files = sorted(
            taxi_directory.rglob(
                "*.parquet"
            )
        )

        for file in taxi_files:

            files.append(
                (
                    file,
                    taxi_type
                )
            )

    return files


# ============================================================
# PROCESS ALL FILES
# ============================================================

def process_all_files():

    raw_files = find_raw_files()

    print(
        f"Total raw files found: "
        f"{len(raw_files)}"
    )

    if not raw_files:

        print(
            "No Parquet files found."
        )

        return

    all_statistics = []

    # --------------------------------------------------------
    # Process each raw file
    # --------------------------------------------------------

    for file_number, (
        input_file,
        taxi_type
    ) in enumerate(
        raw_files,
        start=1
    ):

        print(
            "\n"
            + "=" * 70
        )

        print(
            f"FILE {file_number}/{len(raw_files)}"
        )

        print(
            "=" * 70
        )

        # ----------------------------------------------------
        # Extract year
        # ----------------------------------------------------

        year = input_file.parent.name

        # ----------------------------------------------------
        # Output directory
        # ----------------------------------------------------

        output_directory = (
            PROCESSED_DATA_DIR
            / taxi_type
            / year
        )

        output_directory.mkdir(
            parents=True,
            exist_ok=True
        )

        # ----------------------------------------------------
        # Output filename
        # ----------------------------------------------------

        output_file = (
            output_directory
            / f"{input_file.stem}_cleaned.parquet"
        )

        # ----------------------------------------------------
        # Clean file
        # ----------------------------------------------------

        statistics = clean_file(
            input_file=input_file,
            output_file=output_file,
            taxi_type=taxi_type
        )

        statistics["output_file"] = (
            str(output_file)
        )

        all_statistics.append(
            statistics
        )

    # --------------------------------------------------------
    # Create summary DataFrame
    # --------------------------------------------------------

    summary_df = pd.DataFrame(
        all_statistics
    )

    summary_file = (
        SUMMARY_DIR
        / "cleaning_summary.csv"
    )

    summary_df.to_csv(
        summary_file,
        index=False
    )

    # --------------------------------------------------------
    # Overall summary
    # --------------------------------------------------------

    print(
        "\n"
        + "=" * 70
    )

    print(
        "FULL CLEANING COMPLETED"
    )

    print(
        "=" * 70
    )

    print(
        f"Files processed: "
        f"{len(summary_df)}"
    )

    print(
        f"Original rows: "
        f"{summary_df['rows_before_cleaning'].sum():,}"
    )

    print(
        f"Cleaned rows: "
        f"{summary_df['rows_after_cleaning'].sum():,}"
    )

    print(
        f"Rows removed: "
        f"{summary_df['rows_removed'].sum():,}"
    )

    print(
        f"Negative-duration rows removed: "
        f"{summary_df['negative_duration'].sum():,}"
    )

    print(
        f"Invalid timestamps flagged: "
        f"{summary_df['invalid_timestamp'].sum():,}"
    )

    print(
        "\nCleaning summary saved to:"
    )

    print(
        summary_file
    )


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    process_all_files()