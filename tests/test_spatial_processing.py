
import os
import sys

import pytest
from pyspark.sql import SparkSession
from sedona.spark import SedonaContext

from src.spatial_processing.gps_spatial import (
    validate_gps_data,
    create_gps_geometries,
    project_gps_geometries,
)


@pytest.fixture(scope="module")
def spark():
    """Start Spark with Apache Sedona and the active Python environment."""

    os.environ["PYSPARK_PYTHON"] = sys.executable
    os.environ["PYSPARK_DRIVER_PYTHON"] = sys.executable

    session = (
        SparkSession.builder
        .master("local[2]")
        .appName("GeoPulse-Spatial-Tests")
        .config("spark.sql.session.timeZone", "UTC")
        .config("spark.python.worker.reuse", "true")
        .config(
            "spark.jars.packages",
            "org.apache.sedona:sedona-spark-shaded-3.5_2.12:1.9.1",
        )
        .getOrCreate()
    )

    session.sparkContext.setLogLevel("ERROR")

    # Register Apache Sedona spatial functions.
    session = SedonaContext.create(session)

    yield session

    session.stop()


def create_gps_dataframe(spark, rows):
    """Create a small GPS DataFrame for testing."""

    schema = [
        "device_id",
        "latitude",
        "longitude",
        "event_timestamp",
    ]

    return spark.createDataFrame(rows, schema)


def test_valid_gps_records_pass_validation(spark):
    rows = [
        ("DEV000001", 12.97215, 77.60465, "2026-11-10T09:00:00Z"),
        ("DEV000002", 12.97132, 77.60536, "2026-11-10T09:10:00Z"),
    ]

    gps_df = create_gps_dataframe(spark, rows)
    validated_df = validate_gps_data(gps_df)

    assert validated_df.count() == 2


def test_invalid_latitude_is_rejected(spark):
    rows = [
        ("DEV000001", 95.0, 77.60465, "2026-11-10T09:00:00Z"),
    ]

    gps_df = create_gps_dataframe(spark, rows)

    with pytest.raises(ValueError, match="invalid records"):
        validate_gps_data(gps_df)


def test_invalid_longitude_is_rejected(spark):
    rows = [
        ("DEV000001", 12.97215, 200.0, "2026-11-10T09:00:00Z"),
    ]

    gps_df = create_gps_dataframe(spark, rows)

    with pytest.raises(ValueError, match="invalid records"):
        validate_gps_data(gps_df)


def test_missing_required_column_is_rejected(spark):
    gps_df = spark.createDataFrame(
        [("DEV000001", 12.97215, 77.60465)],
        ["device_id", "latitude", "longitude"],
    )

    with pytest.raises(ValueError, match="Missing required columns"):
        validate_gps_data(gps_df)


def test_gps_geometry_creation(spark):
    rows = [
        ("DEV000001", 12.97215, 77.60465, "2026-11-10T09:00:00Z"),
    ]

    gps_df = create_gps_dataframe(spark, rows)
    spatial_df = create_gps_geometries(spark, gps_df)

    geometry = spatial_df.selectExpr(
        "ST_AsText(geometry) AS geometry_text"
    ).first()["geometry_text"]

    assert geometry == "POINT (77.60465 12.97215)"


def test_gps_geometry_projection(spark):
    rows = [
        ("DEV000001", 12.97215, 77.60465, "2026-11-10T09:00:00Z"),
    ]

    gps_df = create_gps_dataframe(spark, rows)
    spatial_df = create_gps_geometries(spark, gps_df)
    projected_df = project_gps_geometries(spatial_df)

    projected_point = projected_df.selectExpr(
        "ST_AsText(projected_geometry) AS projected_text"
    ).first()["projected_text"]

    assert projected_point.startswith("POINT (")
    assert projected_point != "POINT (77.60465 12.97215)"
