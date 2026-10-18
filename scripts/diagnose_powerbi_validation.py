from pathlib import Path
import pandas as pd


POWERBI_DIR = Path("data/powerbi")

EXPECTED_START = pd.Timestamp("2024-01-01")
EXPECTED_END = pd.Timestamp("2026-07-31")


def section(title):
    print("\n" + "=" * 75)
    print(title)
    print("=" * 75)


# ============================================================
# 1. DATE RANGE DIAGNOSTICS
# ============================================================

section("1. OUT-OF-RANGE DATE DIAGNOSTICS")

date_tables = [
    "fact_daily",
    "fact_hourly",
    "fact_location_daily",
    "fact_payment_daily",
]

for table_name in date_tables:
    path = POWERBI_DIR / f"{table_name}.parquet"
    df = pd.read_parquet(path)

    outside = df[
        (df["pickup_date"] < EXPECTED_START)
        | (df["pickup_date"] > EXPECTED_END)
    ].copy()

    print(f"\n{table_name}")
    print(f"Out-of-range rows: {len(outside):,}")

    if len(outside) > 0:
        print(outside.head(20).to_string(index=False))


# ============================================================
# 2. NEGATIVE TOTAL TIPS
# ============================================================

section("2. NEGATIVE TOTAL TIPS")

for table_name in ["fact_payment_daily", "fact_route"]:

    path = POWERBI_DIR / f"{table_name}.parquet"
    df = pd.read_parquet(path)

    negative = df[df["total_tips"] < 0].copy()

    print(f"\n{table_name}")
    print(f"Rows with negative total_tips: {len(negative)}")

    if len(negative) > 0:
        print(negative.to_string(index=False))


# ============================================================
# 3. REVENUE PER MILE INCONSISTENCY
# ============================================================

section("3. REVENUE PER MILE DIAGNOSTIC")

df = pd.read_parquet(
    POWERBI_DIR / "fact_location_daily.parquet"
)

valid = df["total_distance"] > 0

expected = (
    df.loc[valid, "total_revenue"]
    / df.loc[valid, "total_distance"]
)

actual = df.loc[valid, "revenue_per_mile"]

difference = (expected - actual).abs()

# Same tolerance used by many numerical validations
bad = df.loc[valid].loc[difference > 0.01].copy()

print(f"Rows with > 0.01 difference: {len(bad)}")

if len(bad) > 0:

    bad = bad.copy()

    bad["expected_revenue_per_mile"] = (
        bad["total_revenue"]
        / bad["total_distance"]
    )

    bad["difference"] = (
        bad["expected_revenue_per_mile"]
        - bad["revenue_per_mile"]
    )

    print(
        bad[
            [
                "pickup_date",
                "pickup_location_id",
                "taxi_type",
                "total_revenue",
                "total_distance",
                "revenue_per_mile",
                "expected_revenue_per_mile",
                "difference",
            ]
        ].to_string(index=False)
    )


# ============================================================
# 4. SUMMARY
# ============================================================

section("DIAGNOSTIC COMPLETE")

print("No files were modified.")