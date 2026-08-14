from databricks.labs.community_connector.sources.livebuzz.livebuzz import LiveBuzzLakeflowConnect


class FakeResponse:
    status_code = 200
    headers = {}

    def raise_for_status(self):
        return None

    def json(self):
        return {
            "data": [{"id": "exh-1", "updated_at": "2026-01-01T00:00:00Z"}],
            "meta": {"has_more": False},
        }


class FakeSession:
    def __init__(self):
        self.headers = {}
        self.calls = []

    def get(self, url, params, timeout):
        self.calls.append((url, params, timeout))
        return FakeResponse()


def _connector():
    return LiveBuzzLakeflowConnect(
        {"base_url": "http://example.test", "campaign": "event-1", "api_key": "key"}
    )


def test_tables_metadata_and_auth_headers():
    connector = _connector()
    assert connector.list_tables() == ["exhibitors", "speakers", "sessions", "attendees"]
    assert connector._session.headers["X-API-Key"] == "key"
    assert connector.read_table_metadata("exhibitors", {})["cursor_field"] == "updated_at"


def test_reads_campaign_resource_with_pagination_options_and_none_offset():
    connector = _connector()
    session = FakeSession()
    connector._session = session
    rows, offset = connector.read_table(
        "exhibitors", None, {"page_size": "2", "max_records_per_batch": "2"}
    )
    assert list(rows)[0]["id"] == "exh-1"
    assert offset == {"cursor": "2026-01-01T00:00:00Z"}
    assert session.calls[0] == (
        "http://example.test/campaign/event-1/api/exhibitors",
        {"limit": "2", "offset": "0"},
        20,
    )


def test_rejects_unknown_table():
    try:
        _connector().get_table_schema("unknown", {})
    except ValueError as error:
        assert "Unsupported LiveBuzz table" in str(error)
    else:
        raise AssertionError("unknown table must be rejected")
