from databricks.labs.community_connector.sources.gevme.gevme import GevmeLakeflowConnect


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
        self.headers = {}
        self.calls = []

    def get(self, url, params, timeout):
        self.calls.append((url, params, timeout))
        return FakeResponse([{"id": "attendee-1", "email": "ada@example.test"}])


def _connector():
    return GevmeLakeflowConnect({"base_url": "http://example.test", "event_id": "event-1", "access_token": "token"})


def test_lists_snapshot_table_and_bearer_auth():
    connector = _connector()
    connector._session = FakeSession()
    assert connector.list_tables() == ["attendees"]
    records, offset = connector.read_table("attendees", None, {"page_size": "2", "page_offset": "4"})
    assert list(records)[0]["id"] == "attendee-1"
    assert offset == {}
    assert connector._session.headers["Authorization"] == "Bearer token"


def test_maps_event_path_and_pagination():
    connector = _connector()
    session = FakeSession()
    connector._session = session
    connector.read_table("attendees", None, {"page_size": "2", "page_offset": "4"})
    assert session.calls[0][0] == "http://example.test/apiv2/api/events/event-1/attendees"
    assert session.calls[0][1] == {"limit": "2", "offset": "4"}


def test_rejects_unknown_table():
    try:
        _connector().get_table_schema("unknown", {})
    except ValueError as error:
        assert "Unsupported GEVME table" in str(error)
    else:
        raise AssertionError("unknown tables must be rejected")
