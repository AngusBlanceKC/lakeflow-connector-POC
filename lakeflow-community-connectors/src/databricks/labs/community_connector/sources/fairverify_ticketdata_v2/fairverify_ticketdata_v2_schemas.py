"""Schemas for the FairVerify Ticketdata v2 simulator contract."""

from pyspark.sql.types import BooleanType, DoubleType, MapType, StringType, StructField, StructType

TICKET_SCHEMA = StructType([
    StructField("ticket_id", StringType(), False), StructField("event_id", StringType(), True),
    StructField("barcode", StringType(), True), StructField("ticket_type", StringType(), True),
    StructField("status", StringType(), True), StructField("first_name", StringType(), True),
    StructField("last_name", StringType(), True), StructField("email", StringType(), True),
    StructField("company", StringType(), True), StructField("price", DoubleType(), True),
    StructField("currency", StringType(), True), StructField("checked_in", BooleanType(), True),
    StructField("issued_at", StringType(), True), StructField("updated_at", StringType(), True),
    StructField("custom_fields", MapType(StringType(), StringType()), True), StructField("generated", BooleanType(), True),
])
EVENT_SCHEMA = StructType([
    StructField("event_id", StringType(), False), StructField("name", StringType(), True),
    StructField("status", StringType(), True), StructField("currency", StringType(), True),
])
SUPPORTED_TABLES = ["tickets", "events"]
TABLE_SCHEMAS = {"tickets": TICKET_SCHEMA, "events": EVENT_SCHEMA}
TABLE_METADATA = {table: {"primary_keys": ["ticket_id" if table == "tickets" else "event_id"], "ingestion_type": "snapshot"} for table in SUPPORTED_TABLES}
