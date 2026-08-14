"""Lakeflow connector for the inferred FairVerify Ticketdata v2 contract."""

import time
from typing import Iterator

import requests
from pyspark.sql.types import StructType

from databricks.labs.community_connector.interface.lakeflow_connect import LakeflowConnect
from databricks.labs.community_connector.sources.fairverify_ticketdata_v2.fairverify_ticketdata_v2_schemas import SUPPORTED_TABLES, TABLE_METADATA, TABLE_SCHEMAS


class FairverifyTicketdataV2LakeflowConnect(LakeflowConnect):
    """Read FairVerify event and ticket snapshots."""

    _MAX_ATTEMPTS = 4
    _RETRYABLE = {429, 500, 502, 503, 504}

    def __init__(self, options: dict[str, str]) -> None:
        super().__init__(options)
        self.base_url = options.get("base_url", "https://api.fairverify.de").rstrip("/")
        self.event_id = options["event_id"]
        self.api_key = options.get("api_key", "")
        self.access_token = options.get("access_token", "")
        self._session = requests.Session()
        self._session.headers.update({"Accept": "application/json"})
        if self.api_key:
            self._session.headers["X-FairVerify-API-Key"] = self.api_key
        if self.access_token:
            self._session.headers["Authorization"] = f"Bearer {self.access_token}"

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
        limit = min(max(int(table_options.get("page_size", "100")), 1), 1000)
        offset = max(int(table_options.get("page_offset", "0")), 0)
        params = {"limit": str(limit), "offset": str(offset)}
        if table_name == "tickets":
            path = f"/api/v2/events/{self.event_id}/tickets"
            if table_options.get("status"):
                params["status"] = table_options["status"]
            if table_options.get("email"):
                params["email"] = table_options["email"]
        else:
            path = "/api/v2/events"
        return iter(self._get(path, params)), {}

    def _get(self, path: str, params: dict[str, str]) -> list[dict]:
        last_error: Exception | None = None
        for attempt in range(self._MAX_ATTEMPTS):
            try:
                response = self._session.get(f"{self.base_url}{path}", params=params, timeout=30)
                if response.status_code not in self._RETRYABLE:
                    response.raise_for_status()
                    body = response.json()
                    if isinstance(body, dict):
                        body = body.get("items", body.get("data", body))
                    if not isinstance(body, list):
                        raise ValueError("FairVerify response must be a list or items/data envelope")
                    return body
                last_error = requests.HTTPError(f"FairVerify returned HTTP {response.status_code}")
                delay = min(float(response.headers.get("Retry-After", 2**attempt)), 60.0)
            except (requests.RequestException, ValueError) as error:
                last_error = error
                delay = 2**attempt
            if attempt < self._MAX_ATTEMPTS - 1:
                time.sleep(delay)
        raise RuntimeError(f"FairVerify API unavailable after {self._MAX_ATTEMPTS} attempts: {last_error}") from last_error

    @staticmethod
    def _validate_table(table_name: str) -> None:
        if table_name not in SUPPORTED_TABLES:
            raise ValueError(f"Unsupported FairVerify table {table_name!r}; supported: {SUPPORTED_TABLES}")
