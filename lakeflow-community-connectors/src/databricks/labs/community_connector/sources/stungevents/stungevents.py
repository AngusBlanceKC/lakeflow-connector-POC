"""Lakeflow connector for the public StungEvents REST API."""

from typing import Iterator

import requests
from pyspark.sql.types import StructType

from databricks.labs.community_connector.interface import LakeflowConnect
from databricks.labs.community_connector.sources.stungevents.stungevents_schemas import (
    SUPPORTED_TABLES,
    TABLE_METADATA,
    TABLE_SCHEMAS,
)


class StungEventsLakeflowConnect(LakeflowConnect):
    """Read upcoming public events from StungEvents."""

    def __init__(self, options: dict[str, str]) -> None:
        super().__init__(options)
        self.base_url = options.get("base_url", "https://api.stungevents.com").rstrip("/")
        self._session = requests.Session()
        self._session.headers.update({"Accept": "application/json"})

    def list_tables(self) -> list[str]:
        return SUPPORTED_TABLES.copy()

    def get_table_schema(self, table_name: str, table_options: dict[str, str]) -> StructType:
        self._validate_table(table_name)
        return TABLE_SCHEMAS[table_name]

    def read_table_metadata(self, table_name: str, table_options: dict[str, str]) -> dict:
        self._validate_table(table_name)
        return TABLE_METADATA[table_name].copy()

    def read_table(
        self, table_name: str, start_offset: dict, table_options: dict[str, str]
    ) -> tuple[Iterator[dict], dict]:
        """Read all matching events using the API's offset/limit pagination."""
        self._validate_table(table_name)
        if start_offset:
            # Snapshot tables do not use offsets. The framework should not ask
            # for a second microbatch, but returning the same offset is safe.
            return iter([]), start_offset

        limit = min(int(table_options.get("limit", "100")), 100)
        params = {"limit": str(limit), "offset": "0"}
        option_mapping = {
            "city": "city",
            "country": "country",
            "category": "category",
            "from_date": "from",
            "to_date": "to",
        }
        for option_name, query_name in option_mapping.items():
            if table_options.get(option_name):
                params[query_name] = table_options[option_name]

        records: list[dict] = []
        offset = 0
        while True:
            params["offset"] = str(offset)
            response = self._session.get(f"{self.base_url}/events", params=params, timeout=30)
            response.raise_for_status()
            body = response.json()
            page = body.get("events", [])
            if not isinstance(page, list):
                raise ValueError("StungEvents response field 'events' must be an array")
            records.extend(page)
            if len(page) < limit:
                break
            offset += len(page)

        return iter(records), {}

    def _validate_table(self, table_name: str) -> None:
        if table_name not in SUPPORTED_TABLES:
            raise ValueError(
                f"Unsupported table {table_name!r}; supported tables: {SUPPORTED_TABLES}"
            )
