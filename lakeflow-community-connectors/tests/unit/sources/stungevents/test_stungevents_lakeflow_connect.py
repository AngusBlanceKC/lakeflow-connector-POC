from databricks.labs.community_connector.sources.stungevents.stungevents import (
    StungEventsLakeflowConnect,
)
from tests.unit.sources.test_suite import LakeflowConnectTests


class TestStungEventsConnector(LakeflowConnectTests):
    connector_class = StungEventsLakeflowConnect
    simulator_source = "stungevents"
    replay_config = {"base_url": "https://api.stungevents.com"}
    sample_records = 3
