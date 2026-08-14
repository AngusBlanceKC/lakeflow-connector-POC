"""Fusion/Circdata source connector."""

from databricks.labs.community_connector.sources.fusion.fusion import FusionLakeflowConnect
from databricks.labs.community_connector.sparkpds import LakeflowSource


class FusionDataSource(LakeflowSource):
    _lakeflow_connect_cls = FusionLakeflowConnect


__all__ = ["FusionLakeflowConnect", "FusionDataSource"]
