from pathlib import Path
import pyarrow.parquet as pq


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"


def main():
    files = sorted(RAW_DATA_DIR.rglob("*.parquet"))

    print("=" * 70)
    print("NYC TLC DATA PROFILE")
    print("=" * 70)

    print(f"\nTotal Parquet files: {len(files)}")

    total_rows = 0
    total_size = 0

    for file in files:
        parquet_file = pq.ParquetFile(file)

        rows = parquet_file.metadata.num_rows
        columns = parquet_file.metadata.num_columns
        size_mb = file.stat().st_size / (1024 * 1024)

        total_rows += rows
        total_size += file.stat().st_size

        print(
            f"{file.relative_to(PROJECT_ROOT)} | "
            f"Rows: {rows:,} | "
            f"Columns: {columns} | "
            f"Size: {size_mb:.2f} MB"
        )

    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)

    print(f"Total files : {len(files)}")
    print(f"Total rows  : {total_rows:,}")
    print(f"Total size  : {total_size / (1024 ** 3):.2f} GB")


if __name__ == "__main__":
    main()
    