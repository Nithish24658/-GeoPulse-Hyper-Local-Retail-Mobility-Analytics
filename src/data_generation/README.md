# Synthetic GPS Data Generation

Week 1 workstream. Implement a deterministic generator for mock GPS pings.

Expected output fields:
- `device_id`: generated synthetic ID
- `latitude`: valid WGS84 latitude
- `longitude`: valid WGS84 longitude
- `event_timestamp`: timestamp in the agreed timezone

Recommended design: configurable seed, number of devices, number of pings, time range and city bounding box. Include validation for coordinate ranges and timestamp nulls. Write outputs to an ignored local data directory, not into Git.
