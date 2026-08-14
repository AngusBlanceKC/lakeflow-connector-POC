from databricks.labs.community_connector.sources.fusion.fusion import FusionLakeflowConnect


class FakeResponse:
    def __init__(self, body, status_code=200):
        self._body = body
        self.status_code = status_code
        self.headers = {}

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(self.status_code)

    def json(self):
        return self._body


class FakeSession:
    def __init__(self):
        self.auth = None
        self.headers = {}
        self.calls = []

    def get(self, url, params, timeout):
        self.calls.append((url, params, timeout))
        return FakeResponse([{"Id": "person-1", "FORENAME": "Ada"}])


def _connector():
    return FusionLakeflowConnect({
        "base_url": "http://example.test",
        "event_id": "event-1",
        "username": "user",
        "password": "password",
        "install_name": "install",
        "api_key": "key",
    })


def test_lists_snapshot_tables_and_uses_all_auth_options():
    connector = _connector()
    assert connector.list_tables() == ["people", "event_tickets"]
    assert connector._session.auth == ("user", "password")
    assert connector._session.headers["X-Fusion-Install-Name"] == "install"
    assert connector._session.headers["X-Fusion-API-Key"] == "key"
    assert connector.read_table_metadata("people", {}) == {
        "primary_keys": ["Id"], "ingestion_type": "snapshot"
    }


def test_accepts_none_first_offset_and_maps_event_pagination():
    connector = _connector()
    session = FakeSession()
    connector._session = session

    records, offset = connector.read_table("people", None, {"page_size": "2", "page_offset": "4"})

    assert list(records)[0]["Id"] == "person-1"
    assert offset == {}
    assert session.calls[0][1] == {"eventId": "event-1", "limit": "2", "offset": "4"}


def test_rejects_unknown_table():
    connector = _connector()
    try:
        connector.get_table_schema("unknown", {})
    except ValueError as error:
        assert "Unsupported Fusion table" in str(error)
    else:
        raise AssertionError("unknown tables must be rejected")
