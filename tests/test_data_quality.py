"""Tests for the GeoPulse GPS data quality report."""

import pandas as pd

from src.data_generation.generate_gps_pings import generate_gps_pings
from src.data_quality.gps_quality_report import generate_quality_report


def create_valid_data():
    return generate_gps_pings(
        num_devices=3,
        pings_per_device=2,
        seed=42,
    )


def test_quality_report_counts_records_and_devices():
    report = generate_quality_report(create_valid_data())

    assert report["total_records"] == 6
    assert report["unique_devices"] == 3


def test_valid_data_receives_pass_status():
    report = generate_quality_report(create_valid_data())

    assert report["quality_status"] == "PASS"


def test_missing_values_are_detected():
    data = create_valid_data()
    data.loc[0, "latitude"] = float("nan")

    report = generate_quality_report(data)

    assert report["missing_values"] == 1
    assert report["quality_status"] == "REVIEW REQUIRED"


def test_duplicate_records_are_detected():
    data = create_valid_data()
    data = pd.concat([data, data.iloc[[0]]], ignore_index=True)

    report = generate_quality_report(data)

    assert report["duplicate_records"] == 1
    assert report["duplicate_device_timestamps"] == 1


def test_invalid_latitude_is_detected():
    data = create_valid_data()
    data.loc[0, "latitude"] = 100.0

    report = generate_quality_report(data)

    assert report["invalid_latitude"] == 1
    assert report["invalid_coordinates"] == 1


def test_invalid_longitude_is_detected():
    data = create_valid_data()
    data.loc[0, "longitude"] = 200.0

    report = generate_quality_report(data)

    assert report["invalid_longitude"] == 1


def test_timezone_naive_timestamps_are_detected():
    data = create_valid_data()
    data["event_timestamp"] = data["event_timestamp"].dt.tz_localize(None)

    report = generate_quality_report(data)

    assert report["timezone_aware"] is False
    assert report["invalid_timestamps"] == len(data)


def test_missing_required_columns_are_reported():
    data = create_valid_data().drop(columns=["latitude"])

    report = generate_quality_report(data)

    assert "latitude" in report["missing_required_columns"]
    assert report["quality_status"] == "REVIEW REQUIRED"
