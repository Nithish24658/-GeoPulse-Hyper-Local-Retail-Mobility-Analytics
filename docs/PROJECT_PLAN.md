# GeoPulse Project Plan

## 1. Purpose
Build a hyper-local retail mobility analytics pipeline that turns synthetic mobile-location pings into hourly store-footfall insights and store-overlap/cannibalization indicators.

## 2. Scope

### In scope
- Reproducible synthetic GPS ping generation.
- Store reference data and configurable 500 m catchment areas.
- Snowflake raw spatial data storage using `GEOGRAPHY`.
- Distributed spatial joins using PySpark and Apache Sedona.
- dbt transformations for hourly unique visitors and store-level metrics.
- Device-level multi-store visit analysis and an explicitly labelled cannibalization estimate.
- React + Kepler.gl visualization with time filtering and H3 hexagon layers.
- Airflow orchestration and automated data-quality checks.

### Out of scope for the initial build
- Tracking real people or identifying device owners.
- Production-grade commercial forecasting or guaranteed revenue predictions.
- Collecting GPS data from mobile applications.

## 3. Week-wise implementation

### Week 1 – Data synthesis and warehouse loading
**Spatial engineering:** define schemas; generate mock pings with `device_id`, `latitude`, `longitude`, and `event_timestamp`; validate coordinates/timestamps; document Snowflake database, schema, stage and `GEOGRAPHY` table setup; load a small sample first.

**BI/data modelling:** establish raw source naming and column contracts; create initial dbt project configuration and source definitions; document the expected raw-to-model flow.

**Exit criteria:** reproducible synthetic dataset, documented schema, sample successfully loaded, and row-count/coordinate checks recorded.

### Week 2 – Catchments, spatial joins and hourly metrics
**Spatial engineering:** create store points and 500 m catchment polygons; use Sedona/PySpark to assign pings to catchments; test boundary cases and duplicate matches.

**BI/data modelling:** build dbt staging and hourly aggregation models; calculate unique devices per store per hour; add tests for not-null keys, accepted ranges and uniqueness at the intended grain.

**Mid-project review:** demonstrate a representative spatial join; record input/output counts, runtime and memory observations; compare morning and evening patterns; explain limitations and data-quality results.

**Exit criteria:** spatial join output is reproducible; hourly metrics reconcile to validated input; dbt models and tests pass.

### Week 3 – Cannibalization logic and map integration
**Spatial engineering:** calculate device-level visits across stores and time windows; define overlap and potential cannibalization metrics; validate with controlled synthetic scenarios.

**BI/dashboard:** integrate Kepler.gl into React; load aggregated, privacy-safe output; show store points, catchments and footfall layers.

**Exit criteria:** metric definition is documented; test scenarios behave as expected; dashboard renders the agreed aggregate schema.

### Week 4 – Automation and final visualization
**Spatial engineering:** package repeatable processing steps and make jobs parameterized and restartable.

**BI/dashboard:** create Airflow DAGs for dependencies and daily runs; refine Kepler.gl with H3 hexagons, movement layers and a 24-hour time control; add loading/error states and usage notes.

**Exit criteria:** pipeline can be run end-to-end in documented order; dashboard filters time correctly; final demo uses synthetic data and clearly states assumptions.

## 4. Team workstreams / branches
- `feature/spatial-data-engineering`: generator, spatial processing, Snowflake integration and dbt transformations.
- `feature/geospatial-dashboard`: React UI, Kepler.gl layers, dashboard data contract and visual tests.
- `main`: reviewed, working integration baseline and project documentation.

## 5. Definition of done
A task is done only when code is committed to the correct branch, configuration is documented, tests or validation evidence are provided, no secrets or private location data are committed, and the relevant README/docs are updated.

## 6. Important metric definitions
- **Hourly footfall:** count of distinct synthetic device IDs assigned to a store catchment during an hour. It is a proxy metric, not a count of verified customers.
- **Catchment:** a configurable spatial area around a store; the initial exercise uses 500 metres.
- **Potential overlap:** devices appearing in more than one store catchment within a defined time window.
- **Potential cannibalization:** an estimated share of a proposed store's catchment traffic that overlaps with an existing store under an explicitly documented rule. It is not proof that sales will transfer or decline.

## 7. Risks and controls
- Synthetic data may not represent real urban mobility; label all demo results accordingly.
- Coordinate reference systems and distance units must be checked before spatial operations.
- Overlapping catchments can produce multiple matches; document whether the model retains all matches or selects one.
- Device IDs must be synthetic and short-lived within the generated dataset; do not use real identifiers.
- Large-scale performance claims require recorded test environment, input size and runtime evidence.
