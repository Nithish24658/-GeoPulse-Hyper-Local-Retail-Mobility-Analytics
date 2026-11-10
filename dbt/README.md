# dbt Models

Week 1–2 workstream. Initialize a dbt project using the Snowflake adapter after the warehouse schema is agreed.

Planned model layers:
- `sources`: raw GPS pings, stores and spatial match outputs.
- `staging`: normalized timestamps, coordinate/geometry fields and validated records.
- `marts`: hourly store footfall, store overlap and dashboard-ready aggregates.

Add schema tests for required fields, accepted values and model grain. Keep `profiles.yml` credentials outside the repository; use environment variables or the team's approved secret mechanism.
