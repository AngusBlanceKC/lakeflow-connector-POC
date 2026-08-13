"""Spark schema and metadata for the public StungEvents API."""

from pyspark.sql.types import (
    BooleanType,
    DoubleType,
    LongType,
    StringType,
    StructField,
    StructType,
)

EVENTS_SCHEMA = StructType(
    [
        StructField("id", StringType(), False),
        StructField("title", StringType(), True),
        StructField("slug", StringType(), True),
        StructField("description", StringType(), True),
        StructField("start_utc", StringType(), True),
        StructField("end_utc", StringType(), True),
        StructField("timezone", StringType(), True),
        StructField("status", StringType(), True),
        StructField("attendance_mode", StringType(), True),
        StructField("category", StringType(), True),
        StructField("subcategory", StringType(), True),
        StructField("venue_id", StringType(), True),
        StructField("venue_name", StringType(), True),
        StructField("city", StringType(), True),
        StructField("country", StringType(), True),
        StructField("latitude", DoubleType(), True),
        StructField("longitude", DoubleType(), True),
        StructField("ticket_url", StringType(), True),
        StructField("ticket_availability", StringType(), True),
        StructField("ticket_currency", StringType(), True),
        StructField("ticket_price_min", DoubleType(), True),
        StructField("ticket_price_max", DoubleType(), True),
        StructField("image_url", StringType(), True),
        StructField("stream_url", StringType(), True),
        StructField("is_featured", BooleanType(), True),
        StructField("is_sponsored", BooleanType(), True),
        StructField("source_id", StringType(), True),
        StructField("source_event_id", StringType(), True),
        StructField("created_at", StringType(), True),
        StructField("updated_at", StringType(), True),
        StructField("expires_at", StringType(), True),
        StructField("demand_score", DoubleType(), True),
        StructField("view_count", LongType(), True),
        StructField("viewer_count", LongType(), True),
        StructField("duplicate_of", StringType(), True),
        StructField("duplicate_score", DoubleType(), True),
        StructField("affiliate_source", StringType(), True),
        StructField("tournament_name", StringType(), True),
        StructField("esports_game", StringType(), True),
        StructField("prize_pool_usd", DoubleType(), True),
    ]
)

TABLE_SCHEMAS = {"events": EVENTS_SCHEMA}
SUPPORTED_TABLES = ["events"]
TABLE_METADATA = {
    "events": {
        "primary_keys": ["id"],
        "cursor_field": None,
        "ingestion_type": "snapshot",
    }
}
