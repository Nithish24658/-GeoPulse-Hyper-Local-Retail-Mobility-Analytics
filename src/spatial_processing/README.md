# Spatial Processing

Week 2–3 workstream. Uses PySpark and Apache Sedona for distributed spatial operations.

## Implemented Modules

### 1. Store Point and Catchment Geometry

File: `store_catchments.py`

- Loads store information from CSV.
- Validates store IDs, names and geographic coordinates.
- Rejects duplicate store IDs and invalid records.
- Creates store point geometries using WGS84 (EPSG:4326).
- Transforms geometries into UTM Zone 43N (EPSG:32643).
- Generates configurable catchment buffers in metres.
- Default catchment radius: 500 metres.

### 2. GPS Point Geometry Creation

File: `gps_point_geometry.py`

- Loads GPS ping records from CSV using PySpark.
- Validates device IDs, latitude, longitude and timestamps.
- Rejects missing values, invalid coordinates and unparseable timestamps.
- Creates GPS point geometries using WGS84 (EPSG:4326).
- Transforms GPS points into UTM Zone 43N (EPSG:32643).
- Parses UTC timestamps while preserving the original timestamp column.

## Coordinate Reference Systems

| Purpose | CRS | EPSG |
|---|---|---|
| Original GPS and store coordinates | WGS84 | 4326 |
| Projected spatial operations | UTM Zone 43N | 32643 |

Projected coordinates are used for distance-based operations because their units are metres.

## Testing

Automated tests are maintained in:

- `tests/test_spatial_processing.py`
- `tests/test_gps_point_geometry.py`

Current validation coverage includes:

- Store catchment generation.
- GPS point geometry generation.
- Coordinate reference system checks.
- Geometry validity checks.
- UTC timestamp parsing.
- Invalid and missing coordinate handling.
- Duplicate store ID validation.
- Missing input files and required columns.

## Next Planned Steps

3. Spatial join between GPS pings and 500 m store catchments.
4. Hourly aggregation of GPS activity.
5. Device/store overlap analysis.
6. Spatial analysis and dashboard-ready outputs.

## Processing Guidelines

- Validate input data before processing large datasets.
- Start with small samples before scaling up.
- Record coordinate reference systems and distance units.
- Track input/output row counts and execution runtime.
- Review Spark partition settings for larger datasets.
- Handle boundary points and overlapping catchments explicitly.
- Use synthetic or appropriately authorized location data.
