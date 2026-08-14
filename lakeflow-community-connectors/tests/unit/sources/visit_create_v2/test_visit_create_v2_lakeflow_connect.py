from databricks.labs.community_connector.sources.visit_create_v2.visit_create_v2 import (
    VisitCreateV2LakeflowConnect,
)


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
        if len(self.calls) == 1:
            return FakeResponse([
                {"id": "visitor-1", "revision": 10, "firstName": "Ada"},
                {"id": "visitor-2", "revision": 11, "firstName": "Alan"},
            ])
        return FakeResponse([])


def test_reads_revision_pages_and_uses_basic_auth():
    connector = VisitCreateV2LakeflowConnect(
        {"base_url": "http://example.test/create/v2", "api_key": "secret", "expo_id": "expo-1"}
    )
    connector._session = FakeSession()

    records, offset = connector.read_table("visitors", {}, {"limit": "2"})

    assert [record["id"] for record in records] == ["visitor-1", "visitor-2"]
    assert offset == {"revision": 12}
    assert connector.list_tables()[0] == "expos"


def test_accepts_none_on_first_framework_read():
    connector = VisitCreateV2LakeflowConnect({"expo_id": "expo-1"})
    connector._session = FakeSession()

    records, offset = connector.read_table("expos", None, {})

    assert list(records)[0]["id"] == "visitor-1"
    assert offset == {"revision": 12}


def test_resumes_from_offset_and_maps_filters():
    connector = VisitCreateV2LakeflowConnect({"expo_id": "expo-1"})
    session = FakeSession()
    connector._session = session

    connector.read_table(
        "visitors",
        {"revision": 40},
        {"registration_states": "registered,pending", "show_deleted": "false"},
    )

    params = session.calls[0][1]
    assert params["fromRevision"] == "40"
    assert params["showDeleted"] == "false"
    assert params["registrationStates"] == "registered,pending"
