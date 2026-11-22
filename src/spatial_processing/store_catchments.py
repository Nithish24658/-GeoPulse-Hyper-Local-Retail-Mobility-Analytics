from pathlib import Path

from sedona.spark import SedonaContext


SOURCE_CRS = 4326
PROJECTED_CRS = 32643
DEFAULT_CATCHMENT_METERS = 500


def create_store_catchments(
    spark,
    stores_csv: str | Path,
    catchment_meters: float = DEFAULT_CATCHMENT_METERS,
):
    """Create projected store points and metre-based catchment buffers."""

    if catchment_meters <= 0:
        raise ValueError("catchment_meters must be greater than zero.")

    stores_path = Path(stores_csv)

    if not stores_path.is_file():
        raise FileNotFoundError(f"Store CSV not found: {stores_path}")

    stores = (
        spark.read
        .option("header", True)
        .option("inferSchema", True)
        .csv(str(stores_path))
    )

    required_columns = {
        "store_id",
        "store_name",
        "latitude",
        "longitude",
    }

    missing_columns = required_columns.difference(stores.columns)

    if missing_columns:
        raise ValueError(
            f"Missing required store columns: {sorted(missing_columns)}"
        )

    stores.createOrReplaceTempView("geopulse_stores")

    invalid_count = spark.sql("""
        SELECT COUNT(*) AS invalid_count
        FROM geopulse_stores
        WHERE store_id IS NULL
           OR TRIM(CAST(store_id AS STRING)) = ''
           OR store_name IS NULL
           OR latitude IS NULL
           OR longitude IS NULL
           OR latitude < -90
           OR latitude > 90
           OR longitude < -180
           OR longitude > 180
    """).first()["invalid_count"]

    if invalid_count:
        raise ValueError(
            f"Found {invalid_count} stores with missing or invalid values."
        )

    duplicate_count = spark.sql("""
        SELECT COUNT(*) AS duplicate_count
        FROM (
            SELECT store_id
            FROM geopulse_stores
            GROUP BY store_id
            HAVING COUNT(*) > 1
        )
    """).first()["duplicate_count"]

    if duplicate_count:
        raise ValueError(
            f"Found {duplicate_count} duplicate store IDs."
        )

    stores.createOrReplaceTempView("validated_geopulse_stores")

    return spark.sql(f"""
        SELECT
            store_id,
            store_name,
            latitude,
            longitude,
            {SOURCE_CRS} AS source_srid,
            {PROJECTED_CRS} AS projected_srid,
            ST_Transform(
                ST_SetSRID(
                    ST_Point(longitude, latitude),
                    {SOURCE_CRS}
                ),
                'EPSG:{PROJECTED_CRS}'
            ) AS store_geometry,
            ST_Buffer(
                ST_Transform(
                    ST_SetSRID(
                        ST_Point(longitude, latitude),
                        {SOURCE_CRS}
                    ),
                    'EPSG:{PROJECTED_CRS}'
                ),
                {float(catchment_meters)}
            ) AS catchment_geometry
        FROM validated_geopulse_stores
    """)
