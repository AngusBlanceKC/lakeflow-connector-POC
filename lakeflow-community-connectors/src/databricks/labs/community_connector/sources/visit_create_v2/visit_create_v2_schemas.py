"""Spark schemas and metadata for Visit Create JSON API v2."""

from pyspark.sql.types import BooleanType, DoubleType, LongType, StringType, StructField, StructType


def _schema(*fields: tuple[str, object, bool]) -> StructType:
    return StructType([StructField(name, data_type, nullable) for name, data_type, nullable in fields])


COMMON = (
    ("id", StringType(), False),
    ("revision", LongType(), True),
    ("deleted", BooleanType(), True),
)

RESOURCE_FIELDS = {
    "expos": (("name", StringType(), True), ("reference", StringType(), True), ("status", StringType(), True)),
    "visitors": (
        ("firstName", StringType(), True),
        ("lastName", StringType(), True),
        ("email", StringType(), True),
        ("registrationState", StringType(), True),
        ("contactReference", StringType(), True),
        ("partnerReference", StringType(), True),
    ),
    "partners": (("name", StringType(), True), ("contactReference", StringType(), True)),
    "participants": (("visitorId", StringType(), True), ("showNoShow", StringType(), True), ("checkIn", StringType(), True)),
    "contents": (("title", StringType(), True), ("contentType", StringType(), True), ("body", StringType(), True)),
    "licenses": (("type", StringType(), True), ("status", StringType(), True)),
    "payments": (("visitorId", StringType(), True), ("amount", DoubleType(), True), ("state", StringType(), True)),
    "actions": (("visitorId", StringType(), True), ("type", StringType(), True), ("occurredAt", StringType(), True)),
    "connections": (("visitorId", StringType(), True), ("partnerId", StringType(), True), ("createdAt", StringType(), True)),
    "activities": (("name", StringType(), True), ("start", StringType(), True), ("location", StringType(), True)),
    "touchpoints": (("name", StringType(), True), ("contentId", StringType(), True)),
    "orders": (("visitorId", StringType(), True), ("partnerId", StringType(), True), ("state", StringType(), True), ("total", DoubleType(), True)),
    "questions": (("label", StringType(), True), ("type", StringType(), True)),
    "registrationTypes": (("name", StringType(), True),),
    "registrationForms": (("name", StringType(), True),),
}

SUPPORTED_TABLES = ["expos", *RESOURCE_FIELDS.keys(), "webhooks"]
TABLE_SCHEMAS = {
    resource: _schema(*COMMON, *fields) for resource, fields in RESOURCE_FIELDS.items()
}
TABLE_SCHEMAS["webhooks"] = _schema(
    ("id", StringType(), False),
    ("currentRevision", LongType(), True),
    ("lastRevision", LongType(), True),
    ("errorCount", LongType(), True),
    ("sentTime", StringType(), True),
    ("state", StringType(), True),
    ("enabled", BooleanType(), True),
    ("type", StringType(), True),
    ("url", StringType(), True),
)
TABLE_METADATA = {
    table: {"primary_keys": ["id"], "cursor_field": "revision", "ingestion_type": "incremental"}
    for table in SUPPORTED_TABLES
}
TABLE_METADATA["webhooks"]["cursor_field"] = None
