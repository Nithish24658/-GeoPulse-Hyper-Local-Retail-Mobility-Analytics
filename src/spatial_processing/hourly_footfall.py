from pyspark.sql import functions as F

from src.spatial_processing.gps_store_spatial_join import (
    create_gps_store_spatial_join,
)


def aggregate_hourly_footfall(
    spark,
    gps_csv,
    stores_csv,
    catchment_meters=500,
):
    """Aggregate matched GPS pings into hourly store footfall metrics."""

    matched_pings = create_gps_store_spatial_join(
        spark,
        gps_csv,
        stores_csv,
        catchment_meters=catchment_meters,
    )

    hourly_footfall = (
        matched_pings
        .withColumn(
            "hour",
            F.date_trunc("hour", F.col("event_timestamp")),
        )
        .groupBy(
            "store_id",
            "store_name",
            "hour",
        )
        .agg(
            F.count("*").alias("total_gps_pings"),
            F.countDistinct("device_id").alias("unique_devices"),
        )
        .orderBy(
            "store_id",
            "hour",
        )
    )

    return hourly_footfall
