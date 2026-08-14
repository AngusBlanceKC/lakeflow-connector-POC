"""Schemas for the LiveBuzz event API simulator and connector."""

from pyspark.sql.types import ArrayType, MapType, StringType, StructField, StructType


def _schema(fields: list[str]) -> StructType:
    return StructType([StructField(field, StringType(), True) for field in fields])


EXHIBITORS_SCHEMA = StructType(
    [
        *[
            StructField(field, StringType(), True)
            for field in [
                "id",
                "identifier",
                "companyName",
                "logo",
                "description",
                "telephone",
                "emailAddress",
                "websiteUrl",
            ]
        ],
        StructField("stands", ArrayType(StringType()), True),
        StructField("addresses", ArrayType(MapType(StringType(), StringType())), True),
        StructField("socialMediaChannels", ArrayType(MapType(StringType(), StringType())), True),
        *[StructField(field, StringType(), True) for field in ["status", "updated_at"]],
    ]
)
SPEAKERS_SCHEMA = _schema(
    [
        "id",
        "firstName",
        "lastName",
        "companyName",
        "jobTitle",
        "emailAddress",
        "biography",
        "updated_at",
    ]
)
SESSIONS_SCHEMA = StructType(
    [
        *[
            StructField(field, StringType(), True)
            for field in ["id", "title", "description", "start", "end", "location", "track"]
        ],
        StructField("speaker_ids", ArrayType(StringType()), True),
        StructField("updated_at", StringType(), True),
    ]
)
ATTENDEES_SCHEMA = _schema(
    [
        "id",
        "firstName",
        "lastName",
        "emailAddress",
        "companyName",
        "jobTitle",
        "status",
        "registered_at",
        "updated_at",
    ]
)

SUPPORTED_TABLES = ["exhibitors", "speakers", "sessions", "attendees"]
TABLE_SCHEMAS = {
    "exhibitors": EXHIBITORS_SCHEMA,
    "speakers": SPEAKERS_SCHEMA,
    "sessions": SESSIONS_SCHEMA,
    "attendees": ATTENDEES_SCHEMA,
}
TABLE_METADATA = {
    table: {"primary_keys": ["id"], "cursor_field": "updated_at", "ingestion_type": "cdc"}
    for table in SUPPORTED_TABLES
}
