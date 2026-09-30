import pandas as pd


TLC_BASE_URL = "https://d37ci6vzurychx.cloudfront.net/trip-data"

FILES = {
    "Yellow 2024": f"{TLC_BASE_URL}/yellow_tripdata_2024-01.parquet",
    "Yellow 2025": f"{TLC_BASE_URL}/yellow_tripdata_2025-01.parquet",
    "Yellow 2026": f"{TLC_BASE_URL}/yellow_tripdata_2026-01.parquet",

    "Green 2024": f"{TLC_BASE_URL}/green_tripdata_2024-01.parquet",
    "Green 2025": f"{TLC_BASE_URL}/green_tripdata_2025-01.parquet",
    "Green 2026": f"{TLC_BASE_URL}/green_tripdata_2026-01.parquet",
}


def inspect_file(year, url):
    print("\n" + "=" * 70)
    print(f"{year} — January Yellow Taxi Trip Data")
    print("=" * 70)

    try:
        df = pd.read_parquet(url)

        print(f"Rows       : {len(df):,}")
        print(f"Columns    : {len(df.columns)}")

        print("\nColumns:")
        for column in df.columns:
            print(f"  - {column}")

        print("\nData Types:")
        print(df.dtypes)

        print("\nFirst 5 Rows:")
        print(df.head())

    except Exception as e:
        print(f"ERROR while reading {year} file:")
        print(e)


def main():
    print("NYC TLC Yellow Taxi — Schema Inspection")
    print("=" * 70)

    for year, url in FILES.items():
        inspect_file(year, url)

    print("\n" + "=" * 70)
    print("Inspection completed.")
    print("=" * 70)


if __name__ == "__main__":
    main()