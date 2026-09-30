# NYC Taxi Demand, Revenue & Mobility Analytics

An end-to-end Data Analytics project analyzing **NYC Yellow and Green Taxi trip records from January 2024 through July 2026**.

The project uses **Python, SQL (MySQL), and Power BI** to transform large-scale raw taxi trip data into meaningful insights about demand, revenue, mobility patterns, geography, and payment behavior.

---

## 📌 Project Overview

New York City's taxi trip data contains millions of records covering trip times, locations, distances, fares, payment methods, and other operational attributes.

This project aims to analyze this data to answer questions such as:

- When is taxi demand highest?
- How does demand change across months, days, and hours?
- How do Yellow and Green taxis differ?
- Which pickup and drop-off locations are most active?
- How do fares and revenue vary over time?
- What are the typical trip distances and durations?
- How do payment methods and tipping behavior vary?
- How have taxi patterns changed from 2024 to 2026?

The final output will be an interactive **Power BI dashboard** supported by Python-based data processing and SQL analysis.

---

## 📊 Data Source

The dataset is obtained from the official **New York City Taxi & Limousine Commission (NYC TLC)** Trip Record Data.

### Official Source

- **NYC TLC Trip Record Data:**  
  https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page

- **NYC TLC Trip Record User Guide:**  
  https://www.nyc.gov/assets/tlc/downloads/pdf/trip_record_user_guide.pdf

- **Yellow Taxi Data Dictionary:**  
  https://www.nyc.gov/assets/tlc/downloads/pdf/data_dictionary_trip_records_yellow.pdf

The project uses the official **Parquet trip-record files** published by NYC TLC.

### Data Coverage

| Taxi Type | Period |
|---|---|
| Yellow Taxi | January 2024 – July 2026 |
| Green Taxi | January 2024 – July 2026 |

A total of **62 monthly Parquet files** are currently included:

- 24 Yellow Taxi files for 2024–2025
- 24 Green Taxi files for 2024–2025
- 7 Yellow Taxi files for 2026
- 7 Green Taxi files for 2026

Raw data files are **not stored in this GitHub repository** because of their large size.

---

## 🏗️ Project Architecture

The project follows an end-to-end analytics pipeline:

```text
                    OFFICIAL NYC TLC DATA
                            │
                            ▼
                  Raw Parquet Files
                Yellow + Green Taxi
                            │
                            ▼
                 ┌─────────────────────┐
                 │ Python / Pandas     │
                 │                     │
                 │ • Data Profiling    │
                 │ • Data Cleaning     │
                 │ • Transformation    │
                 │ • Feature Creation  │
                 │ • Data Validation   │
                 └──────────┬──────────┘
                            │
                            ▼
                  Cleaned / Standardized
                         Trip Data
                            │
                            ▼
                 ┌─────────────────────┐
                 │ MySQL               │
                 │                     │
                 │ • Data Storage      │
                 │ • SQL Analysis      │
                 │ • Aggregations      │
                 │ • Business Queries  │
                 └──────────┬──────────┘
                            │
                            ▼
                 ┌─────────────────────┐
                 │ Power BI            │
                 │                     │
                 │ • Data Modeling     │
                 │ • Power Query       │
                 │ • DAX Measures      │
                 │ • Visualization     │
                 └──────────┬──────────┘
                            │
                            ▼
                  Interactive Dashboard
                            │
                            ▼
                  Business Insights