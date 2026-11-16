
"""
GeoPulse - GPS Spatial Processing

Loads GPS pings, validates coordinates, and creates
spatial point geometries using Apache Sedona.

Source CRS: EPSG:4326 (WGS84)
Target CRS: EPSG:32643 (UTM Zone 43N)
"""

from pathlib import Path

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, count, expr, lit
from sedona.spark import SedonaContext


PROJECT_ROOT = Path(__file__).resolve().parents[2]
GPS_DATA_PATH = PROJECT_ROOT / "data" / "generated" / "gps_pings.csv"

SOURCE_CRS = "EPSG:4326"
TARGET_CRS = "EPSG:32643"


def create_spark_session():
    """Create a Spark session with Apache Sedona enabled."""

    spark = (
        SparkSession.builder
        .master("local[2]")
        .appName("GeoPulse-GPS-Spatial-Processing")
        .config("spark.sql.session.timeZone", "UTC")
        .config(
            "spark.jars.packages",
            "org.apache.sedona:sedona-spark-shaded-3.5_2.12:1.9.1",
        )
        .getOrCreate()
    )

    spark.sparkContext.setLogLevel("WARN")

    return SedonaContext.create(spark)


def load_gps_data(spark):
    """Load GPS records from the generated CSV file."""

    if not GPS_DATA_PATH.exists():
        raise FileNotFoundError(
            f"GPS dataset not found: {GPS_DATA_PATH}"
        )

    gps_df = (
        spark.read
        .option("header", True)
        .option("inferSchema", True)
        .csv(str(GPS_DATA_PATH))
    )

    return gps_df


def validate_gps_data(gps_df):
    """Validate required fields and geographic coordinate ranges."""

    required_columns = {
        "device_id",
        "latitude",
        "longitude",
        "event_timestamp",
    }

    missing_columns = required_columns - set(gps_df.columns)

    if missing_columns:
        raise ValueError(
            f"Missing required columns: {sorted(missing_columns)}"
        )

    invalid_records = gps_df.filter(
        col("device_id").isNull()
        | col("latitude").isNull()
        | col("longitude").isNull()
        | col("event_timestamp").isNull()
        | (~col("latitude").between(-90, 90))
        | (~col("longitude").between(-180, 180))
    )

    invalid_count = invalid_records.count()

    if invalid_count > 0:
        raise ValueError(
            f"GPS validation failed: {invalid_count} invalid records"
        )

    return gps_df


def create_gps_geometries(spark, gps_df):
    """Create WGS84 point geometries from longitude and latitude."""

    spatial_df = gps_df.withColumn(
        "geometry",
        expr("ST_SetSRID(ST_Point(longitude, latitude), 4326)")
    )

    return spatial_df


def project_gps_geometries(spatial_df):
    """Transform WGS84 geometries into UTM Zone 43N."""

    projected_df = spatial_df.withColumn(
        "projected_geometry",
        expr(
            "ST_Transform(geometry, 'epsg:4326', 'epsg:32643', true)"
        )
    )

    return projected_df


def print_processing_summary(gps_df, spatial_df):
    """Print GPS processing statistics."""

    total_records = gps_df.count()
    total_devices = gps_df.select("device_id").distinct().count()
    spatial_records = spatial_df.count()

    print("\n========== GeoPulse GPS Processing ==========")
    print(f"Input GPS records       : {total_records}")
    print(f"Unique devices          : {total_devices}")
    print(f"Spatial records created : {spatial_records}")
    print(f"Source CRS              : {SOURCE_CRS}")
    print(f"Target CRS              : {TARGET_CRS}")
    print("Distance unit           : Metres")
    print("Timestamp timezone      : UTC")
    print("=============================================\n")


def main():
    """Run the GPS spatial-processing pipeline."""

    spark = None

    try:
        spark = create_spark_session()

        gps_df = load_gps_data(spark)
        gps_df = validate_gps_data(gps_df)

        spatial_df = create_gps_geometries(spark, gps_df)
        projected_df = project_gps_geometries(spatial_df)

        print_processing_summary(gps_df, projected_df)

        projected_df.select(
            "device_id",
            "latitude",
            "longitude",
            "event_timestamp",
            "geometry",
            "projected_geometry",
        ).show(5, truncate=False)

    finally:
        if spark is not None:
            spark.stop()


if __name__ == "__main__":
    main()
