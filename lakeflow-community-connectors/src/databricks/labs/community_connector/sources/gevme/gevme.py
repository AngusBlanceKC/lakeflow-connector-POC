"""Lakeflow connector for GEVME Registration API v2 attendees."""

import time
from typing import Iterator

import requests
from pyspark.sql.types import StructType

from databricks.labs.community_connector.interface.lakeflow_connect import LakeflowConnect
from databricks.labs.community_connector.sources.gevme.gevme_schemas import (
    SUPPORTED_TABLES,
    TABLE_METADATA,
    TABLE_SCHEMAS,
)


class GevmeLakeflowConnect(LakeflowConnect):
    """Read a snapshot of attendees from a GEVME event."""

    _MAX_ATTEMPTS = 4
    _RETRYABLE = {429, 500, 502, 503, 504}

    def __init__(self, options: dict[str, str]) -> None:
        super().__init__(options)
        self.base_url = options.get("base_url", "https://www.gevme.com").rstrip("/")
        self.event_id = options["event_id"]
        self.access_token = options.get("access_token", "")
        self.client_id = options.get("client_id", "")
        self.client_secret = options.get("client_secret", "")
        self._session = requests.Session()
        self._session.headers.update({"Accept": "application/json"})

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

    def read_table(self, table_name: str, start_offset: dict | None, table_options: dict[str, str]) -> tuple[Iterator[dict], dict]:
        self._validate_table(table_name)
        del start_offset
        self._ensure_token()
        limit = min(max(int(table_options.get("page_size", "1000")), 1), 1000)
        offset = max(int(table_options.get("page_offset", "0")), 0)
        rows = self._get_page(limit, offset, table_options)
        return iter(rows), {}

    def _ensure_token(self) -> None:
        if self.access_token:
            self._session.headers["Authorization"] = f"Bearer {self.access_token}"
            return
        if not self.client_id or not self.client_secret:
            raise ValueError("GEVME requires access_token or client_id/client_secret")
        response = self._session.post(
            f"{self.base_url}/apiv2/api/oauth/access_token",
            data={"grant_type": "client_credentials", "client_id": self.client_id, "client_secret": self.client_secret, "scope": "root"},
            timeout=30,
        )
        response.raise_for_status()
        self._session.headers["Authorization"] = f"Bearer {response.json()['access_token']}"

    def _get_page(self, limit: int, offset: int, options: dict[str, str]) -> list[dict]:
        params = {"limit": str(limit), "offset": str(offset)}
        if options.get("modified_from"):
            params["modifiedFrom"] = options["modified_from"]
        if options.get("where_email"):
            params["where[email]"] = options["where_email"]
        last_error: Exception | None = None
        for attempt in range(self._MAX_ATTEMPTS):
            try:
                response = self._session.get(
                    f"{self.base_url}/apiv2/api/events/{self.event_id}/attendees",
                    params=params,
                    timeout=30,
                )
                if response.status_code not in self._RETRYABLE:
                    response.raise_for_status()
                    body = response.json()
                    if isinstance(body, dict):
                        body = body.get("items", body.get("data", body))
                    if not isinstance(body, list):
                        raise ValueError("GEVME attendees response must be an array or items envelope")
                    return body
                last_error = requests.HTTPError(f"GEVME returned HTTP {response.status_code}")
                delay = min(float(response.headers.get("Retry-After", 2**attempt)), 60.0)
            except (requests.RequestException, ValueError, KeyError) as error:
                last_error = error
                delay = 2**attempt
            if attempt < self._MAX_ATTEMPTS - 1:
                time.sleep(delay)
        raise RuntimeError(f"GEVME API unavailable after {self._MAX_ATTEMPTS} attempts: {last_error}") from last_error

    @staticmethod
    def _validate_table(table_name: str) -> None:
        if table_name not in SUPPORTED_TABLES:
            raise ValueError(f"Unsupported GEVME table {table_name!r}; supported: {SUPPORTED_TABLES}")
