"""LiveBuzz source connector."""

from databricks.labs.community_connector.sources.livebuzz.livebuzz import LiveBuzzLakeflowConnect
from databricks.labs.community_connector.sparkpds import LakeflowSource


class LiveBuzzDataSource(LakeflowSource):
    _lakeflow_connect_cls = LiveBuzzLakeflowConnect


__all__ = ["LiveBuzzLakeflowConnect", "LiveBuzzDataSource"]
