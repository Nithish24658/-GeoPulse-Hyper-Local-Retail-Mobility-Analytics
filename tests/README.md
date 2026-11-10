# Tests and Validation

Add tests alongside each implementation rather than waiting until the final week.

Initial validation checklist:
- Latitude is between -90 and 90; longitude is between -180 and 180.
- Required IDs and timestamps are not null.
- Synthetic generator is reproducible for a fixed seed.
- Catchment radius calculations use metre-based distance semantics.
- Spatial join handles boundary and overlapping catchments as documented.
- Hourly unique visitor counts match a small hand-checked fixture.
- Cannibalization logic passes controlled synthetic scenarios.
- Dashboard data contains aggregates, not device-level records.
