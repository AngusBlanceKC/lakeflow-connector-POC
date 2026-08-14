"""Schemas and metadata for the private Fusion/Circdata API."""

from pyspark.sql.types import LongType, MapType, StringType, StructField, StructType


PEOPLE_FIELDS = [
    "Id", "TITLE", "FORENAME", "SURNAME", "EMAIL", "TEL", "MOBILE", "FAX",
    "COMPANY", "JOBTITLE", "ADDR1", "ADDR2", "ADDR3", "TOWN", "COUNTY",
    "POSTCODE", "COUNTRY", "STATUS", "BADGETYPE", "CURRENCY", "ATTENDED", "BADGEID",
]

PEOPLE_SCHEMA = StructType([StructField(field, StringType(), True) for field in PEOPLE_FIELDS])
EVENT_TICKETS_SCHEMA = StructType([
    StructField("Id", StringType(), False),
    StructField("PersonId", StringType(), True),
    StructField("EventId", StringType(), True),
    StructField("TicketType", StringType(), True),
    StructField("Status", StringType(), True),
    StructField("RegisteredAt", StringType(), True),
    StructField("UpdatedAt", StringType(), True),
    StructField("CustomFields", MapType(StringType(), StringType()), True),
])

SUPPORTED_TABLES = ["people", "event_tickets"]
TABLE_SCHEMAS = {"people": PEOPLE_SCHEMA, "event_tickets": EVENT_TICKETS_SCHEMA}
TABLE_METADATA = {
    table: {"primary_keys": ["Id"], "ingestion_type": "snapshot"}
    for table in SUPPORTED_TABLES
}
