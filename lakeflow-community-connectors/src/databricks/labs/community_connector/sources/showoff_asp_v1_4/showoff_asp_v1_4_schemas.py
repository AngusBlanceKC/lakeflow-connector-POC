"""Schemas for core ShowOff v1.4 resources."""

from pyspark.sql.types import BooleanType, StringType, StructField, StructType

FIELDS = ["Uuid", "SiteUuid", "Name", "Slug", "Code", "FirstName", "LastName", "Email", "Company", "JobTitle", "Status", "isActive", "isPublished", "Start", "End", "Generated"]
SCHEMA = StructType([StructField(field, BooleanType() if field in {"isActive", "isPublished", "Generated"} else StringType(), True) for field in FIELDS])
TABLES = ["visitors", "exhibitors", "seminars", "sessions", "speakers", "sites", "products"]
TABLE_SCHEMAS = {table: SCHEMA for table in TABLES}
TABLE_METADATA = {table: {"primary_keys": ["Uuid"], "ingestion_type": "snapshot"} for table in TABLES}
