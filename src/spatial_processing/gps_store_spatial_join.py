from pathlib import Path

from pyspark.sql import functions as F

from src.spatial_processing.gps_point_geometry import (
    create_gps_point_geometries,
)
from src.spatial_processing.store_catchments import (
    create_store_catchments,
)


def create_gps_store_spatial_join(
    spark,
    gps_csv: str | Path,
    stores_csv: str | Path,
    catchment_meters: float = 500,
):
    """Match GPS pings with store catchment areas."""

    gps_points = create_gps_point_geometries(spark, gps_csv)

    store_catchments = create_store_catchments(
        spark,
        stores_csv,
        catchment_meters=catchment_meters,
    )

    gps = gps_points.alias("gps")
    stores = store_catchments.alias("store")

    joined = gps.join(
        stores,
        F.expr(
            "ST_Intersects("
            "gps.projected_geometry, "
            "store.catchment_geometry)"
        ),
        "inner",
    )

    return joined.select(
        F.col("gps.device_id").alias("device_id"),
        F.col("gps.latitude").alias("gps_latitude"),
        F.col("gps.longitude").alias("gps_longitude"),
        F.col("gps.parsed_timestamp").alias("event_timestamp"),
        F.col("store.store_id").alias("store_id"),
        F.col("store.store_name").alias("store_name"),
        F.round(
            F.expr(
                "ST_Distance("
                "gps.projected_geometry, "
                "store.store_geometry)"
            ),
            2,
        ).alias("distance_meters"),
    )
