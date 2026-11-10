# Spatial Processing

Week 2–3 workstream. Use PySpark and Apache Sedona for distributed spatial operations.

Planned modules:
1. Store point and catchment geometry creation.
2. GPS ping geometry creation and spatial reference checks.
3. Spatial join between pings and 500 m store catchments.
4. Hourly aggregation inputs and device/store overlap analysis.

Before processing large inputs, validate on a small sample. Record CRS, distance units, input/output row counts, runtime and partition settings. Handle boundary points and overlapping catchments explicitly.
