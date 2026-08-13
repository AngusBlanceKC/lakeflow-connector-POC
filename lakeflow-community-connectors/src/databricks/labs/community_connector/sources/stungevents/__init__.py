"""StungEvents source connector."""

from databricks.labs.community_connector.sources.stungevents.stungevents import (
    StungEventsLakeflowConnect,
)
from databricks.labs.community_connector.sparkpds import LakeflowSource


class StungEventsDataSource(LakeflowSource):
    _lakeflow_connect_cls = StungEventsLakeflowConnect


__all__ = ["StungEventsLakeflowConnect", "StungEventsDataSource"]
