from pathlib import Path
import requests
from tqdm import tqdm


# ============================================================
# CONFIGURATION
# ============================================================

BASE_URL = "https://d37ci6vzurychx.cloudfront.net/trip-data"

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"

# Years and months to download
DOWNLOAD_PLAN = {
    2024: list(range(1, 13)),   # Jan-Dec
    2025: list(range(1, 13)),   # Jan-Dec
    2026: list(range(1, 10)),   # Jan-Sep
}

TAXI_TYPES = {
    "yellow": "yellow_tripdata",
    "green": "green_tripdata",
}

# HTTP settings
CONNECT_TIMEOUT = 30
READ_TIMEOUT = 300
CHUNK_SIZE = 1024 * 1024  # 1 MB


# ============================================================
# DOWNLOAD FUNCTION
# ============================================================

def download_file(url: str, destination: Path) -> str:
    """
    Download one file from the TLC CloudFront server.

    Returns:
        "downloaded" -> file downloaded successfully
        "skipped"    -> file already exists
        "not_found"  -> server returned 404
        "failed"     -> another error occurred
    """

    # Skip already downloaded files
    if destination.exists() and destination.stat().st_size > 0:
        return "skipped"

    temporary_file = destination.with_suffix(destination.suffix + ".part")

    try:
        with requests.get(
            url,
            stream=True,
            timeout=(CONNECT_TIMEOUT, READ_TIMEOUT),
        ) as response:

            if response.status_code == 404:
                return "not_found"

            response.raise_for_status()

            total_size = int(response.headers.get("content-length", 0))

            with open(temporary_file, "wb") as file:

                progress = tqdm(
                    total=total_size,
                    unit="B",
                    unit_scale=True,
                    unit_divisor=1024,
                    desc=destination.name,
                    leave=True,
                )

                for chunk in response.iter_content(
                    chunk_size=CHUNK_SIZE
                ):
                    if chunk:
                        file.write(chunk)
                        progress.update(len(chunk))

                progress.close()

        # Only mark as complete after successful download
        temporary_file.replace(destination)

        return "downloaded"

    except Exception as error:

        # Remove incomplete download
        if temporary_file.exists():
            temporary_file.unlink()

        print(f"\nERROR: {error}")
        return "failed"


# ============================================================
# MAIN DOWNLOAD PROCESS
# ============================================================

def main():

    print("=" * 70)
    print("NYC TLC YELLOW + GREEN TAXI DATA DOWNLOADER")
    print("=" * 70)

    summary = {
        "downloaded": [],
        "skipped": [],
        "not_found": [],
        "failed": [],
    }

    total_files = sum(len(months) for months in DOWNLOAD_PLAN.values()) * len(
        TAXI_TYPES
    )

    print(f"\nTotal files planned: {total_files}")
    print(f"Download location : {RAW_DATA_DIR}")

    # --------------------------------------------------------
    # Download files
    # --------------------------------------------------------

    for year, months in DOWNLOAD_PLAN.items():

        for taxi_type, file_prefix in TAXI_TYPES.items():

            year_directory = RAW_DATA_DIR / taxi_type / str(year)
            year_directory.mkdir(parents=True, exist_ok=True)

            print("\n" + "=" * 70)
            print(f"{taxi_type.upper()} TAXI - {year}")
            print("=" * 70)

            for month in months:

                month_string = f"{month:02d}"

                filename = (
                    f"{file_prefix}_{year}-{month_string}.parquet"
                )

                url = f"{BASE_URL}/{filename}"

                destination = year_directory / filename

                print(f"\n[{year}-{month_string}]")
                print(f"URL : {url}")
                print(f"FILE: {destination}")

                status = download_file(
                    url=url,
                    destination=destination,
                )

                summary[status].append(
                    f"{taxi_type}/{year}/{filename}"
                )

                if status == "downloaded":
                    print("Status: DOWNLOADED")

                elif status == "skipped":
                    print("Status: ALREADY EXISTS - SKIPPED")

                elif status == "not_found":
                    print("Status: NOT FOUND")

                elif status == "failed":
                    print("Status: FAILED")

    # --------------------------------------------------------
    # Summary
    # --------------------------------------------------------

    print("\n" + "=" * 70)
    print("DOWNLOAD SUMMARY")
    print("=" * 70)

    print(f"Downloaded : {len(summary['downloaded'])}")
    print(f"Skipped    : {len(summary['skipped'])}")
    print(f"Not found  : {len(summary['not_found'])}")
    print(f"Failed     : {len(summary['failed'])}")

    if summary["not_found"]:
        print("\nNOT FOUND FILES:")
        for file in summary["not_found"]:
            print(f"  - {file}")

    if summary["failed"]:
        print("\nFAILED FILES:")
        for file in summary["failed"]:
            print(f"  - {file}")

    print("\n" + "=" * 70)
    print("Download process completed.")
    print("=" * 70)


if __name__ == "__main__":
    main()