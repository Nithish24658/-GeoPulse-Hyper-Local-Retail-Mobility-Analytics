# Week 1 – Day 1: Project Setup and Synthetic GPS Data

## Objective
Create the first working data-engineering component: a reproducible synthetic GPS-ping generator with a documented data contract and basic validation.

## Work items
- Define the GPS ping schema.
- Generate mock device IDs and movement points with Python.
- Make device count, pings per device, seed, start time and interval configurable.
- Validate required fields, WGS84 coordinate ranges and timezone-aware timestamps.
- Add automated tests for schema, reproducibility, coordinate validity and CSV output.
- Prepare the Snowflake raw-table DDL.

## Data contract

| Field | Type | Description |
|---|---|---|
| device_id | VARCHAR / string | Synthetic device identifier |
| latitude | FLOAT | WGS84 latitude in decimal degrees |
| longitude | FLOAT | WGS84 longitude in decimal degrees |
| event_timestamp | TIMESTAMP_TZ / ISO-8601 | Time of synthetic location event |

The CSV contains the four source fields. Snowflake will derive a GEOGRAPHY point from longitude and latitude when data is loaded.

## Run locally

```bash
python -m src.data_generation.generate_gps_pings --devices 100 --pings-per-device 10 --seed 42 --output data/generated/gps_pings.csv
```

This creates 1,000 records. Generated data is stored locally and excluded from Git.

## Run tests

```bash
python -m pytest tests/test_data_generation.py -q
```

## Snowflake preparation
Review and run snowflake/sql/01_create_raw_gps_pings.sql in the development database/schema after selecting the correct role and warehouse. Never commit account credentials.

## Validation checklist
- [ ] Expected number of rows is generated.
- [ ] Same seed produces identical records.
- [ ] Required fields are populated.
- [ ] Coordinates are valid WGS84 values.
- [ ] Timestamps include timezone information.
- [ ] CSV is created in the ignored generated-data directory.
- [ ] Snowflake raw table DDL is reviewed and executed in the development account.

All data generated for this exercise is synthetic and does not represent real people, devices or observed mobility.
