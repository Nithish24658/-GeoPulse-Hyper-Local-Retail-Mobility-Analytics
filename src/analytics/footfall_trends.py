from pyspark.sql import DataFrame
from pyspark.sql import functions as F
from pyspark.sql.window import Window


REQUIRED_COLUMNS = {
    "store_id",
    "store_name",
    "hour",
    "total_gps_pings",
}


def _validate_hourly_data(hourly_footfall: DataFrame):
    """Validate the input hourly footfall DataFrame."""

    missing_columns = REQUIRED_COLUMNS - set(hourly_footfall.columns)

    if missing_columns:
        raise ValueError(
            f"Missing required columns: {sorted(missing_columns)}"
        )


def generate_hourly_footfall_trends(
    hourly_footfall: DataFrame,
) -> DataFrame:
    """Generate store-wise average and total footfall by hour of day."""

    _validate_hourly_data(hourly_footfall)

    trends = (
        hourly_footfall
        .withColumn(
            "hour_of_day",
            F.hour(F.col("hour")),
        )
        .groupBy(
            "store_id",
            "store_name",
            "hour_of_day",
        )
        .agg(
            F.sum("total_gps_pings").alias("total_gps_pings"),
            F.round(
                F.avg("total_gps_pings"),
                2,
            ).alias("avg_gps_pings"),
            F.count("*").alias("observed_hours"),
        )
        .orderBy(
            "store_id",
            "hour_of_day",
        )
    )

    return trends


def generate_daily_footfall_trends(
    hourly_footfall: DataFrame,
) -> DataFrame:
    """Generate daily store footfall totals."""

    _validate_hourly_data(hourly_footfall)

    daily_trends = (
        hourly_footfall
        .withColumn(
            "date",
            F.to_date(F.col("hour")),
        )
        .groupBy(
            "store_id",
            "store_name",
            "date",
        )
        .agg(
            F.sum("total_gps_pings").alias("total_gps_pings"),
            F.count("*").alias("active_store_hours"),
            F.round(
                F.avg("total_gps_pings"),
                2,
            ).alias("avg_pings_per_active_hour"),
        )
        .orderBy(
            "store_id",
            "date",
        )
    )

    return daily_trends


def summarize_peak_and_quiet_hours(
    hourly_trends: DataFrame,
) -> DataFrame:
    """Identify the busiest and quietest observed hours for each store."""

    required_columns = {
        "store_id",
        "store_name",
        "hour_of_day",
        "avg_gps_pings",
    }

    missing_columns = required_columns - set(hourly_trends.columns)

    if missing_columns:
        raise ValueError(
            f"Missing required columns: {sorted(missing_columns)}"
        )

    peak_window = (
        Window
        .partitionBy("store_id")
        .orderBy(
            F.desc("avg_gps_pings"),
            F.asc("hour_of_day"),
        )
    )

    quiet_window = (
        Window
        .partitionBy("store_id")
        .orderBy(
            F.asc("avg_gps_pings"),
            F.asc("hour_of_day"),
        )
    )

    peak_hours = (
        hourly_trends
        .withColumn(
            "rank",
            F.row_number().over(peak_window),
        )
        .filter(F.col("rank") == 1)
        .select(
            "store_id",
            "store_name",
            F.col("hour_of_day").alias("peak_hour"),
            F.col("avg_gps_pings").alias("peak_avg_gps_pings"),
        )
    )

    quiet_hours = (
        hourly_trends
        .withColumn(
            "rank",
            F.row_number().over(quiet_window),
        )
        .filter(F.col("rank") == 1)
        .select(
            "store_id",
            F.col("hour_of_day").alias("quiet_hour"),
            F.col("avg_gps_pings").alias("quiet_avg_gps_pings"),
        )
    )

    return (
        peak_hours
        .join(quiet_hours, on="store_id", how="inner")
        .select(
            "store_id",
            "store_name",
            "peak_hour",
            "peak_avg_gps_pings",
            "quiet_hour",
            "quiet_avg_gps_pings",
        )
        .orderBy("store_id")
    )
