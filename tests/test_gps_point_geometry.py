from pathlib import Path

import pytest
from sedona.spark import SedonaContext

from src.spatial_processing.gps_point_geometry import (
    create_gps_point_geometries,
)


@pytest.fixture(scope="module")
def spark():
    session = (
        SedonaContext.builder()
        .master("local[1]")
        .appName("GeoPulse-GPS-Geometry-Tests")
        .config(
            "spark.jars.packages",
            "org.apache.sedona:sedona-spark-shaded-3.5_2.12:1.9.1",
        )
        .config("spark.sql.session.timeZone", "UTC")
        .getOrCreate()
    )

    SedonaContext.create(session)

    yield session

    session.stop()


@pytest.fixture
def valid_gps_csv(tmp_path):
    csv_path = tmp_path / "gps_test.csv"

    csv_path.write_text(
        "device_id,latitude,longitude,event_timestamp\n"
        "DEV001,12.9716,77.5946,2026-11-10T09:00:00Z\n"
        "DEV002,12.9750,77.6050,2026-11-10T09:10:00Z\n",
        encoding="utf-8",
    )

    return csv_path


def test_processes_all_generated_gps_records(spark):
    gps_path = Path("data/generated/gps_pings.csv")

    result = create_gps_point_geometries(spark, gps_path)

    assert result.count() == 1000


def test_creates_valid_gps_and_projected_geometries(
    spark, valid_gps_csv
):
    result = create_gps_point_geometries(spark, valid_gps_csv)

    assert result.count() == 2

    validity = result.selectExpr(
        "ST_IsValid(gps_geometry) AS gps_valid",
        "ST_IsValid(projected_geometry) AS projected_valid",
    ).collect()

    assert all(row.gps_valid for row in validity)
    assert all(row.projected_valid for row in validity)


def test_uses_correct_coordinate_reference_systems(
    spark, valid_gps_csv
):
    result = create_gps_point_geometries(spark, valid_gps_csv)

    row = result.first()

    assert row.source_srid == 4326
    assert row.projected_srid == 32643


def test_parses_utc_timestamps(spark, valid_gps_csv):
    result = create_gps_point_geometries(spark, valid_gps_csv)

    row = result.first()

    assert row.parsed_timestamp is not None
    epoch = result.selectExpr("unix_timestamp(parsed_timestamp) AS epoch").first()["epoch"]
    assert epoch == 1794301200


def test_rejects_invalid_latitude(spark, tmp_path):
    csv_path = tmp_path / "invalid_latitude.csv"

    csv_path.write_text(
        "device_id,latitude,longitude,event_timestamp\n"
        "DEV001,95,77.5946,2026-11-10T09:00:00Z\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="invalid values"):
        create_gps_point_geometries(spark, csv_path)


def test_rejects_invalid_longitude(spark, tmp_path):
    csv_path = tmp_path / "invalid_longitude.csv"

    csv_path.write_text(
        "device_id,latitude,longitude,event_timestamp\n"
        "DEV001,12.9716,190,2026-11-10T09:00:00Z\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="invalid values"):
        create_gps_point_geometries(spark, csv_path)


def test_rejects_invalid_timestamp(spark, tmp_path):
    csv_path = tmp_path / "invalid_timestamp.csv"

    csv_path.write_text(
        "device_id,latitude,longitude,event_timestamp\n"
        "DEV001,12.9716,77.5946,not-a-timestamp\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="invalid values"):
        create_gps_point_geometries(spark, csv_path)


def test_rejects_missing_required_columns(spark, tmp_path):
    csv_path = tmp_path / "missing_column.csv"

    csv_path.write_text(
        "device_id,latitude,longitude\n"
        "DEV001,12.9716,77.5946\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="Missing required GPS columns"):
        create_gps_point_geometries(spark, csv_path)


def test_rejects_missing_gps_file(spark, tmp_path):
    missing_path = tmp_path / "does_not_exist.csv"

    with pytest.raises(FileNotFoundError, match="GPS CSV not found"):
        create_gps_point_geometries(spark, missing_path)

