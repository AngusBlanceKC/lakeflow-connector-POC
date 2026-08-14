"""Lakeflow connector for ShowOff ASP API v1.4."""

import base64
import time
from typing import Iterator

import requests
from pyspark.sql.types import StructType

from databricks.labs.community_connector.interface.lakeflow_connect import LakeflowConnect
from databricks.labs.community_connector.sources.showoff_asp_v1_4.showoff_asp_v1_4_schemas import TABLES, TABLE_METADATA, TABLE_SCHEMAS


class ShowoffAspV14LakeflowConnect(LakeflowConnect):
    """Read paginated ShowOff collections with cached one-hour bearer tokens."""

    _MAX_ATTEMPTS = 4
    _RETRYABLE = {429, 500, 502, 503, 504}

    def __init__(self, options: dict[str, str]) -> None:
        super().__init__(options)
        self.base_url = options.get("base_url", "https://api.showoff.asp.events").rstrip("/")
        self.api_key = options["api_key"]
        self.api_secret = options["api_secret"]
        self.site_uuid = options.get("site_uuid", "")
        self._session = requests.Session()
        self._token: str | None = options.get("access_token") or None
        self._token_expiry = 0.0

    def list_tables(self) -> list[str]:
        return TABLES.copy()

    def get_table_schema(self, table_name: str, table_options: dict[str, str]) -> StructType:
        del table_options
        self._validate(table_name)
        return TABLE_SCHEMAS[table_name]

    def read_table_metadata(self, table_name: str, table_options: dict[str, str]) -> dict:
        del table_options
        self._validate(table_name)
        return TABLE_METADATA[table_name].copy()

    def read_table(self, table_name: str, start_offset: dict | None, table_options: dict[str, str]) -> tuple[Iterator[dict], dict]:
        self._validate(table_name)
        del start_offset
        limit = min(max(int(table_options.get("page_size", "100")), 1), 1000)
        offset = max(int(table_options.get("page_offset", "0")), 0)
        params = {"O": str(offset), "L": str(limit)}
        site = table_options.get("site_uuid", self.site_uuid)
        if site: params["SiteUuid"] = site
        if table_options.get("query"): params["Q"] = table_options["query"]
        self._ensure_token()
        return iter(self._get(table_name, params)), {"offset": offset + limit}

    def _ensure_token(self) -> None:
        if self._token and time.time() < self._token_expiry - 30: return
        raw = base64.b64encode(f"{self.api_key}:{self.api_secret}".encode()).decode()
        response = self._session.post(f"{self.base_url}/public/token", headers={"Authorization": f"Basic {raw}"}, timeout=30)
        response.raise_for_status()
        token = response.json()
        self._token = token if isinstance(token, str) else token["access_token"]
        self._token_expiry = time.time() + int(response.headers.get("Authentication-Info", "expires-in=3600").split("=")[-1])
        self._session.headers["Authorization"] = f"Bearer {self._token}"

    def _get(self, table_name: str, params: dict[str, str]) -> list[dict]:
        last_error: Exception | None = None
        for attempt in range(self._MAX_ATTEMPTS):
            try:
                response = self._session.get(f"{self.base_url}/public/{table_name}", params=params, timeout=30)
                if response.status_code not in self._RETRYABLE:
                    response.raise_for_status()
                    body = response.json()
                    if not isinstance(body, list): raise ValueError("ShowOff collection response must be an array")
                    return body
                last_error = requests.HTTPError(f"ShowOff returned HTTP {response.status_code}")
                delay = min(float(response.headers.get("Retry-After", 2**attempt)), 60.0)
            except (requests.RequestException, ValueError) as error:
                last_error = error; delay = 2**attempt
            if attempt < self._MAX_ATTEMPTS - 1: time.sleep(delay)
        raise RuntimeError(f"ShowOff API unavailable after {self._MAX_ATTEMPTS} attempts: {last_error}") from last_error

    @staticmethod
    def _validate(table_name: str) -> None:
        if table_name not in TABLES: raise ValueError(f"Unsupported ShowOff table {table_name!r}; supported: {TABLES}")
