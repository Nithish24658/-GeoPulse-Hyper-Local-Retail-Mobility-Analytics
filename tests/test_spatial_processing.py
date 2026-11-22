import pytest
from pyspark.sql import SparkSession
from sedona.spark import SedonaContext

from src.spatial_processing.store_catchments import (
    create_store_catchments,
)


@pytest.fixture(scope="module")
def spark():
    session = (
        SedonaContext.builder()
        .master("local[1]")
        .appName("GeoPulse-Spatial-Tests")
        .config(
            "spark.jars.packages",
            "org.apache.sedona:sedona-spark-shaded-3.5_2.12:1.9.1",
        )
        .getOrCreate()
    )

    SedonaContext.create(session)

    yield session

    session.stop()


def create_store_csv(tmp_path, content):
    csv_path = tmp_path / "stores.csv"
    csv_path.write_text(content, encoding="utf-8")
    return csv_path


def valid_store_csv():
    return (
        "store_id,store_name,latitude,longitude\n"
        "STORE001,Store Central,12.9716,77.5946\n"
        "STORE002,Store East,12.975,77.605\n"
    )


def test_creates_catchments_for_valid_stores(spark, tmp_path):
    csv_path = create_store_csv(tmp_path, valid_store_csv())

    result = create_store_catchments(spark, csv_path)

    assert result.count() == 2


def test_preserves_store_information_and_projected_crs(spark, tmp_path):
    csv_path = create_store_csv(tmp_path, valid_store_csv())

    result = create_store_catchments(spark, csv_path)
    rows = result.collect()

    assert rows[0]["store_id"] == "STORE001"
    assert rows[0]["store_name"] == "Store Central"
    assert rows[0]["source_srid"] == 4326
    assert rows[0]["projected_srid"] == 32643


def test_creates_valid_500_metre_catchments(spark, tmp_path):
    csv_path = create_store_csv(tmp_path, valid_store_csv())

    result = create_store_catchments(spark, csv_path)

    validation = result.selectExpr(
        "ST_IsValid(catchment_geometry) AS is_valid",
        "ST_Area(catchment_geometry) AS area",
    ).first()

    assert validation["is_valid"] is True
    assert 750000 < validation["area"] < 800000


def test_rejects_invalid_latitude(spark, tmp_path):
    content = (
        "store_id,store_name,latitude,longitude\n"
        "STORE001,Store Central,100,77.5946\n"
    )
    csv_path = create_store_csv(tmp_path, content)

    with pytest.raises(ValueError, match="invalid values"):
        create_store_catchments(spark, csv_path)


def test_rejects_invalid_longitude(spark, tmp_path):
    content = (
        "store_id,store_name,latitude,longitude\n"
        "STORE001,Store Central,12.9716,200\n"
    )
    csv_path = create_store_csv(tmp_path, content)

    with pytest.raises(ValueError, match="invalid values"):
        create_store_catchments(spark, csv_path)


def test_rejects_duplicate_store_ids(spark, tmp_path):
    content = (
        "store_id,store_name,latitude,longitude\n"
        "STORE001,Store Central,12.9716,77.5946\n"
        "STORE001,Store East,12.975,77.605\n"
    )
    csv_path = create_store_csv(tmp_path, content)

    with pytest.raises(ValueError, match="duplicate store IDs"):
        create_store_catchments(spark, csv_path)


def test_rejects_missing_required_columns(spark, tmp_path):
    content = (
        "store_id,store_name,latitude\n"
        "STORE001,Store Central,12.9716\n"
    )
    csv_path = create_store_csv(tmp_path, content)

    with pytest.raises(ValueError, match="Missing required store columns"):
        create_store_catchments(spark, csv_path)


@pytest.mark.parametrize("distance", [0, -100])
def test_rejects_non_positive_catchment_distance(distance, spark, tmp_path):
    csv_path = create_store_csv(tmp_path, valid_store_csv())

    with pytest.raises(ValueError, match="greater than zero"):
        create_store_catchments(
            spark,
            csv_path,
            catchment_meters=distance,
        )


def test_rejects_missing_csv_file(spark, tmp_path):
    missing_path = tmp_path / "missing_stores.csv"

    with pytest.raises(FileNotFoundError, match="Store CSV not found"):
        create_store_catchments(spark, missing_path)
