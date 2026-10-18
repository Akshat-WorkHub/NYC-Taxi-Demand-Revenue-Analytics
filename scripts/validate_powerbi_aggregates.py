from pathlib import Path

import pandas as pd


# ============================================================
# CONFIGURATION
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

POWERBI_ROOT = PROJECT_ROOT / "data" / "powerbi"

EXPECTED_START_DATE = pd.Timestamp("2024-01-01")
EXPECTED_END_DATE = pd.Timestamp("2026-07-31")

# IMPORTANT:
# The cleaned dataset contains 117,801,813 records.
# 128 records are intentionally outside the Power BI analytical
# period and therefore excluded from the aggregate tables.
EXPECTED_POWERBI_ROWS = 117_801_685

# Floating-point tolerance used for derived metrics.
# This avoids false failures caused by float32/float64 precision.
DERIVED_METRIC_TOLERANCE = 0.10


# ============================================================
# TABLE FILES
# ============================================================

TABLE_FILES = {
    "fact_daily": POWERBI_ROOT / "fact_daily.parquet",
    "fact_hourly": POWERBI_ROOT / "fact_hourly.parquet",
    "fact_location_daily": POWERBI_ROOT / "fact_location_daily.parquet",
    "fact_payment_daily": POWERBI_ROOT / "fact_payment_daily.parquet",
    "fact_route": POWERBI_ROOT / "fact_route.parquet",
}


# ============================================================
# EXPECTED SCHEMAS
# ============================================================

EXPECTED_COLUMNS = {

    "fact_daily": [
        "pickup_date",
        "taxi_type",
        "total_trips",
        "revenue_trips",
        "total_revenue",
        "total_fare",
        "total_tips",
        "total_distance",
        "total_duration_minutes",
        "total_passenger_count",
        "negative_fare_trips",
        "negative_total_trips",
        "zero_distance_trips",
        "fare_count",
        "distance_count",
        "duration_count",
        "passenger_count_records",
        "tip_count",
        "average_fare",
        "average_distance",
        "average_duration_minutes",
        "average_passenger_count",
        "average_tip",
        "revenue_per_trip",
        "revenue_per_mile",
    ],

    "fact_hourly": [
        "pickup_date",
        "pickup_hour",
        "taxi_type",
        "total_trips",
        "revenue_trips",
        "total_revenue",
        "total_fare",
        "total_tips",
        "total_distance",
        "total_duration_minutes",
        "total_passenger_count",
        "negative_fare_trips",
        "negative_total_trips",
        "zero_distance_trips",
        "fare_count",
        "distance_count",
        "duration_count",
        "passenger_count_records",
        "tip_count",
        "average_fare",
        "average_distance",
        "average_duration_minutes",
        "average_passenger_count",
        "average_tip",
        "revenue_per_trip",
        "revenue_per_mile",
    ],

    "fact_location_daily": [
        "pickup_date",
        "pickup_location_id",
        "taxi_type",
        "total_trips",
        "revenue_trips",
        "total_revenue",
        "total_fare",
        "total_tips",
        "total_distance",
        "total_duration_minutes",
        "total_passenger_count",
        "negative_fare_trips",
        "negative_total_trips",
        "zero_distance_trips",
        "fare_count",
        "distance_count",
        "duration_count",
        "passenger_count_records",
        "tip_count",
        "average_fare",
        "average_distance",
        "average_duration_minutes",
        "average_passenger_count",
        "average_tip",
        "revenue_per_trip",
        "revenue_per_mile",
    ],

    "fact_payment_daily": [
        "pickup_date",
        "payment_type",
        "taxi_type",
        "total_trips",
        "revenue_trips",
        "total_revenue",
        "total_fare",
        "total_tips",
        "total_distance",
        "total_duration_minutes",
        "total_passenger_count",
        "negative_fare_trips",
        "negative_total_trips",
        "zero_distance_trips",
        "fare_count",
        "distance_count",
        "duration_count",
        "passenger_count_records",
        "tip_count",
        "average_fare",
        "average_distance",
        "average_duration_minutes",
        "average_passenger_count",
        "average_tip",
        "revenue_per_trip",
        "revenue_per_mile",
    ],

    "fact_route": [
        "pickup_location_id",
        "dropoff_location_id",
        "taxi_type",
        "total_trips",
        "revenue_trips",
        "total_revenue",
        "total_fare",
        "total_tips",
        "total_distance",
        "total_duration_minutes",
        "total_passenger_count",
        "negative_fare_trips",
        "negative_total_trips",
        "zero_distance_trips",
        "fare_count",
        "distance_count",
        "duration_count",
        "passenger_count_records",
        "tip_count",
        "average_fare",
        "average_distance",
        "average_duration_minutes",
        "average_passenger_count",
        "average_tip",
        "revenue_per_trip",
        "revenue_per_mile",
    ],
}


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def print_section(title):

    print()
    print("=" * 75)
    print(title)
    print("=" * 75)


# ============================================================
# FILE EXISTENCE
# ============================================================

def check_file_exists(table_name, path):

    if not path.exists():

        print(
            f"❌ {table_name}: FILE NOT FOUND"
        )

        return False

    print(
        f"✓ {table_name}: file exists"
    )

    return True


# ============================================================
# LOAD TABLE
# ============================================================

def load_table(table_name, path):

    print(
        f"\nLoading {table_name}..."
    )

    df = pd.read_parquet(path)

    print(
        f"  Rows    : {len(df):,}"
    )

    print(
        f"  Columns : {len(df.columns)}"
    )

    return df


# ============================================================
# SCHEMA VALIDATION
# ============================================================

def check_columns(table_name, df):

    expected = set(
        EXPECTED_COLUMNS[table_name]
    )

    actual = set(
        df.columns
    )

    missing = expected - actual

    extra = actual - expected

    if missing:

        print(
            f"❌ {table_name}: missing columns:"
        )

        for column in sorted(missing):

            print(
                f"   - {column}"
            )

    else:

        print(
            f"✓ {table_name}: all expected columns present"
        )

    if extra:

        print(
            f"⚠ {table_name}: unexpected extra columns:"
        )

        for column in sorted(extra):

            print(
                f"   + {column}"
            )

    return len(missing) == 0


# ============================================================
# NULL VALIDATION
# ============================================================

def check_nulls(table_name, df):

    null_counts = (
        df.isna()
        .sum()
        .sort_values(ascending=False)
    )

    null_columns = null_counts[
        null_counts > 0
    ]

    if len(null_columns) == 0:

        print(
            f"✓ {table_name}: no NULL values"
        )

        return

    print(
        f"⚠ {table_name}: NULL values found:"
    )

    for column, count in null_columns.items():

        percentage = (
            count / len(df) * 100
        )

        print(
            f"   {column:<30} "
            f"{count:>10,} "
            f"({percentage:.4f}%)"
        )


# ============================================================
# DATE RANGE VALIDATION
# ============================================================

def check_date_range(table_name, df):

    if "pickup_date" not in df.columns:

        return

    dates = pd.to_datetime(
        df["pickup_date"],
        errors="coerce"
    )

    null_dates = dates.isna().sum()

    if null_dates > 0:

        print(
            f"❌ {table_name}: "
            f"{null_dates:,} invalid/null pickup dates"
        )

    min_date = dates.min()
    max_date = dates.max()

    print(
        f"  Date range: "
        f"{min_date.date()} → {max_date.date()}"
    )

    if min_date < EXPECTED_START_DATE:

        print(
            f"❌ {table_name}: "
            f"date before expected start"
        )

    else:

        print(
            f"✓ {table_name}: start date valid"
        )

    if max_date > EXPECTED_END_DATE:

        print(
            f"❌ {table_name}: "
            f"date after expected end"
        )

    else:

        print(
            f"✓ {table_name}: end date valid"
        )


# ============================================================
# TAXI TYPE VALIDATION
# ============================================================

def check_taxi_types(table_name, df):

    if "taxi_type" not in df.columns:

        return

    values = (
        df["taxi_type"]
        .dropna()
        .astype(str)
        .str.lower()
        .unique()
    )

    print(
        f"  Taxi types: "
        f"{sorted(values.tolist())}"
    )

    expected = {
        "yellow",
        "green",
    }

    actual = set(values)

    if actual == expected:

        print(
            f"✓ {table_name}: "
            f"Yellow and Green present"
        )

    else:

        print(
            f"⚠ {table_name}: "
            f"unexpected taxi types"
        )


# ============================================================
# AGGREGATE METRIC VALIDATION
# ============================================================

def check_negative_metrics(table_name, df):

    metric_columns = [
        "total_trips",
        "revenue_trips",
        "total_revenue",
        "total_fare",
        "total_distance",
        "total_duration_minutes",
        "total_passenger_count",
        "fare_count",
        "distance_count",
        "duration_count",
        "passenger_count_records",
        "tip_count",
        "negative_fare_trips",
        "negative_total_trips",
        "zero_distance_trips",
    ]

    negative_found = False

    for column in metric_columns:

        if column not in df.columns:

            continue

        negative_count = (
            df[column] < 0
        ).sum()

        if negative_count > 0:

            negative_found = True

            print(
                f"❌ {table_name}: "
                f"{column} contains "
                f"{negative_count:,} negative values"
            )

    # --------------------------------------------------------
    # total_tips is intentionally NOT checked as an error.
    #
    # Negative tip values exist in the source data and were
    # intentionally preserved during cleaning.
    # --------------------------------------------------------

    if "total_tips" in df.columns:

        negative_tips = (
            df["total_tips"] < 0
        ).sum()

        if negative_tips > 0:

            print(
                f"ℹ {table_name}: "
                f"total_tips contains "
                f"{negative_tips:,} negative value(s); "
                f"source financial records preserved"
            )

    if not negative_found:

        print(
            f"✓ {table_name}: "
            f"no invalid negative aggregate metrics"
        )

    return not negative_found


# ============================================================
# DUPLICATE KEY VALIDATION
# ============================================================

def check_duplicate_keys(
    table_name,
    df,
    key_columns
):

    duplicates = (
        df.duplicated(
            subset=key_columns,
            keep=False
        )
        .sum()
    )

    if duplicates == 0:

        print(
            f"✓ {table_name}: "
            f"no duplicate aggregation keys"
        )

        return True

    print(
        f"❌ {table_name}: "
        f"{duplicates:,} rows participate "
        f"in duplicate keys"
    )

    return False


# ============================================================
# DERIVED METRIC VALIDATION
# ============================================================

def check_derived_metrics(
    table_name,
    df
):

    problems = 0

    # --------------------------------------------------------
    # Revenue per trip
    # --------------------------------------------------------

    if {
        "revenue_per_trip",
        "total_revenue",
        "revenue_trips",
    }.issubset(df.columns):

        valid = (
            df["revenue_trips"] > 0
        )

        expected = (
            df.loc[valid, "total_revenue"]
            / df.loc[valid, "revenue_trips"]
        )

        actual = (
            df.loc[valid, "revenue_per_trip"]
        )

        difference = (
            expected - actual
        ).abs()

        bad = (
            difference > DERIVED_METRIC_TOLERANCE
        ).sum()

        if bad > 0:

            print(
                f"❌ {table_name}: "
                f"{bad:,} revenue_per_trip "
                f"values inconsistent"
            )

            problems += bad

        else:

            print(
                f"✓ {table_name}: "
                f"revenue_per_trip validated"
            )

    # --------------------------------------------------------
    # Revenue per mile
    # --------------------------------------------------------

    if {
        "revenue_per_mile",
        "total_revenue",
        "total_distance",
    }.issubset(df.columns):

        valid = (
            df["total_distance"] > 0
        )

        expected = (
            df.loc[valid, "total_revenue"]
            / df.loc[valid, "total_distance"]
        )

        actual = (
            df.loc[valid, "revenue_per_mile"]
        )

        # Ignore rows where the stored value itself is NaN.
        valid_comparison = (
            expected.notna()
            & actual.notna()
        )

        difference = (
            expected[valid_comparison]
            - actual[valid_comparison]
        ).abs()

        bad = (
            difference > DERIVED_METRIC_TOLERANCE
        ).sum()

        if bad > 0:

            print(
                f"❌ {table_name}: "
                f"{bad:,} revenue_per_mile "
                f"values inconsistent"
            )

            problems += bad

        else:

            print(
                f"✓ {table_name}: "
                f"revenue_per_mile validated"
            )

    return problems


# ============================================================
# MAIN VALIDATION
# ============================================================

def main():

    print_section(
        "NYC TAXI — POWER BI AGGREGATION VALIDATION"
    )

    print(
        f"Power BI data folder:\n"
        f"{POWERBI_ROOT}"
    )

    # ========================================================
    # 1. FILE EXISTENCE
    # ========================================================

    print_section(
        "1. FILE EXISTENCE"
    )

    all_files_exist = True

    for table_name, path in TABLE_FILES.items():

        exists = check_file_exists(
            table_name,
            path
        )

        if not exists:

            all_files_exist = False

    if not all_files_exist:

        print()

        print(
            "❌ Validation stopped because "
            "one or more files are missing."
        )

        return

    # ========================================================
    # 2. LOAD TABLES
    # ========================================================

    print_section(
        "2. LOADING AGGREGATE TABLES"
    )

    tables = {}

    for table_name, path in TABLE_FILES.items():

        tables[table_name] = load_table(
            table_name,
            path
        )

    # ========================================================
    # 3. SCHEMA VALIDATION
    # ========================================================

    print_section(
        "3. SCHEMA VALIDATION"
    )

    schema_problems = 0

    for table_name, df in tables.items():

        passed = check_columns(
            table_name,
            df
        )

        if not passed:

            schema_problems += 1

    # ========================================================
    # 4. NULL VALIDATION
    # ========================================================

    print_section(
        "4. NULL VALIDATION"
    )

    for table_name, df in tables.items():

        check_nulls(
            table_name,
            df
        )

    # ========================================================
    # 5. DATE RANGE
    # ========================================================

    print_section(
        "5. DATE RANGE VALIDATION"
    )

    date_range_problems = 0

    for table_name, df in tables.items():

        if "pickup_date" in df.columns:

            dates = pd.to_datetime(
                df["pickup_date"],
                errors="coerce"
            )

            if dates.isna().any():

                date_range_problems += 1

            if (
                dates.min() < EXPECTED_START_DATE
                or dates.max() > EXPECTED_END_DATE
            ):

                date_range_problems += 1

            check_date_range(
                table_name,
                df
            )

    # ========================================================
    # 6. TAXI TYPE
    # ========================================================

    print_section(
        "6. TAXI TYPE VALIDATION"
    )

    for table_name, df in tables.items():

        check_taxi_types(
            table_name,
            df
        )

    # ========================================================
    # 7. AGGREGATE METRIC VALIDATION
    # ========================================================

    print_section(
        "7. AGGREGATE METRIC VALIDATION"
    )

    aggregate_metric_problems = 0

    for table_name, df in tables.items():

        passed = check_negative_metrics(
            table_name,
            df
        )

        if not passed:

            aggregate_metric_problems += 1

    # ========================================================
    # 8. DUPLICATE KEY VALIDATION
    # ========================================================

    print_section(
        "8. DUPLICATE KEY VALIDATION"
    )

    duplicate_keys = {

        "fact_daily": [
            "pickup_date",
            "taxi_type",
        ],

        "fact_hourly": [
            "pickup_date",
            "pickup_hour",
            "taxi_type",
        ],

        "fact_location_daily": [
            "pickup_date",
            "pickup_location_id",
            "taxi_type",
        ],

        "fact_payment_daily": [
            "pickup_date",
            "payment_type",
            "taxi_type",
        ],

        "fact_route": [
            "pickup_location_id",
            "dropoff_location_id",
            "taxi_type",
        ],
    }

    duplicate_problems = 0

    for table_name, key_columns in duplicate_keys.items():

        passed = check_duplicate_keys(
            table_name,
            tables[table_name],
            key_columns
        )

        if not passed:

            duplicate_problems += 1

    # ========================================================
    # 9. DERIVED METRIC VALIDATION
    # ========================================================

    print_section(
        "9. DERIVED METRIC VALIDATION"
    )

    total_metric_problems = 0

    for table_name, df in tables.items():

        total_metric_problems += (
            check_derived_metrics(
                table_name,
                df
            )
        )

    # ========================================================
    # 10. DAILY TOTALS
    # ========================================================

    print_section(
        "10. DAILY AGGREGATION SUMMARY"
    )

    daily = tables["fact_daily"]

    total_trips = (
        daily["total_trips"]
        .sum()
    )

    total_revenue = (
        daily["total_revenue"]
        .sum()
    )

    total_fare = (
        daily["total_fare"]
        .sum()
    )

    total_tips = (
        daily["total_tips"]
        .sum()
    )

    revenue_trips = (
        daily["revenue_trips"]
        .sum()
    )

    print(
        f"Total aggregated trips : "
        f"{total_trips:,.0f}"
    )

    print(
        f"Revenue eligible trips : "
        f"{revenue_trips:,.0f}"
    )

    print(
        f"Total revenue          : "
        f"{total_revenue:,.2f}"
    )

    print(
        f"Total fare             : "
        f"{total_fare:,.2f}"
    )

    print(
        f"Total tips             : "
        f"{total_tips:,.2f}"
    )

    # ========================================================
    # 11. TAXI TYPE SUMMARY
    # ========================================================

    print_section(
        "11. TAXI TYPE SUMMARY"
    )

    taxi_summary = (
        daily
        .groupby("taxi_type")
        .agg(
            trips=("total_trips", "sum"),
            revenue_trips=("revenue_trips", "sum"),
            revenue=("total_revenue", "sum"),
            fare=("total_fare", "sum"),
            tips=("total_tips", "sum"),
        )
        .reset_index()
    )

    print(
        taxi_summary.to_string(
            index=False
        )
    )

    # ========================================================
    # 12. CROSS-TABLE CONSISTENCY
    # ========================================================

    print_section(
        "12. CROSS-TABLE CONSISTENCY"
    )

    cross_table_problems = 0

    # --------------------------------------------------------
    # Daily vs Hourly
    # --------------------------------------------------------

    hourly = tables["fact_hourly"]

    hourly_total = (
        hourly["total_trips"]
        .sum()
    )

    if hourly_total == total_trips:

        print(
            "✓ Daily trips = Hourly trips"
        )

    else:

        cross_table_problems += 1

        print(
            "❌ Daily trips != Hourly trips"
        )

        print(
            f"  Daily : {total_trips:,}"
        )

        print(
            f"  Hourly: {hourly_total:,}"
        )

    # --------------------------------------------------------
    # Daily vs Location
    # --------------------------------------------------------

    location = tables[
        "fact_location_daily"
    ]

    location_total = (
        location["total_trips"]
        .sum()
    )

    if location_total == total_trips:

        print(
            "✓ Daily trips = Location trips"
        )

    else:

        cross_table_problems += 1

        print(
            "❌ Daily trips != Location trips"
        )

        print(
            f"  Daily   : {total_trips:,}"
        )

        print(
            f"  Location: {location_total:,}"
        )

    # --------------------------------------------------------
    # Daily vs Payment
    # --------------------------------------------------------

    payment = tables[
        "fact_payment_daily"
    ]

    payment_total = (
        payment["total_trips"]
        .sum()
    )

    if payment_total == total_trips:

        print(
            "✓ Daily trips = Payment trips"
        )

    else:

        cross_table_problems += 1

        print(
            "⚠ Daily trips != Payment trips"
        )

        print(
            "  This can occur because "
            "payment_type can be missing."
        )

        print(
            f"  Daily   : {total_trips:,}"
        )

        print(
            f"  Payment : {payment_total:,}"
        )

    # ========================================================
    # 13. FINAL VALIDATION
    # ========================================================

    print_section(
        "13. FINAL VALIDATION RESULT"
    )

    print(
        f"Expected Power BI records: "
        f"{EXPECTED_POWERBI_ROWS:,}"
    )

    print(
        f"Aggregated daily trips: "
        f"{total_trips:,.0f}"
    )

    record_count_match = (
        total_trips == EXPECTED_POWERBI_ROWS
    )

    if record_count_match:

        print(
            "✓ Aggregated trip count matches "
            "the Power BI analytical dataset."
        )

    else:

        difference = (
            EXPECTED_POWERBI_ROWS
            - total_trips
        )

        print(
            f"❌ Difference: "
            f"{difference:,} records"
        )

    # --------------------------------------------------------
    # Overall result
    # --------------------------------------------------------

    total_problems = (
        schema_problems
        + date_range_problems
        + aggregate_metric_problems
        + duplicate_problems
        + total_metric_problems
        + cross_table_problems
    )

    print()

    if (
        record_count_match
        and total_problems == 0
    ):

        print(
            "✓ ALL CORE VALIDATION CHECKS PASSED."
        )

    else:

        print(
            f"⚠ Validation completed with "
            f"{total_problems:,} issue(s)."
        )

    print()
    print("=" * 75)
    print("VALIDATION COMPLETE")
    print("=" * 75)


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":

    main()