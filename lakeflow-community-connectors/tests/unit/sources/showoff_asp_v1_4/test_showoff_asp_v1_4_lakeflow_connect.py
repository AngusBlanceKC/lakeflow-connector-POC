from databricks.labs.community_connector.sources.showoff_asp_v1_4.showoff_asp_v1_4 import ShowoffAspV14LakeflowConnect


class Response:
    status_code = 200
    headers = {"Authentication-Info": "expires-in=3600"}

    def raise_for_status(self): return None
    def json(self): return [{"Uuid": "visitor-0001"}]


class TokenResponse(Response):
    def json(self): return "demo-token"


class Session:
    def __init__(self): self.headers = {}; self.calls = []
    def post(self, url, headers, timeout): self.calls.append(("post", url, headers)); return TokenResponse()
    def get(self, url, params, timeout): self.calls.append(("get", url, params)); return Response()


def test_lists_resources_and_reads_first_offset():
    item = ShowoffAspV14LakeflowConnect({"base_url": "http://example.test", "api_key": "key", "api_secret": "secret"})
    session = Session(); item._session = session
    records, offset = item.read_table("visitors", None, {"page_size": "2", "page_offset": "4"})
    assert list(records)[0]["Uuid"] == "visitor-0001"
    assert offset == {"offset": 6}
    assert session.calls[0][0] == "post"
    assert session.calls[1][1] == "http://example.test/public/visitors"
    assert session.calls[1][2] == {"O": "4", "L": "2"}


def test_rejects_unknown_table():
    try:
        ShowoffAspV14LakeflowConnect({"api_key": "key", "api_secret": "secret"}).get_table_schema("unknown", {})
    except ValueError as error:
        assert "Unsupported ShowOff table" in str(error)
    else:
        raise AssertionError("unknown tables must be rejected")
