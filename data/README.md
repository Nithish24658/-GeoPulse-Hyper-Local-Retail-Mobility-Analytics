# Data Directory

Generated and downloaded datasets belong here during local development.

- Keep only schema documentation and tiny, non-sensitive examples in Git.
- Store raw/generated CSV or Parquet files under ignored paths such as `data/generated/` or `data/processed/`.
- Use synthetic device identifiers and synthetic coordinates for this project.
- Do not commit real GPS histories, personal identifiers, or licensed datasets without authorization.

Expected ping fields: `device_id`, `latitude`, `longitude`, `event_timestamp`.
