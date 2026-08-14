"""Schemas and metadata for the GEVME attendee API."""

from pyspark.sql.types import BooleanType, StringType, StructField, StructType


ATTENDEE_SCHEMA = StructType([
    StructField("id", StringType(), False),
    StructField("event_id", StringType(), True),
    StructField("email", StringType(), True),
    StructField("first_name", StringType(), True),
    StructField("last_name", StringType(), True),
    StructField("full_name", StringType(), True),
    StructField("company", StringType(), True),
    StructField("job_title", StringType(), True),
    StructField("country", StringType(), True),
    StructField("status", StringType(), True),
    StructField("checked_in", BooleanType(), True),
    StructField("created_at", StringType(), True),
    StructField("updated_at", StringType(), True),
    StructField("generated", BooleanType(), True),
])

SUPPORTED_TABLES = ["attendees"]
TABLE_SCHEMAS = {"attendees": ATTENDEE_SCHEMA}
TABLE_METADATA = {"attendees": {"primary_keys": ["id"], "ingestion_type": "snapshot"}}
