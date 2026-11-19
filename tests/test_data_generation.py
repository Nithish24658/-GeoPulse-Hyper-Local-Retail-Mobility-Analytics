
"""Tests for the GeoPulse synthetic GPS data generator."""

import pandas as pd
import pytest

from src.data_generation.generate_gps_pings import (
    generate_gps_pings,
    save_gps_pings,
    validate_bounds,
    validate_gps_data,
)


def create_valid_gps_data():
    """Create a small valid GPS dataset for validation tests."""
    return pd.DataFrame({
        "device_id": ["DEV000001", "DEV000002"],
        "latitude": [13.0, 12.95],
        "longitude": [77.0, 77.05],
        "event_timestamp": pd.to_datetime(
            ["2026-01-01 10:00:00", "2026-01-01 11:00:00"],
            utc=True,
        ),
    })


def test_default_record_count():
    data = generate_gps_pings()

    assert len(data) == 1000
    assert data["device_id"].nunique() == 100


def test_custom_record_count():
    data = generate_gps_pings(
        num_devices=5,
        pings_per_device=4,
    )

    assert len(data) == 20
    assert data["device_id"].nunique() == 5


def test_generator_is_reproducible():
    first = generate_gps_pings(seed=123)
    second = generate_gps_pings(seed=123)

    pd.testing.assert_frame_equal(first, second)


def test_different_seeds_produce_different_data():
    first = generate_gps_pings(seed=123)
    second = generate_gps_pings(seed=456)

    assert not first.equals(second)


def test_required_columns_exist():
    data = generate_gps_pings()

    expected = {
        "device_id",
        "latitude",
        "longitude",
        "event_timestamp",
    }

    assert set(data.columns) == expected


def test_coordinates_are_valid():
    data = generate_gps_pings()

    assert data["latitude"].between(-90, 90).all()
    assert data["longitude"].between(-180, 180).all()


def test_coordinates_stay_inside_custom_bounds():
    bounds = {
        "latitude_min": 10.0,
        "latitude_max": 11.0,
        "longitude_min": 76.0,
        "longitude_max": 77.0,
    }

    data = generate_gps_pings(
        num_devices=10,
        pings_per_device=5,
        bounds=bounds,
    )

    assert data["latitude"].between(10.0, 11.0).all()
    assert data["longitude"].between(76.0, 77.0).all()


def test_timestamps_are_timezone_aware():
    data = generate_gps_pings()

    assert data["event_timestamp"].dt.tz is not None
    assert str(data["event_timestamp"].dt.tz) == "Asia/Kolkata"


def test_required_values_are_not_null():
    data = generate_gps_pings()

    assert not data.isnull().any().any()


def test_invalid_device_count_is_rejected():
    with pytest.raises(ValueError):
        generate_gps_pings(num_devices=0)


def test_invalid_ping_count_is_rejected():
    with pytest.raises(ValueError):
        generate_gps_pings(pings_per_device=-1)


def test_invalid_time_range_is_rejected():
    with pytest.raises(ValueError):
        generate_gps_pings(
            start_time="2026-01-02 10:00:00",
            end_time="2026-01-02 09:00:00",
        )


def test_invalid_latitude_bounds_are_rejected():
    bounds = {
        "latitude_min": -100,
        "latitude_max": 10,
        "longitude_min": 76,
        "longitude_max": 77,
    }

    with pytest.raises(ValueError):
        validate_bounds(bounds)


def test_missing_required_column_is_rejected():
    data = pd.DataFrame({
        "device_id": ["DEV000001"],
        "latitude": [13.0],
        "longitude": [77.0],
    })

    with pytest.raises(ValueError):
        validate_gps_data(data)


def test_invalid_coordinates_are_rejected():
    data = pd.DataFrame({
        "device_id": ["DEV000001"],
        "latitude": [100.0],
        "longitude": [77.0],
        "event_timestamp": pd.to_datetime(
            ["2026-01-01 10:00:00"],
            utc=True,
        ),
    })

    with pytest.raises(ValueError):
        validate_gps_data(data)


def test_empty_dataset_is_rejected():
    data = pd.DataFrame({
        "device_id": pd.Series(dtype="object"),
        "latitude": pd.Series(dtype="float64"),
        "longitude": pd.Series(dtype="float64"),
        "event_timestamp": pd.Series(dtype="datetime64[ns, UTC]"),
    })

    with pytest.raises(ValueError):
        validate_gps_data(data)


def test_save_gps_pings_creates_csv(tmp_path):
    data = generate_gps_pings(
        num_devices=2,
        pings_per_device=3,
    )

    output_file = tmp_path / "generated" / "gps_pings.csv"
    saved_path = save_gps_pings(data, str(output_file))

    assert saved_path.exists()

    loaded = pd.read_csv(saved_path)

    assert len(loaded) == 6
    assert list(loaded.columns) == list(data.columns)


# Day 2: Additional data-quality validation tests

def test_blank_device_id_is_rejected():
    data = create_valid_gps_data()
    data.loc[0, "device_id"] = "   "

    with pytest.raises(ValueError, match="Device IDs"):
        validate_gps_data(data)


def test_duplicate_device_timestamp_is_rejected():
    data = create_valid_gps_data()
    data.loc[1, "device_id"] = data.loc[0, "device_id"]
    data.loc[1, "event_timestamp"] = data.loc[0, "event_timestamp"]

    with pytest.raises(ValueError, match="Duplicate"):
        validate_gps_data(data)


def test_timezone_naive_timestamp_is_rejected():
    data = create_valid_gps_data()
    data["event_timestamp"] = (
        data["event_timestamp"].dt.tz_localize(None)
    )

    with pytest.raises(ValueError, match="timezone-aware"):
        validate_gps_data(data)


def test_non_numeric_coordinates_are_rejected():
    data = create_valid_gps_data()
    data["latitude"] = ["invalid", 12.95]

    with pytest.raises(ValueError, match="numeric"):
        validate_gps_data(data)


def test_infinite_coordinates_are_rejected():
    data = create_valid_gps_data()
    data.loc[0, "longitude"] = float("inf")

    with pytest.raises(ValueError, match="finite"):
        validate_gps_data(data)
