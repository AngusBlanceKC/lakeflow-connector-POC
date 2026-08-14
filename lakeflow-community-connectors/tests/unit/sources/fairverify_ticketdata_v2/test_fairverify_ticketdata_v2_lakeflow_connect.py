from databricks.labs.community_connector.sources.fairverify_ticketdata_v2.fairverify_ticketdata_v2 import FairverifyTicketdataV2LakeflowConnect


class Response:
    status_code = 200
    headers = {}

    def raise_for_status(self):
        return None

    def json(self):
        return [{"ticket_id": "fv-ticket-00001"}]


class Session:
    def __init__(self):
        self.headers = {"X-FairVerify-API-Key": "key"}
        self.calls = []

    def get(self, url, params, timeout):
        self.calls.append((url, params, timeout))
        return Response()


def connector():
    return FairverifyTicketdataV2LakeflowConnect({"base_url": "http://example.test", "event_id": "event-1", "api_key": "key"})


def test_lists_tables_and_reads_first_offset():
    item = connector()
    item._session = Session()
    records, offset = item.read_table("tickets", None, {"page_size": "2", "page_offset": "4"})
    assert list(records)[0]["ticket_id"] == "fv-ticket-00001"
    assert offset == {}
    assert item._session.headers["X-FairVerify-API-Key"] == "key"


def test_maps_event_ticket_path_and_query():
    item = connector()
    session = Session()
    item._session = session
    item.read_table("tickets", None, {"page_size": "2", "page_offset": "4", "status": "valid"})
    assert session.calls[0][0] == "http://example.test/api/v2/events/event-1/tickets"
    assert session.calls[0][1] == {"limit": "2", "offset": "4", "status": "valid"}


def test_rejects_unknown_table():
    try:
        connector().get_table_schema("unknown", {})
    except ValueError as error:
        assert "Unsupported FairVerify table" in str(error)
    else:
        raise AssertionError("unknown tables must be rejected")
