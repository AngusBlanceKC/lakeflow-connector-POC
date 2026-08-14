"""Visit Create JSON API v2 source connector."""

from databricks.labs.community_connector.sources.visit_create_v2.visit_create_v2 import (
    VisitCreateV2LakeflowConnect,
)
from databricks.labs.community_connector.sparkpds import LakeflowSource


class VisitCreateV2DataSource(LakeflowSource):
    _lakeflow_connect_cls = VisitCreateV2LakeflowConnect


__all__ = ["VisitCreateV2LakeflowConnect", "VisitCreateV2DataSource"]
