from pathlib import Path

import gc
import math

import pandas as pd
import pyarrow.parquet as pq
from tqdm import tqdm


# ============================================================
# CONFIGURATION
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

INPUT_ROOT = PROJECT_ROOT / "data" / "processed"
OUTPUT_ROOT = PROJECT_ROOT / "data" / "powerbi"

BATCH_SIZE = 100_000

TAXI_TYPES = ["yellow", "green"]

# Analytical period for Power BI
ANALYTICAL_START = pd.Timestamp("2024-01-01")
ANALYTICAL_END = pd.Timestamp("2026-07-31")


# ============================================================
# COLUMNS REQUIRED FROM CLEANED DATA
# ============================================================

REQUIRED_COLUMNS = [
    "pickup_datetime",
    "pickup_date",
    "pickup_hour",
    "pickup_year",
    "pickup_month",
    "pickup_day_of_week",
    "is_weekend",
    "taxi_type",
    "pickup_location_id",
    "dropoff_location_id",
    "payment_type",
    "passenger_count",
    "trip_distance",
    "trip_duration_minutes",
    "fare_amount",
    "tip_amount",
    "total_amount",
]


# ============================================================
# FIND CLEANED FILES
# ============================================================

def get_cleaned_files():
    """
    Find all cleaned Yellow and Green Taxi Parquet files.
    """

    files = []

    for taxi_type in TAXI_TYPES:

        taxi_path = INPUT_ROOT / taxi_type

        if not taxi_path.exists():
            print(
                f"WARNING: Folder not found: {taxi_path}"
            )
            continue

        files.extend(
            sorted(
                taxi_path.rglob("*_cleaned.parquet")
            )
        )

    return files


# ============================================================
# PREPARE BATCH
# ============================================================

def prepare_batch(df):
    """
    Prepare one batch before aggregation.

    The analytical-period filter is applied here so that
    Power BI aggregate tables contain only records from the
    project's defined reporting period.

    Records outside the analytical period remain untouched
    in the cleaned Parquet dataset.
    """

    # --------------------------------------------------------
    # Check required columns
    # --------------------------------------------------------

    missing_columns = [
        column
        for column in REQUIRED_COLUMNS
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Missing required columns: {missing_columns}"
        )

    # --------------------------------------------------------
    # Standardize date
    # --------------------------------------------------------

    df["pickup_date"] = pd.to_datetime(
        df["pickup_date"],
        errors="coerce"
    ).dt.normalize()

    # --------------------------------------------------------
    # Analytical period filter
    # --------------------------------------------------------

    period_mask = (
        df["pickup_date"].notna()
        & (df["pickup_date"] >= ANALYTICAL_START)
        & (df["pickup_date"] <= ANALYTICAL_END)
    )

    df = df.loc[period_mask].copy()

    # If no records from this batch belong to the
    # analytical period, return the empty batch.
    if df.empty:
        return df

    # --------------------------------------------------------
    # Numeric columns
    # --------------------------------------------------------

    numeric_columns = [
        "pickup_year",
        "pickup_month",
        "pickup_hour",
        "pickup_day_of_week",
        "pickup_location_id",
        "dropoff_location_id",
        "payment_type",
        "passenger_count",
        "trip_distance",
        "trip_duration_minutes",
        "fare_amount",
        "tip_amount",
        "total_amount",
    ]

    for column in numeric_columns:

        df[column] = pd.to_numeric(
            df[column],
            errors="coerce"
        )

    # --------------------------------------------------------
    # Taxi type
    # --------------------------------------------------------

    df["taxi_type"] = (
        df["taxi_type"]
        .astype("string")
    )

    # --------------------------------------------------------
    # Revenue quality flag
    #
    # Negative financial records remain in the cleaned
    # dataset, but are excluded from normal revenue/fare KPIs.
    # --------------------------------------------------------

    df["is_revenue_record"] = (
        df["fare_amount"].notna()
        & df["total_amount"].notna()
        & (df["fare_amount"] >= 0)
        & (df["total_amount"] >= 0)
    )

    # --------------------------------------------------------
    # Valid distance
    #
    # Negative distances are excluded from distance metrics.
    # Zero-distance trips remain valid records.
    # --------------------------------------------------------

    df["is_valid_distance"] = (
        df["trip_distance"].notna()
        & (df["trip_distance"] >= 0)
    )

    # --------------------------------------------------------
    # Valid duration
    #
    # Negative-duration records were already removed during
    # the cleaning stage.
    # --------------------------------------------------------

    df["is_valid_duration"] = (
        df["trip_duration_minutes"].notna()
        & (df["trip_duration_minutes"] >= 0)
    )

    # --------------------------------------------------------
    # Valid passenger count
    # --------------------------------------------------------

    df["is_valid_passenger_count"] = (
        df["passenger_count"].notna()
        & (df["passenger_count"] >= 0)
    )

    # --------------------------------------------------------
    # Valid tip
    # --------------------------------------------------------

    df["is_valid_tip"] = (
        df["tip_amount"].notna()
    )

    return df


# ============================================================
# AGGREGATE ONE BATCH
# ============================================================

def aggregate_batch(df, group_columns):
    """
    Aggregate a single batch.

    IMPORTANT:
    We calculate SUMS and COUNTS instead of averaging values.

    Final averages are calculated only after all batches
    have been combined.
    """

    if df.empty:
        return pd.DataFrame()

    # --------------------------------------------------------
    # Revenue
    # --------------------------------------------------------

    revenue_mask = df["is_revenue_record"]
    revenue_df = df.loc[revenue_mask]

    # --------------------------------------------------------
    # Distance
    # --------------------------------------------------------

    distance_df = df.loc[
        df["is_valid_distance"]
    ]

    # --------------------------------------------------------
    # Duration
    # --------------------------------------------------------

    duration_df = df.loc[
        df["is_valid_duration"]
    ]

    # --------------------------------------------------------
    # Passenger count
    # --------------------------------------------------------

    passenger_df = df.loc[
        df["is_valid_passenger_count"]
    ]

    # --------------------------------------------------------
    # Tips
    # --------------------------------------------------------

    tip_df = df.loc[
        df["is_valid_tip"]
    ]

    # --------------------------------------------------------
    # Base aggregation
    # --------------------------------------------------------

    result = (
        df.groupby(
            group_columns,
            dropna=False,
            observed=True
        )
        .agg(
            total_trips=(
                "taxi_type",
                "size"
            ),

            total_tips=(
                "tip_amount",
                "sum"
            ),

            total_distance=(
                "trip_distance",
                "sum"
            ),

            total_duration_minutes=(
                "trip_duration_minutes",
                "sum"
            ),

            total_passenger_count=(
                "passenger_count",
                "sum"
            ),

            negative_fare_trips=(
                "fare_amount",
                lambda x: (x < 0).sum()
            ),

            negative_total_trips=(
                "total_amount",
                lambda x: (x < 0).sum()
            ),

            zero_distance_trips=(
                "trip_distance",
                lambda x: (x == 0).sum()
            ),
        )
        .reset_index()
    )

    # --------------------------------------------------------
    # Revenue aggregation
    # --------------------------------------------------------

    if not revenue_df.empty:

        revenue_grouped = (
            revenue_df
            .groupby(
                group_columns,
                dropna=False,
                observed=True
            )
            .agg(
                revenue_trips=(
                    "total_amount",
                    "size"
                ),

                total_revenue=(
                    "total_amount",
                    "sum"
                ),

                total_fare=(
                    "fare_amount",
                    "sum"
                ),

                fare_count=(
                    "fare_amount",
                    "count"
                ),
            )
            .reset_index()
        )

        result = result.merge(
            revenue_grouped,
            on=group_columns,
            how="left"
        )

    # --------------------------------------------------------
    # Distance count
    # --------------------------------------------------------

    if not distance_df.empty:

        distance_grouped = (
            distance_df
            .groupby(
                group_columns,
                dropna=False,
                observed=True
            )
            .agg(
                distance_count=(
                    "trip_distance",
                    "count"
                )
            )
            .reset_index()
        )

        result = result.merge(
            distance_grouped,
            on=group_columns,
            how="left"
        )

    # --------------------------------------------------------
    # Duration count
    # --------------------------------------------------------

    if not duration_df.empty:

        duration_grouped = (
            duration_df
            .groupby(
                group_columns,
                dropna=False,
                observed=True
            )
            .agg(
                duration_count=(
                    "trip_duration_minutes",
                    "count"
                )
            )
            .reset_index()
        )

        result = result.merge(
            duration_grouped,
            on=group_columns,
            how="left"
        )

    # --------------------------------------------------------
    # Passenger count
    # --------------------------------------------------------

    if not passenger_df.empty:

        passenger_grouped = (
            passenger_df
            .groupby(
                group_columns,
                dropna=False,
                observed=True
            )
            .agg(
                passenger_count_records=(
                    "passenger_count",
                    "count"
                )
            )
            .reset_index()
        )

        result = result.merge(
            passenger_grouped,
            on=group_columns,
            how="left"
        )

    # --------------------------------------------------------
    # Tip count
    # --------------------------------------------------------

    if not tip_df.empty:

        tip_grouped = (
            tip_df
            .groupby(
                group_columns,
                dropna=False,
                observed=True
            )
            .agg(
                tip_count=(
                    "tip_amount",
                    "count"
                )
            )
            .reset_index()
        )

        result = result.merge(
            tip_grouped,
            on=group_columns,
            how="left"
        )

    # --------------------------------------------------------
    # Fill missing aggregation values
    # --------------------------------------------------------

    fill_zero_columns = [
        "revenue_trips",
        "total_revenue",
        "total_fare",
        "fare_count",
        "distance_count",
        "duration_count",
        "passenger_count_records",
        "tip_count",
    ]

    for column in fill_zero_columns:

        if column in result.columns:
            result[column] = result[column].fillna(0)

    return result


# ============================================================
# COMBINE AGGREGATION RESULTS
# ============================================================

def combine_aggregations(aggregation_list, group_columns):
    """
    Combine batch-level aggregation results.

    Sums are added together and counts are added together.
    """

    if not aggregation_list:
        return pd.DataFrame()

    combined = pd.concat(
        aggregation_list,
        ignore_index=True
    )

    sum_columns = [
        "total_trips",
        "revenue_trips",
        "total_revenue",
        "total_fare",
        "fare_count",
        "total_tips",
        "total_distance",
        "distance_count",
        "total_duration_minutes",
        "duration_count",
        "total_passenger_count",
        "passenger_count_records",
        "tip_count",
        "negative_fare_trips",
        "negative_total_trips",
        "zero_distance_trips",
    ]

    existing_sum_columns = [
        column
        for column in sum_columns
        if column in combined.columns
    ]

    combined = (
        combined
        .groupby(
            group_columns,
            dropna=False,
            observed=True
        )[existing_sum_columns]
        .sum()
        .reset_index()
    )

    # --------------------------------------------------------
    # Final average metrics
    # --------------------------------------------------------

    combined["average_fare"] = (
        combined["total_fare"]
        / combined["fare_count"].replace(0, pd.NA)
    )

    combined["average_distance"] = (
        combined["total_distance"]
        / combined["distance_count"].replace(0, pd.NA)
    )

    combined["average_duration_minutes"] = (
        combined["total_duration_minutes"]
        / combined["duration_count"].replace(0, pd.NA)
    )

    combined["average_passenger_count"] = (
        combined["total_passenger_count"]
        / combined["passenger_count_records"].replace(0, pd.NA)
    )

    combined["average_tip"] = (
        combined["total_tips"]
        / combined["tip_count"].replace(0, pd.NA)
    )

    combined["revenue_per_trip"] = (
        combined["total_revenue"]
        / combined["revenue_trips"].replace(0, pd.NA)
    )

    # Revenue per mile should only use groups with
    # positive distance.
    combined["revenue_per_mile"] = (
        combined["total_revenue"]
        / combined["total_distance"].where(
            combined["total_distance"] > 0
        )
    )

    return combined


# ============================================================
# OPTIMIZE DATA TYPES
# ============================================================

def optimize_dtypes(df):
    """
    Reduce Power BI aggregate table size while preserving
    analytical usability.
    """

    integer_columns = [
        "pickup_year",
        "pickup_month",
        "pickup_hour",
        "pickup_day_of_week",
        "pickup_location_id",
        "dropoff_location_id",
        "payment_type",
        "total_trips",
        "revenue_trips",
        "fare_count",
        "distance_count",
        "duration_count",
        "passenger_count_records",
        "tip_count",
        "negative_fare_trips",
        "negative_total_trips",
        "zero_distance_trips",
    ]

    for column in integer_columns:

        if column in df.columns:

            # Nullable integer is useful where NaN may exist.
            try:
                df[column] = (
                    pd.to_numeric(
                        df[column],
                        errors="coerce"
                    )
                    .round()
                    .astype("Int64")
                )
            except Exception:
                pass

    float_columns = [
        "total_revenue",
        "total_fare",
        "total_tips",
        "total_distance",
        "total_duration_minutes",
        "total_passenger_count",
        "average_fare",
        "average_distance",
        "average_duration_minutes",
        "average_passenger_count",
        "average_tip",
        "revenue_per_trip",
        "revenue_per_mile",
    ]

    for column in float_columns:

        if column in df.columns:

            df[column] = pd.to_numeric(
                df[column],
                errors="coerce"
            ).astype("float32")

    return df


# ============================================================
# AGGREGATION DEFINITIONS
# ============================================================

AGGREGATIONS = {

    "fact_daily": {
        "group_columns": [
            "pickup_date",
            "taxi_type",
        ]
    },

    "fact_hourly": {
        "group_columns": [
            "pickup_date",
            "pickup_hour",
            "taxi_type",
        ]
    },

    "fact_location_daily": {
        "group_columns": [
            "pickup_date",
            "pickup_location_id",
            "taxi_type",
        ]
    },

    "fact_payment_daily": {
        "group_columns": [
            "pickup_date",
            "payment_type",
            "taxi_type",
        ]
    },

    "fact_route": {
        "group_columns": [
            "pickup_location_id",
            "dropoff_location_id",
            "taxi_type",
        ]
    },
}


# ============================================================
# PROCESS ALL FILES
# ============================================================

def process_all_files():

    files = get_cleaned_files()

    if not files:
        raise FileNotFoundError(
            "No cleaned Parquet files were found."
        )

    print()
    print("=" * 70)
    print("POWER BI AGGREGATION")
    print("=" * 70)

    print(f"Cleaned files found: {len(files)}")
    print(
        f"Analytical period: "
        f"{ANALYTICAL_START.date()} "
        f"to "
        f"{ANALYTICAL_END.date()}"
    )
    print()

    # --------------------------------------------------------
    # Storage for batch aggregations
    # --------------------------------------------------------

    aggregation_results = {
        table_name: []
        for table_name in AGGREGATIONS
    }

    total_rows_processed = 0

    # --------------------------------------------------------
    # Process files
    # --------------------------------------------------------

    file_progress = tqdm(
        files,
        desc="Processing files",
        unit="file"
    )

    for file_path in file_progress:

        try:

            parquet_file = pq.ParquetFile(
                file_path
            )

            file_rows_processed = 0
            file_rows_in_period = 0

            batch_iterator = parquet_file.iter_batches(
                batch_size=BATCH_SIZE,
                columns=REQUIRED_COLUMNS
            )

            for batch in batch_iterator:

                df = batch.to_pandas()

                rows_in_batch = len(df)

                file_rows_processed += rows_in_batch

                # --------------------------------------------
                # Prepare and filter analytical period
                # --------------------------------------------

                df = prepare_batch(df)

                rows_in_period = len(df)

                file_rows_in_period += rows_in_period
                total_rows_processed += rows_in_period

                if df.empty:
                    del df
                    gc.collect()
                    continue

                # --------------------------------------------
                # Aggregate for each Power BI table
                # --------------------------------------------

                for table_name, config in AGGREGATIONS.items():

                    group_columns = config[
                        "group_columns"
                    ]

                    aggregated = aggregate_batch(
                        df,
                        group_columns
                    )

                    if not aggregated.empty:
                        aggregation_results[
                            table_name
                        ].append(aggregated)

                    del aggregated

                del df
                gc.collect()

            file_progress.set_postfix(
                file=file_path.name,
                period_rows=file_rows_in_period
            )

        except Exception as exc:

            print()
            print(
                f"ERROR processing file: "
                f"{file_path}"
            )

            raise exc

    print()
    print("=" * 70)
    print("COMBINING AGGREGATIONS")
    print("=" * 70)

    # --------------------------------------------------------
    # Combine all batch-level results
    # --------------------------------------------------------

    final_tables = {}

    for table_name, config in AGGREGATIONS.items():

        print(
            f"Combining {table_name}..."
        )

        combined = combine_aggregations(
            aggregation_results[table_name],
            config["group_columns"]
        )

        combined = optimize_dtypes(
            combined
        )

        final_tables[
            table_name
        ] = combined

        # Free batch aggregation list
        aggregation_results[
            table_name
        ].clear()

    # --------------------------------------------------------
    # Save Power BI tables
    # --------------------------------------------------------

    OUTPUT_ROOT.mkdir(
        parents=True,
        exist_ok=True
    )

    print()
    print("=" * 70)
    print("SAVING POWER BI AGGREGATE TABLES")
    print("=" * 70)

    for table_name, df in final_tables.items():

        output_path = (
            OUTPUT_ROOT
            / f"{table_name}.parquet"
        )

        df.to_parquet(
            output_path,
            index=False,
            engine="pyarrow",
            compression="snappy"
        )

        size_mb = (
            output_path.stat().st_size
            / (1024 ** 2)
        )

        print(
            f"  ✓ {table_name:<30}"
            f"{len(df):>10,} rows | "
            f"{size_mb:>9.2f} MB"
        )

    # --------------------------------------------------------
    # Final summary
    # --------------------------------------------------------

    print()
    print("=" * 70)
    print("AGGREGATION COMPLETED SUCCESSFULLY")
    print("=" * 70)

    print(
        f"Power BI records included: "
        f"{total_rows_processed:,}"
    )

    print()
    print("Power BI tables:")

    for table_name, df in final_tables.items():

        print(
            f"  {table_name:<30}"
            f"{len(df):>10,} rows"
        )

    print()
    print(
        f"Output folder:\n"
        f"{OUTPUT_ROOT}"
    )

    print()

    # --------------------------------------------------------
    # Cleanup
    # --------------------------------------------------------

    del final_tables
    gc.collect()


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    process_all_files()