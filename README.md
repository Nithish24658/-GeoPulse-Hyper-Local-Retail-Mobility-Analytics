# GeoPulse – Hyper-Local Retail Mobility Analytics

GeoPulse is a geospatial analytics project that uses **synthetic, anonymized-style mobile GPS pings** to understand movement patterns, estimate hourly footfall around retail locations, and assess potential store cannibalization before a new store is opened.

> Development note: this repository starts with a project scaffold. The week-wise implementation will be added incrementally. Use synthetic or properly authorized, privacy-preserving data only; never commit real device identifiers, precise personal movement histories, credentials, or private datasets.

## Project goals

- Generate reproducible mock mobility pings (`device_id`, latitude, longitude, timestamp).
- Store and query spatial data in Snowflake using `GEOGRAPHY`.
- Build store catchment areas and perform scalable spatial joins with Apache Sedona / PySpark.
- Transform raw spatial results into hourly store-footfall metrics with dbt.
- Measure overlap between store visits and estimate potential cannibalization.
- Visualize footfall patterns and time-based movement in a React + Kepler.gl dashboard.
- Orchestrate repeatable pipeline jobs with Apache Airflow.

## Technology stack

| Layer | Technology |
|---|---|
| Warehouse | Snowflake |
| Spatial processing | Python, PySpark, Apache Sedona |
| Transformation | dbt (Snowflake adapter) |
| Visualization | Kepler.gl, React |
| Orchestration | Apache Airflow |
| Testing | pytest, dbt tests |

## Week-wise roadmap

| Phase | Deliverables |
|---|---|
| Week 1 | Synthetic GPS-ping generator; Snowflake setup, raw schema and loading plan |
| Week 2 | 500-metre store catchments; Sedona spatial joins; dbt hourly visitor models; data-quality checks |
| Mid-project review | Demonstrate spatial processing at scale and validate morning/evening footfall outputs |
| Week 3 | Device-level multi-store visit logic and cannibalization metrics; React + Kepler.gl map integration |
| Week 4 | Airflow orchestration; 3D H3 hexagon layer; 24-hour time slider and final refinements |
| Final review | End-to-end pipeline, documented assumptions, validated metrics and interactive dashboard |

## Repository structure

```text
.
├── data/                 # Data instructions; generated data stays local/ignored
├── dbt/                  # dbt project and Snowflake models
├── docs/                 # Scope, architecture, decisions and weekly plan
├── dashboard/            # React + Kepler.gl application
├── orchestration/        # Airflow DAGs
├── src/
│   ├── data_generation/  # Synthetic GPS ping generation
│   └── spatial_processing/ # Catchments and spatial joins
├── tests/                # Python and pipeline tests
├── .env.example          # Environment variable template (no secrets)
├── .gitignore
└── requirements.txt
```

## Getting started

1. Create a Python virtual environment.
2. Install the Python dependencies listed in `requirements.txt` that apply to your development environment.
3. Copy `.env.example` to `.env` and fill in your own Snowflake connection values locally.
4. Generate synthetic data using the Week 1 generator (to be implemented).
5. Follow the setup instructions in [`docs/PROJECT_PLAN.md`](docs/PROJECT_PLAN.md) and [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).

Do not commit `.env`, credentials, raw personal location data, or generated large datasets.

## Team branch workflow

- `main` – shared project outline and stable integration point.
- `feature/spatial-data-engineering` – synthetic data, Snowflake, Sedona/PySpark and dbt pipeline.
- `feature/geospatial-dashboard` – React, Kepler.gl, map layers and time-based visualization.

Work in the relevant feature branch and merge through pull requests after review. Keep interfaces and sample schemas aligned with the architecture document.

## Current status

**Scaffold initialized.** Implementation is planned week by week; features should be marked complete only after they are implemented and tested.
