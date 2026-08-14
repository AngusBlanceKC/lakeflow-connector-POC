"""Lakeflow connector for the LiveBuzz event JSON API."""

from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import Iterator

import requests
from pyspark.sql.types import StructType

from databricks.labs.community_connector.interface.lakeflow_connect import LakeflowConnect
from databricks.labs.community_connector.sources.livebuzz.livebuzz_schemas import (
    SUPPORTED_TABLES,
    TABLE_METADATA,
    TABLE_SCHEMAS,
)


class LiveBuzzLakeflowConnect(LakeflowConnect):
    _RETRYABLE = {429, 500, 502, 503, 504}

    def __init__(self, options: dict[str, str]) -> None:
        super().__init__(options)
        self.base_url = options["base_url"].rstrip("/")
        self.campaign = options["campaign"]
        self.api_key = options.get("api_key", "")
        self.bearer = options.get("bearer", "")
        self._session = requests.Session()
        self._session.headers.update({"Accept": "application/json", "X-API-Key": self.api_key})
        if self.bearer:
            self._session.headers["Authorization"] = f"Bearer {self.bearer}"
        self._init_ts = datetime.now(timezone.utc)

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
        start_offset = start_offset or {}
        cursor = start_offset.get("cursor")
        if cursor and cursor >= self._init_ts.isoformat().replace("+00:00", "Z"):
            return iter([]), start_offset
        limit = min(max(int(table_options.get("page_size", "100")), 1), 100)
        max_records = max(1, int(table_options.get("max_records_per_batch", "1000")))
        rows: list[dict] = []
        offset = 0
        while len(rows) < max_records:
            params = {"limit": str(min(limit, max_records - len(rows))), "offset": str(offset)}
            if cursor:
                params["since"] = cursor
            body = self._get(table_name, params)
            page = body.get("data", body) if isinstance(body, dict) else body
            if not isinstance(page, list) or not page:
                break
            rows.extend(page)
            offset += len(page)
            if not isinstance(body, dict) or not body.get("meta", {}).get("has_more", False):
                break
        rows = rows[:max_records]
        end_cursor = max(
            (row.get("updated_at", cursor or "") for row in rows), default=cursor or ""
        )
        return iter(rows), {"cursor": end_cursor} if end_cursor else start_offset

    def _get(self, table_name: str, params: dict[str, str]) -> dict:
        last_error: Exception | None = None
        url = f"{self.base_url}/campaign/{self.campaign}/api/{table_name}"
        for attempt in range(4):
            try:
                response = self._session.get(url, params=params, timeout=20)
                if response.status_code not in self._RETRYABLE:
                    response.raise_for_status()
                    payload = response.json()
                    if not isinstance(payload, (dict, list)):
                        raise ValueError("LiveBuzz response must be an object or array")
                    return payload if isinstance(payload, dict) else {"data": payload}
                last_error = requests.HTTPError(f"LiveBuzz returned HTTP {response.status_code}")
                delay = min(float(response.headers.get("Retry-After", 2**attempt)), 60.0)
            except (requests.RequestException, ValueError) as error:
                last_error = error
                delay = 2**attempt
            if attempt < 3:
                time.sleep(delay)
        raise RuntimeError(f"LiveBuzz API unavailable after retries: {last_error}") from last_error

    @staticmethod
    def _validate_table(table_name: str) -> None:
        if table_name not in SUPPORTED_TABLES:
            raise ValueError(
                f"Unsupported LiveBuzz table {table_name!r}; supported: {SUPPORTED_TABLES}"
            )
