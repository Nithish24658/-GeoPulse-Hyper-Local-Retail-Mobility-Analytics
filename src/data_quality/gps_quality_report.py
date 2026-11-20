"""Generate data quality reports for GeoPulse GPS datasets."""

import numpy as np
import pandas as pd


def generate_quality_report(data: pd.DataFrame) -> dict:
    """Analyze GPS data and return a structured quality report."""

    required_columns = [
        "device_id",
        "latitude",
        "longitude",
        "event_timestamp",
    ]

    missing_columns = [
        column for column in required_columns
        if column not in data.columns
    ]

    missing_by_column = data.isnull().sum().to_dict()

    total_records = len(data)

    unique_devices = (
        data["device_id"].nunique()
        if "device_id" in data.columns else 0
    )

    duplicate_records = int(data.duplicated().sum())

    missing_values = int(data.isnull().sum().sum())

    duplicate_device_timestamps = 0
    if {"device_id", "event_timestamp"}.issubset(data.columns):
        duplicate_device_timestamps = int(
            data.duplicated(
                subset=["device_id", "event_timestamp"]
            ).sum()
        )

    invalid_latitude = 0
    if "latitude" in data.columns:
        latitude = pd.to_numeric(data["latitude"], errors="coerce")
        valid_latitude = (
            latitude.notna()
            & np.isfinite(latitude)
            & latitude.between(-90, 90)
        )
        invalid_latitude = int((~valid_latitude).sum())

    invalid_longitude = 0
    if "longitude" in data.columns:
        longitude = pd.to_numeric(data["longitude"], errors="coerce")
        valid_longitude = (
            longitude.notna()
            & np.isfinite(longitude)
            & longitude.between(-180, 180)
        )
        invalid_longitude = int((~valid_longitude).sum())

    invalid_timestamps = 0
    timezone_aware = False

    if "event_timestamp" in data.columns:
        timestamps = data["event_timestamp"]

        if pd.api.types.is_datetime64_any_dtype(timestamps):
            timezone_aware = timestamps.dt.tz is not None

            if not timezone_aware:
                invalid_timestamps = int(timestamps.notna().sum())
        else:
            invalid_timestamps = int(timestamps.notna().sum())

    invalid_coordinates = invalid_latitude + invalid_longitude

    issues_found = (
        bool(missing_columns)
        or missing_values > 0
        or duplicate_records > 0
        or duplicate_device_timestamps > 0
        or invalid_coordinates > 0
        or invalid_timestamps > 0
    )

    return {
        "total_records": total_records,
        "unique_devices": unique_devices,
        "missing_values": missing_values,
        "missing_values_by_column": missing_by_column,
        "missing_required_columns": missing_columns,
        "duplicate_records": duplicate_records,
        "duplicate_device_timestamps": duplicate_device_timestamps,
        "invalid_latitude": invalid_latitude,
        "invalid_longitude": invalid_longitude,
        "invalid_coordinates": invalid_coordinates,
        "invalid_timestamps": invalid_timestamps,
        "timezone_aware": timezone_aware,
        "quality_status": "REVIEW REQUIRED" if issues_found else "PASS",
    }
