"""Lakeflow connector for the private Fusion (formerly Circdata) API."""

import time
from typing import Iterator

import requests
from pyspark.sql.types import StructType

from databricks.labs.community_connector.interface.lakeflow_connect import LakeflowConnect
from databricks.labs.community_connector.sources.fusion.fusion_schemas import (
    SUPPORTED_TABLES,
    TABLE_METADATA,
    TABLE_SCHEMAS,
)


class FusionLakeflowConnect(LakeflowConnect):
    """Read Fusion event people and ticket snapshots."""

    _MAX_ATTEMPTS = 4
    _RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}
    _MAX_PAGE_SIZE = 500

    def __init__(self, options: dict[str, str]) -> None:
        super().__init__(options)
        self.base_url = options.get("base_url", "https://developers.gofusion.com").rstrip("/")
        self.event_id = options["event_id"]
        self.username = options["username"]
        self.password = options["password"]
        self.install_name = options["install_name"]
        self.api_key = options["api_key"]
        self._session = requests.Session()
        self._session.headers.update({
            "Accept": "application/json",
            "X-Fusion-Install-Name": self.install_name,
            "X-Fusion-API-Key": self.api_key,
        })
        self._session.auth = (self.username, self.password)

    def list_tables(self) -> list[str]:
        return SUPPORTED_TABLES.copy()

    def get_table_schema(self, table_name: str, table_options: dict[str, str]) -> StructType:
        del table_options
        self._validate_table(table_name)
        return TABLE_SCHEMAS[table_name]

    def read_table_metadata(self, table_name: str, table_options: dict[str, str]) -> dict:
        del table_options
        self._validate_table(table_name)
        return TABLE_METADATA[table_name].copy()

    def read_table(
        self, table_name: str, start_offset: dict | None, table_options: dict[str, str]
    ) -> tuple[Iterator[dict], dict]:
        self._validate_table(table_name)
        del start_offset
        page_size = min(max(int(table_options.get("page_size", "100")), 1), self._MAX_PAGE_SIZE)
        offset = max(int(table_options.get("page_offset", "0")), 0)
        params = {
            "eventId": self.event_id,
            "limit": str(page_size),
            "offset": str(offset),
        }
        rows = self._get_page(table_name, params)
        return iter(rows), {}

    def _get_page(self, table_name: str, params: dict[str, str]) -> list[dict]:
        path = "People" if table_name == "people" else "VisitorIntegrationApi/api/EventTicket"
        last_error: Exception | None = None
        for attempt in range(self._MAX_ATTEMPTS):
            try:
                response = self._session.get(f"{self.base_url}/{path}", params=params, timeout=30)
                if response.status_code not in self._RETRYABLE_STATUS_CODES:
                    response.raise_for_status()
                    body = response.json()
                    if isinstance(body, dict):
                        body = body.get("items", body.get("data", body))
                    if not isinstance(body, list):
                        raise ValueError(f"Fusion response for {table_name!r} must be an array or items envelope")
                    return body
                last_error = requests.HTTPError(f"Fusion returned HTTP {response.status_code}")
                retry_after = response.headers.get("Retry-After")
                delay = min(float(retry_after), 60.0) if retry_after else 2**attempt
            except (requests.RequestException, ValueError) as error:
                last_error = error
                delay = 2**attempt
            if attempt < self._MAX_ATTEMPTS - 1:
                time.sleep(delay)
        raise RuntimeError(f"Fusion API unavailable after {self._MAX_ATTEMPTS} attempts: {last_error}") from last_error

    @staticmethod
    def _validate_table(table_name: str) -> None:
        if table_name not in SUPPORTED_TABLES:
            raise ValueError(f"Unsupported Fusion table {table_name!r}; supported: {SUPPORTED_TABLES}")
