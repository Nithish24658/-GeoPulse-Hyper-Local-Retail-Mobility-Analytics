# Synthetic GPS Data Generation

Week 1 / Day 1 implementation.

## Generate a sample dataset

From the repository root:

```bash
python -m src.data_generation.generate_gps_pings --devices 100 --pings-per-device 10 --seed 42 --output data/generated/gps_pings.csv
```

The default command creates 1,000 synthetic records. The generator supports:
- `--devices`: number of synthetic device IDs
- `--pings-per-device`: number of pings per device
- `--seed`: reproducible random seed
- `--start-time`: timezone-aware ISO-8601 timestamp
- `--interval-minutes`: minutes between pings
- `--output`: local CSV output path

The output schema is `device_id, latitude, longitude, event_timestamp`. Coordinates are mock points within an approximate Bengaluru demonstration bounding box, clustered around synthetic hubs. They are not actual user/device locations.

## Validation and tests

The generator validates required fields, coordinate ranges and timezone-aware timestamps.

```bash
python -m pytest tests/test_data_generation.py -q
```

Generated CSV files belong under `data/generated/`, which is excluded from Git. Do not commit real GPS histories, personal identifiers or licensed datasets without authorization.
