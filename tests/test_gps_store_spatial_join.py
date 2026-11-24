from pathlib import Path

import pytest
from sedona.spark import SedonaContext

from src.spatial_processing.gps_store_spatial_join import (
    create_gps_store_spatial_join,
)


@pytest.fixture(scope="module")
def spark():
    session = (
        SedonaContext.builder()
        .master("local[1]")
        .appName("GeoPulse-GPS-Store-Join-Tests")
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
def spatial_test_files(tmp_path):
    gps_path = tmp_path / "gps.csv"
    stores_path = tmp_path / "stores.csv"

    gps_path.write_text(
        "device_id,latitude,longitude,event_timestamp\n"
        "DEV001,12.9716,77.5946,2026-11-10T09:00:00Z\n"
        "DEV002,12.9750,77.6050,2026-11-10T09:10:00Z\n"
        "DEV003,13.1000,77.7000,2026-11-10T09:20:00Z\n",
        encoding="utf-8",
    )

    stores_path.write_text(
        "store_id,store_name,latitude,longitude\n"
        "STORE001,Central Store,12.9716,77.5946\n"
        "STORE002,East Store,12.9750,77.6050\n",
        encoding="utf-8",
    )

    return gps_path, stores_path


def test_matches_gps_points_inside_store_catchments(
    spark, spatial_test_files
):
    gps_path, stores_path = spatial_test_files

    result = create_gps_store_spatial_join(
        spark, gps_path, stores_path
    )

    assert result.count() == 2


def test_excludes_gps_points_outside_store_catchments(
    spark, spatial_test_files
):
    gps_path, stores_path = spatial_test_files

    result = create_gps_store_spatial_join(
        spark, gps_path, stores_path
    )

    device_ids = {
        row.device_id for row in result.select("device_id").collect()
    }

    assert "DEV003" not in device_ids


def test_returns_correct_device_and_store_matches(
    spark, spatial_test_files
):
    gps_path, stores_path = spatial_test_files

    result = create_gps_store_spatial_join(
        spark, gps_path, stores_path
    )

    matches = {
        row.device_id: row.store_id
        for row in result.select("device_id", "store_id").collect()
    }

    assert matches == {
        "DEV001": "STORE001",
        "DEV002": "STORE002",
    }


def test_calculates_distance_in_meters(
    spark, spatial_test_files
):
    gps_path, stores_path = spatial_test_files

    result = create_gps_store_spatial_join(
        spark, gps_path, stores_path
    )

    distances = [
        row.distance_meters
        for row in result.select("distance_meters").collect()
    ]

    assert all(distance is not None for distance in distances)
    assert all(distance >= 0 for distance in distances)
    assert all(distance == 0 for distance in distances)


def test_returns_expected_output_columns(
    spark, spatial_test_files
):
    gps_path, stores_path = spatial_test_files

    result = create_gps_store_spatial_join(
        spark, gps_path, stores_path
    )

    assert result.columns == [
        "device_id",
        "gps_latitude",
        "gps_longitude",
        "event_timestamp",
        "store_id",
        "store_name",
        "distance_meters",
    ]


def test_rejects_non_positive_catchment_distance(
    spark, spatial_test_files
):
    gps_path, stores_path = spatial_test_files

    with pytest.raises(ValueError, match="greater than zero"):
        create_gps_store_spatial_join(
            spark,
            gps_path,
            stores_path,
            catchment_meters=0,
        )


def test_rejects_missing_gps_file(spark, tmp_path):
    stores_path = tmp_path / "stores.csv"
    stores_path.write_text(
        "store_id,store_name,latitude,longitude\n"
        "STORE001,Central Store,12.9716,77.5946\n",
        encoding="utf-8",
    )

    with pytest.raises(FileNotFoundError, match="GPS CSV not found"):
        create_gps_store_spatial_join(
            spark,
            tmp_path / "missing_gps.csv",
            stores_path,
        )


def test_rejects_missing_store_file(spark, tmp_path):
    gps_path = tmp_path / "gps.csv"
    gps_path.write_text(
        "device_id,latitude,longitude,event_timestamp\n"
        "DEV001,12.9716,77.5946,2026-11-10T09:00:00Z\n",
        encoding="utf-8",
    )

    with pytest.raises(FileNotFoundError, match="Store CSV not found"):
        create_gps_store_spatial_join(
            spark,
            gps_path,
            tmp_path / "missing_stores.csv",
        )


def test_processes_generated_project_gps_data(spark):
    gps_path = Path("data/generated/gps_pings.csv")
    stores_path = Path("data/generated/stores.csv")

    result = create_gps_store_spatial_join(
        spark, gps_path, stores_path
    )

    assert result.count() > 0
