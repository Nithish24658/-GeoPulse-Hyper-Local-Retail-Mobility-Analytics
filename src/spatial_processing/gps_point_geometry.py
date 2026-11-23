from pathlib import Path

from pyspark.sql import functions as F


SOURCE_CRS = 4326
PROJECTED_CRS = 32643


def create_gps_point_geometries(spark, gps_csv: str | Path):
    """Load, validate and create projected spatial geometries for GPS pings."""

    gps_path = Path(gps_csv)

    if not gps_path.is_file():
        raise FileNotFoundError(f"GPS CSV not found: {gps_path}")

    gps = (
        spark.read
        .option("header", True)
        .option("inferSchema", False)
        .csv(str(gps_path))
    )

    required_columns = {
        "device_id",
        "latitude",
        "longitude",
        "event_timestamp",
    }

    missing_columns = required_columns.difference(gps.columns)

    if missing_columns:
        raise ValueError(
            f"Missing required GPS columns: {sorted(missing_columns)}"
        )

    gps = gps.select(
        F.col("device_id").cast("string").alias("device_id"),
        F.col("latitude").cast("double").alias("latitude"),
        F.col("longitude").cast("double").alias("longitude"),
        F.col("event_timestamp").cast("string").alias("event_timestamp"),
    )

    gps = gps.withColumn(
        "parsed_timestamp",
        F.to_timestamp(
            "event_timestamp",
            "yyyy-MM-dd'T'HH:mm:ssX"
        )
    )

    invalid_count = gps.filter(
        F.col("device_id").isNull()
        | (F.trim(F.col("device_id")) == "")
        | F.col("latitude").isNull()
        | F.isnan("latitude")
        | (F.abs(F.col("latitude")) == float("inf"))
        | (F.col("latitude") < -90)
        | (F.col("latitude") > 90)
        | F.col("longitude").isNull()
        | F.isnan("longitude")
        | (F.abs(F.col("longitude")) == float("inf"))
        | (F.col("longitude") < -180)
        | (F.col("longitude") > 180)
        | F.col("parsed_timestamp").isNull()
    ).count()

    if invalid_count:
        raise ValueError(
            f"Found {invalid_count} GPS records with missing or invalid values."
        )

    gps.createOrReplaceTempView("validated_geopulse_gps")

    return spark.sql(f"""
        SELECT
            device_id,
            latitude,
            longitude,
            event_timestamp,
            parsed_timestamp,
            {SOURCE_CRS} AS source_srid,
            {PROJECTED_CRS} AS projected_srid,
            ST_SetSRID(
                ST_Point(longitude, latitude),
                {SOURCE_CRS}
            ) AS gps_geometry,
            ST_Transform(
                ST_SetSRID(
                    ST_Point(longitude, latitude),
                    {SOURCE_CRS}
                ),
                'EPSG:{PROJECTED_CRS}'
            ) AS projected_geometry
        FROM validated_geopulse_gps
    """)

