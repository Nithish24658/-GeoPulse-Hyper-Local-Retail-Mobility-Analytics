from datetime import datetime, timezone

import pytest

from src.data_generation.generate_gps_pings import (
    FIELDNAMES, generate_records, parse_timestamp, validate_records, write_csv,
)


def test_expected_row_count_and_schema():
    records = generate_records(device_count=3, pings_per_device=4)
    assert len(records) == 12
    assert list(records[0]) == FIELDNAMES


def test_same_seed_produces_same_records():
    assert generate_records(2, 3, seed=7) == generate_records(2, 3, seed=7)


def test_ids_are_synthetic_and_reused_per_device():
    records = generate_records(2, 2)
    assert [row["device_id"] for row in records] == [
        "DEV000001", "DEV000001", "DEV000002", "DEV000002"
    ]


def test_coordinates_are_valid():
    for row in generate_records(10, 5):
        assert -90 <= float(row["latitude"]) <= 90
        assert -180 <= float(row["longitude"]) <= 180


def test_invalid_latitude_is_rejected():
    bad_row = {"device_id": "DEV000001", "latitude": 95, "longitude": 77.5,
               "event_timestamp": "2026-11-10T09:00:00Z"}
    with pytest.raises(ValueError, match="invalid latitude"):
        validate_records([bad_row])


def test_start_time_requires_timezone():
    with pytest.raises(ValueError, match="timezone"):
        parse_timestamp("2026-11-10T09:00:00")


def test_csv_output(tmp_path):
    output = tmp_path / "generated" / "sample.csv"
    write_csv(generate_records(2, 2), output)
    lines = output.read_text(encoding="utf-8").splitlines()
    assert lines[0] == ",".join(FIELDNAMES)
    assert len(lines) == 5


def test_invalid_generation_parameters_are_rejected():
    with pytest.raises(ValueError, match="at least 1"):
        generate_records(device_count=0)
