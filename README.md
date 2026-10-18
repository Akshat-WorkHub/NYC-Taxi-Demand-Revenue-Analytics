# NYC Taxi Demand, Revenue & Mobility Analytics

An end-to-end data analytics project exploring **New York City's Yellow and Green Taxi trip records from January 2024 through July 2026** using Python, Pandas, SQL, and Power BI.

The project transforms large-scale official taxi trip data into analytical datasets and interactive dashboards to investigate demand patterns, revenue trends, geographic mobility, trip characteristics, and payment behavior.

> **Project status:** In progress. Data processing and the Power BI report are being developed incrementally. Features and analytical findings will be documented as they are validated.

## Project Overview

New York City's taxi trip records contain millions of observations covering pickup and drop-off times, locations, trip distances, fares, tips, payment methods, and other operational attributes.

This project aims to turn these records into actionable insights by answering questions such as:

- When and where is taxi demand highest?
- How does demand vary by month, weekday, and hour?
- How do Yellow and Green taxis differ in trip volume and revenue?
- Which pickup and drop-off locations experience the most activity?
- How do fare revenue and tips change over time?
- What patterns exist in trip distance, duration, and payment behavior?
- How have taxi activity patterns changed between 2024 and 2026?

The objective is to demonstrate an end-to-end analytics workflow involving data preparation, validation, analytical transformations, data modeling, visualization, and business interpretation.

## Data Source

The project uses official trip-record data published by the New York City Taxi & Limousine Commission (NYC TLC).

**Official resources**

- [NYC TLC Trip Record Data](https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page)
- [NYC TLC Trip Record User Guide](https://www.nyc.gov/assets/tlc/downloads/pdf/trip_record_user_guide.pdf)
- [Yellow Taxi Trip Record Data Dictionary](https://www.nyc.gov/assets/tlc/downloads/pdf/data_dictionary_trip_records_yellow.pdf)

The source data is published in Parquet format. The project processes Yellow and Green Taxi records and accounts for schema differences across reporting periods.

### Data Coverage

| Taxi type | Period |
|---|---|
| Yellow Taxi | January 2024 – July 2026 |
| Green Taxi | January 2024 – July 2026 |

The working dataset is intended to cover **62 monthly source files**:

- 24 Yellow Taxi files for 2024–2025
- 24 Green Taxi files for 2024–2025
- 7 Yellow Taxi files for January–July 2026
- 7 Green Taxi files for January–July 2026

Verify these counts against the actual source files before publishing.

Raw source data and large intermediate datasets are excluded from GitHub to keep the repository manageable.

## Technology Stack

- **Python and Pandas:** Data inspection, cleaning, transformation, feature engineering, and validation.
- **Parquet:** Efficient columnar storage for large datasets and analytical outputs.
- **SQL / MySQL:** Relational querying and analytical analysis, where implemented.
- **Power BI Desktop:** Data modeling, DAX measures, interactive reports, and visualization.
- **Git and GitHub:** Version control and project documentation.

## Project Architecture

The implemented workflow uses Python to prepare the data and generate analytical datasets for Power BI.

```text
Official NYC TLC Trip Records
          |
          v
Raw Yellow & Green Taxi Parquet Files
          |
          v
Python / Pandas
  - Data profiling
  - Schema standardization
  - Data cleaning
  - Timestamp and trip validation
  - Feature engineering
          |
          v
Cleaned Trip-Level Data
          |
          v
Analytical Aggregation
  - Daily demand
  - Hourly demand
  - Location-level activity
  - Payment-level summaries
  - Route-level summaries
          |
          v
Parquet Analytical Datasets
          |
          v
Power BI Semantic Model
  - Data relationships
  - DAX measures
  - Interactive filters
          |
          v
Power BI Dashboard
          |
          v
Business Analysis & Insights
```

**SQL/MySQL integration:** Include a MySQL stage in this architecture only after the corresponding loading and analysis workflow has been implemented and validated. Do not imply that Power BI queries MySQL directly if the current report uses Parquet-based analytical datasets.

## Data Processing

The processing workflow is designed to preserve the integrity of the source data while making it suitable for analysis.

Key activities include:

- Inspecting source schemas and identifying differences between reporting periods.
- Standardizing relevant fields across Yellow and Green Taxi datasets.
- Validating timestamps and trip records.
- Identifying invalid trip durations and other data-quality issues.
- Preparing cleaned Parquet data for downstream analysis.
- Generating aggregated datasets to support efficient Power BI reporting.

Processing results and validation statistics should be updated in this section as the pipeline evolves.

## Power BI Dashboard

The report is organized into five analytical pages:

1. **Executive Overview** — High-level trip volume, revenue, taxi-type contribution, and payment-method summaries.
2. **Demand Analysis** — Temporal demand patterns and changes in taxi activity.
3. **Revenue Analysis** — Revenue and fare trends across reporting periods and taxi types.
4. **Geographic Analysis** — Pickup-zone activity and spatial mobility patterns.
5. **Trip & Payment Analysis** — Trip characteristics, payment behavior, and related metrics.

The report uses synchronized filters for reporting year, taxi type, and date range to support interactive exploration across pages.

## Repository Structure

```text
NYC-Taxi-Demand-Revenue-Analytics/
|
|-- data/
|   |-- raw/          # Local raw source files; not committed
|   |-- processed/    # Local cleaned/intermediate data
|   |-- powerbi/      # Prepared analytical Parquet datasets
|
|-- notebooks/        # Exploratory analysis
|-- scripts/          # Cleaning, validation, and aggregation
|
|-- NYC_Taxi_Demand_Revenue_Analytics.Report/
|-- NYC_Taxi_Demand_Revenue_Analytics.SemanticModel/
|-- NYC_Taxi_Demand_Revenue_Analytics.pbip
|
|-- NYC_Taxi_Zones.csv
|-- AGENTS.md
|-- PROJECT_CONTEXT.md
|-- README.md
|-- requirements.txt
|-- LICENSE
|-- .gitignore
```

The Power BI report folder, semantic-model folder, and `.pbip` entry point are kept together at the project root. The `data/powerbi/` directory contains prepared datasets rather than the report definition itself.

## Running the Project

### Prerequisites

- Python version compatible with the project dependencies
- Git
- Power BI Desktop
- Required Python packages listed in `requirements.txt`

### Getting started

1. Clone the repository.
2. Install the Python dependencies.
3. Obtain the required monthly Parquet files from the official NYC TLC source.
4. Place the source files in the expected local data directory.
5. Run the relevant processing scripts in the documented order.
6. Generate the required analytical datasets.
7. Open `NYC_Taxi_Demand_Revenue_Analytics.pbip` in Power BI Desktop.
8. Verify the configured data paths and refresh the report when the required local datasets are available.

Exact script commands and processing order should be added after confirming the current implementation.

## Data Availability and Limitations

The source trip records are large and are not committed to this repository. Users may need to download the relevant source files and regenerate the analytical datasets before reproducing the complete workflow.

The report's functionality depends on the availability of its required data files and the correctness of the configured paths. Some analysis may also be affected by missing, invalid, or inconsistent source records.

## Future Improvements

- Complete and document SQL-based analytical queries where applicable.
- Strengthen automated data-quality checks and pipeline reproducibility.
- Refine dashboard layout, accessibility, and visual consistency.
- Expand validated business insights and document their analytical basis.
- Improve refresh and deployment documentation.

## License and Data Attribution

The project code and documentation are governed by the license included in this repository. The underlying trip records are published by NYC TLC; consult the official source and applicable terms for the data.

---

**Author:** Akshat Agarwal

**Project:** NYC Taxi Demand, Revenue & Mobility Analytics