
"""Generate reproducible synthetic GPS pings for GeoPulse."""

from pathlib import Path
from typing import Optional, Tuple

import numpy as np
import pandas as pd


DEFAULT_CITY_BOUNDS = {
    "latitude_min": 12.90,
    "latitude_max": 13.10,
    "longitude_min": 77.50,
    "longitude_max": 77.70,
}


def validate_bounds(
    bounds: dict,
) -> None:
    """Validate geographic bounding-box configuration."""
    required = {
        "latitude_min",
        "latitude_max",
        "longitude_min",
        "longitude_max",
    }

    if not required.issubset(bounds):
        missing = required - set(bounds)
        raise ValueError(f"Missing bounding-box values: {sorted(missing)}")

    lat_min = bounds["latitude_min"]
    lat_max = bounds["latitude_max"]
    lon_min = bounds["longitude_min"]
    lon_max = bounds["longitude_max"]

    if not (-90 <= lat_min < lat_max <= 90):
        raise ValueError("Invalid latitude bounds.")

    if not (-180 <= lon_min < lon_max <= 180):
        raise ValueError("Invalid longitude bounds.")


def validate_gps_data(data: pd.DataFrame) -> None:
    """Validate generated GPS records."""
    required_columns = {
        "device_id",
        "latitude",
        "longitude",
        "event_timestamp",
    }

    missing = required_columns - set(data.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")

    if data.empty:
        raise ValueError("GPS dataset cannot be empty.")

    if data[list(required_columns)].isnull().any().any():
        raise ValueError("GPS data contains missing required values.")

    if not data["latitude"].between(-90, 90).all():
        raise ValueError("Latitude must be between -90 and 90.")

    if not data["longitude"].between(-180, 180).all():
        raise ValueError("Longitude must be between -180 and 180.")

    if not pd.api.types.is_datetime64_any_dtype(
        data["event_timestamp"]
    ):
        raise ValueError("Timestamps must use a datetime data type.")


def generate_gps_pings(
    num_devices: int = 100,
    pings_per_device: int = 10,
    seed: int = 42,
    start_time: str = "2026-01-01 09:00:00",
    end_time: str = "2026-01-01 21:00:00",
    bounds: Optional[dict] = None,
    timezone: str = "Asia/Kolkata",
) -> pd.DataFrame:
    """
    Generate synthetic GPS pings inside a geographic bounding box.

    A fixed seed produces identical records for identical inputs.
    Timestamps are timezone-aware.
    """
    if num_devices <= 0 or pings_per_device <= 0:
        raise ValueError("Device and ping counts must be positive.")

    if not timezone:
        raise ValueError("Timezone cannot be empty.")

    selected_bounds = bounds or DEFAULT_CITY_BOUNDS.copy()
    validate_bounds(selected_bounds)

    start = pd.Timestamp(start_time)
    end = pd.Timestamp(end_time)

    if start.tzinfo is None:
        start = start.tz_localize(timezone)
    else:
        start = start.tz_convert(timezone)

    if end.tzinfo is None:
        end = end.tz_localize(timezone)
    else:
        end = end.tz_convert(timezone)

    if start >= end:
        raise ValueError("Start time must be earlier than end time.")

    rng = np.random.default_rng(seed)
    total_records = num_devices * pings_per_device

    device_ids = np.repeat(
        [f"DEV{i:06d}" for i in range(1, num_devices + 1)],
        pings_per_device,
    )

    latitudes = rng.uniform(
        selected_bounds["latitude_min"],
        selected_bounds["latitude_max"],
        total_records,
    )

    longitudes = rng.uniform(
        selected_bounds["longitude_min"],
        selected_bounds["longitude_max"],
        total_records,
    )

    start_ns = start.value
    end_ns = end.value

    timestamps_ns = rng.integers(
        start_ns,
        end_ns + 1,
        size=total_records,
        dtype=np.int64,
    )

    timestamps = pd.to_datetime(
        timestamps_ns,
        utc=True,
    ).tz_convert(timezone)

    data = pd.DataFrame({
        "device_id": device_ids,
        "latitude": latitudes.round(6),
        "longitude": longitudes.round(6),
        "event_timestamp": timestamps,
    })

    data = data.sort_values(
        ["device_id", "event_timestamp"]
    ).reset_index(drop=True)

    validate_gps_data(data)
    return data


def save_gps_pings(
    data: pd.DataFrame,
    output_path: str = "data/generated/gps_pings.csv",
) -> Path:
    """Validate and save GPS records to a local CSV file."""
    validate_gps_data(data)

    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)

    data.to_csv(destination, index=False)
    return destination


if __name__ == "__main__":
    gps_data = generate_gps_pings(
        num_devices=100,
        pings_per_device=10,
        seed=42,
    )

    output_file = save_gps_pings(gps_data)

    print(f"Generated records: {len(gps_data)}")
    print(f"Unique devices: {gps_data['device_id'].nunique()}")
    print(f"Output file: {output_file}")
    print("\nSample records:")
    print(gps_data.head())
