"""Lakeflow connector for the Visit Create JSON API v2."""

import time
from typing import Iterator

import requests
from pyspark.sql.types import StructType

from databricks.labs.community_connector.interface import LakeflowConnect
from databricks.labs.community_connector.sources.visit_create_v2.visit_create_v2_schemas import (
    SUPPORTED_TABLES,
    TABLE_METADATA,
    TABLE_SCHEMAS,
)


class VisitCreateV2LakeflowConnect(LakeflowConnect):
    """Read Visit Create resources using revision-based incremental pagination."""

    _MAX_REQUEST_ATTEMPTS = 4
    _RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}
    _MAX_PAGE_SIZE = 100

    def __init__(self, options: dict[str, str]) -> None:
        super().__init__(options)
        self.base_url = options.get("base_url", "http://127.0.0.1:8000/create/v2").rstrip("/")
        self.api_key = options.get("api_key", "demo-api-key")
        self.expo_id = options.get("expo_id", "0rwwipz7fufs1")
        self._session = requests.Session()
        self._session.auth = (self.api_key, "")
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

    def read_table(
        self, table_name: str, start_offset: dict, table_options: dict[str, str]
    ) -> tuple[Iterator[dict], dict]:
        self._validate_table(table_name)
        limit = min(max(int(table_options.get("limit", "100")), 1), self._MAX_PAGE_SIZE)
        from_revision = int(start_offset.get("revision", table_options.get("from_revision", "0")))
        params = {"limit": str(limit), "fromRevision": str(from_revision)}
        if table_name != "expos":
            params["showDeleted"] = table_options.get("show_deleted", "true").lower()
        for option_name in ("webhook_id", "contact_reference", "contact_id", "registration_states"):
            if table_options.get(option_name):
                params[self._query_name(option_name)] = table_options[option_name]

        records: list[dict] = []
        next_revision = from_revision
        while True:
            page = self._get_page(table_name, params)
            if not page:
                break
            records.extend(page)
            revisions = [int(row["revision"]) for row in page if row.get("revision") is not None]
            if revisions:
                page_revision = max(revisions)
                if page_revision <= next_revision:
                    break
                next_revision = page_revision
            if len(page) < limit:
                break
            params["fromRevision"] = str(next_revision + 1)

        # fromRevision is inclusive, so advance beyond the highest row returned
        # to avoid replaying that row in the next batch.
        offset = {"revision": next_revision + 1} if records and table_name != "webhooks" else {}
        return iter(records), offset

    def _get_page(self, table_name: str, params: dict[str, str]) -> list[dict]:
        last_error: Exception | None = None
        path = "expos" if table_name == "expos" else f"{table_name}/{self.expo_id}"
        for attempt in range(self._MAX_REQUEST_ATTEMPTS):
            try:
                response = self._session.get(f"{self.base_url}/{path}", params=params, timeout=30)
                if response.status_code not in self._RETRYABLE_STATUS_CODES:
                    response.raise_for_status()
                    body = response.json()
                    if not isinstance(body, list):
                        raise ValueError(f"Visit Create response for {table_name!r} must be an array")
                    return body
                last_error = requests.HTTPError(
                    f"Visit Create returned HTTP {response.status_code} for {table_name}"
                )
                retry_after = response.headers.get("Retry-After")
                delay = min(float(retry_after), 60.0) if retry_after else 2**attempt
            except (requests.RequestException, ValueError) as error:
                last_error = error
                delay = 2**attempt
            if attempt < self._MAX_REQUEST_ATTEMPTS - 1:
                time.sleep(delay)
        raise RuntimeError(
            f"Visit Create API remained unavailable after {self._MAX_REQUEST_ATTEMPTS} attempts "
            f"for table {table_name!r}. Last error: {last_error}"
        ) from last_error

    @staticmethod
    def _query_name(option_name: str) -> str:
        return {
            "webhook_id": "webhookId",
            "contact_reference": "contactReference",
            "contact_id": "contactId",
            "registration_states": "registrationStates",
        }[option_name]

    @staticmethod
    def _validate_table(table_name: str) -> None:
        if table_name not in SUPPORTED_TABLES:
            raise ValueError(f"Unsupported table {table_name!r}; supported tables: {SUPPORTED_TABLES}")
