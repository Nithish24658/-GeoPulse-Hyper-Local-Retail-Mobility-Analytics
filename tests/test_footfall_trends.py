
from datetime import datetime, timezone

import pytest
from sedona.spark import SedonaContext

from src.analytics.footfall_trends import (
    generate_hourly_footfall_trends,
    generate_daily_footfall_trends,
    summarize_peak_and_quiet_hours,
)


@pytest.fixture(scope="module")
def spark():
    session = (
        SedonaContext.builder()
        .master("local[1]")
        .appName("GeoPulse-Footfall-Trend-Tests")
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
def hourly_data(spark):
    data = [
        ("STORE001", "Central Store", datetime(2026, 11, 10, 9, 0, tzinfo=timezone.utc), 10, 5),
        ("STORE001", "Central Store", datetime(2026, 11, 10, 10, 0, tzinfo=timezone.utc), 5, 3),
        ("STORE001", "Central Store", datetime(2026, 11, 11, 9, 0, tzinfo=timezone.utc), 20, 8),
        ("STORE001", "Central Store", datetime(2026, 11, 12, 9, 0, tzinfo=timezone.utc), 30, 10),
        ("STORE002", "East Store", datetime(2026, 11, 10, 11, 0, tzinfo=timezone.utc), 8, 4),
        ("STORE002", "East Store", datetime(2026, 11, 10, 12, 0, tzinfo=timezone.utc), 16, 7),
    ]

    columns = [
        "store_id",
        "store_name",
        "hour",
        "total_gps_pings",
        "unique_devices",
    ]

    return spark.createDataFrame(data, columns)


def test_generates_hourly_footfall_totals(hourly_data):
    result = generate_hourly_footfall_trends(hourly_data)

    central_nine = result.filter(
        "store_id = 'STORE001' AND hour_of_day = 9"
    ).first()

    assert central_nine.total_gps_pings == 60
    assert central_nine.avg_gps_pings == 20.0
    assert central_nine.observed_hours == 3


def test_generates_hourly_footfall_for_each_store(hourly_data):
    result = generate_hourly_footfall_trends(hourly_data)

    east_eleven = result.filter(
        "store_id = 'STORE002' AND hour_of_day = 11"
    ).first()

    assert east_eleven.total_gps_pings == 8
    assert east_eleven.avg_gps_pings == 8.0


def test_generates_daily_footfall_totals(hourly_data):
    result = generate_daily_footfall_trends(hourly_data)

    central_day = result.filter(
        "store_id = 'STORE001' AND date = '2026-11-10'"
    ).first()

    assert central_day.total_gps_pings == 15
    assert central_day.active_store_hours == 2
    assert central_day.avg_pings_per_active_hour == 7.5


def test_separates_daily_footfall_by_date(hourly_data):
    result = generate_daily_footfall_trends(hourly_data)

    central_days = result.filter(
        "store_id = 'STORE001'"
    ).count()

    assert central_days == 3


def test_identifies_peak_and_quiet_hours(hourly_data):
    hourly_trends = generate_hourly_footfall_trends(hourly_data)
    result = summarize_peak_and_quiet_hours(hourly_trends)

    central = result.filter(
        "store_id = 'STORE001'"
    ).first()

    assert central.peak_hour == 9
    assert central.peak_avg_gps_pings == 20.0
    assert central.quiet_hour == 10
    assert central.quiet_avg_gps_pings == 5.0


def test_identifies_peak_hours_for_each_store(hourly_data):
    hourly_trends = generate_hourly_footfall_trends(hourly_data)
    result = summarize_peak_and_quiet_hours(hourly_trends)

    east = result.filter(
        "store_id = 'STORE002'"
    ).first()

    assert east.peak_hour == 12
    assert east.quiet_hour == 11


def test_rejects_missing_hourly_columns(spark):
    invalid_data = spark.createDataFrame(
        [("STORE001", 10)],
        ["store_id", "total_gps_pings"],
    )

    with pytest.raises(ValueError, match="Missing required columns"):
        generate_hourly_footfall_trends(invalid_data)


def test_rejects_missing_columns_in_peak_summary(spark):
    invalid_data = spark.createDataFrame(
        [("STORE001", 9)],
        ["store_id", "hour_of_day"],
    )

    with pytest.raises(ValueError, match="Missing required columns"):
        summarize_peak_and_quiet_hours(invalid_data)
