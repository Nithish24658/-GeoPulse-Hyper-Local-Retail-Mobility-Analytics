# GeoPulse Architecture

## High-level data flow

```text
Synthetic GPS ping generator
        |
        v
Raw ping files (local sample / object stage)
        |
        v
Snowflake RAW tables (GEOGRAPHY)
        |
        v
PySpark + Apache Sedona spatial processing
        |  store catchment joins / matched ping records
        v
Snowflake spatial result tables
        |
        v
 dbt staging + hourly aggregates + overlap metrics
        |
        v
Dashboard-ready aggregate views
        |
        v
React application + Kepler.gl

Airflow orchestrates the scheduled pipeline stages.
```

## Data contracts

### `raw_gps_pings`
| Column | Type / meaning |
|---|---|
| `device_id` | Synthetic identifier; never a real device identifier |
| `latitude` | Decimal latitude in WGS84 degrees |
| `longitude` | Decimal longitude in WGS84 degrees |
| `event_timestamp` | Event timestamp with an agreed timezone convention |
| `event_geography` | Snowflake `GEOGRAPHY` point derived from longitude/latitude |

### `dim_stores`
| Column | Type / meaning |
|---|---|
| `store_id` | Stable synthetic store key |
| `store_name` | Demo store label |
| `latitude`, `longitude` | Store point coordinates |
| `catchment_radius_m` | Configurable radius; initial default 500 m |

### `fact_store_footfall_hourly`
| Column | Meaning |
|---|---|
| `store_id` | Store key |
| `hour_start` | Start of aggregation hour |
| `unique_visitors` | Distinct synthetic device IDs in the catchment/hour |
| `ping_count` | Number of matched pings; diagnostic metric |

### `fact_device_store_visits` (restricted processing output)
Use only synthetic IDs. Keep this intermediate dataset out of the public dashboard; aggregate it before visualization. Define retention and access controls before any non-demo use.

## Spatial conventions
- Store latitude/longitude in WGS84 (EPSG:4326).
- Confirm the spatial engine's expected geometry and distance units. Do not assume planar degrees equal metres.
- Use geography-aware distance calculations or project to a suitable metric CRS before applying a 500 m radius.
- Define how pings on polygon boundaries and pings matching multiple catchments are handled.

## Dashboard contract
The frontend should consume aggregate records with `store_id`, `store_name`, `latitude`, `longitude`, `hour_start`, `unique_visitors`, and optional H3 index/count fields. Do not expose device-level rows or raw GPS trails to the browser.

## Configuration and secrets
Read connection settings from environment variables. Keep `.env` out of version control. Use least-privilege Snowflake roles and separate development credentials. Never place credentials in source code, notebooks, screenshots or commits.
