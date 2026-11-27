from datetime import datetime, timezone

import pytest
from pyspark.sql import functions as F
from sedona.spark import SedonaContext

from src.spatial_processing.hourly_footfall import (
    aggregate_hourly_footfall,
)


@pytest.fixture(scope="module")
def spark():
    session = (
        SedonaContext.builder()
        .master("local[1]")
        .appName("GeoPulse-Hourly-Footfall-Tests")
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
def matched_pings(spark):
    data = [
        (
            "DEV001", "STORE001", "Central Store",
            datetime(2026, 11, 10, 9, 5, tzinfo=timezone.utc), 0.0
        ),
        (
            "DEV001", "STORE001", "Central Store",
            datetime(2026, 11, 10, 9, 15, tzinfo=timezone.utc), 10.0
        ),
        (
            "DEV002", "STORE001", "Central Store",
            datetime(2026, 11, 10, 9, 30, tzinfo=timezone.utc), 20.0
        ),
        (
            "DEV001", "STORE001", "Central Store",
            datetime(2026, 11, 10, 10, 5, tzinfo=timezone.utc), 5.0
        ),
        (
            "DEV003", "STORE002", "East Store",
            datetime(2026, 11, 10, 9, 10, tzinfo=timezone.utc), 0.0
        ),
    ]

    columns = [
        "device_id",
        "store_id",
        "store_name",
        "event_timestamp",
        "distance_meters",
    ]

    return spark.createDataFrame(data, columns)


@pytest.fixture
def aggregated_result(
    spark, matched_pings, monkeypatch
):
    def mock_spatial_join(*args, **kwargs):
        return matched_pings

    monkeypatch.setattr(
        "src.spatial_processing.hourly_footfall.create_gps_store_spatial_join",
        mock_spatial_join,
    )

    return aggregate_hourly_footfall(
        spark,
        "unused_gps.csv",
        "unused_stores.csv",
    )


def test_calculates_total_gps_pings_per_store_hour(
    aggregated_result,
):
    central_morning = (
        aggregated_result
        .filter(F.col("store_id") == "STORE001")
        .filter(F.hour("hour") == 9)
        .first()
    )

    assert central_morning.total_gps_pings == 3


def test_calculates_unique_devices_per_store_hour(
    aggregated_result,
):
    central_morning = (
        aggregated_result
        .filter(F.col("store_id") == "STORE001")
        .filter(F.hour("hour") == 9)
        .first()
    )

    assert central_morning.unique_devices == 2


def test_separates_different_hours(
    aggregated_result,
):
    central_rows = (
        aggregated_result
        .filter(F.col("store_id") == "STORE001")
        .withColumn("hour_of_day", F.hour("hour"))
        .select("hour_of_day", "total_gps_pings")
        .collect()
    )

    hourly_counts = {
        row.hour_of_day: row.total_gps_pings
        for row in central_rows
    }

    assert len(hourly_counts) == 2
    assert hourly_counts[9] == 3
    assert hourly_counts[10] == 1


def test_groups_footfall_by_store(
    aggregated_result,
):
    east_store = (
        aggregated_result
        .filter(F.col("store_id") == "STORE002")
        .first()
    )

    assert east_store.total_gps_pings == 1
    assert east_store.unique_devices == 1


def test_returns_expected_output_columns(
    aggregated_result,
):
    assert aggregated_result.columns == [
        "store_id",
        "store_name",
        "hour",
        "total_gps_pings",
        "unique_devices",
    ]


def test_sorts_results_by_store_and_hour(
    aggregated_result,
):
    rows = aggregated_result.collect()

    keys = [
        (row.store_id, row.hour)
        for row in rows
    ]

    assert keys == sorted(keys)
