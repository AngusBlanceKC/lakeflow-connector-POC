from pyspark import pipelines as dp

from _generated_fusion_python_source import register_lakeflow_source


BASE_URL = spark.conf.get("fusion.base_url")
EVENT_ID = spark.conf.get("fusion.event_id")
USERNAME = spark.conf.get("fusion.username")
PASSWORD = spark.conf.get("fusion.password")
INSTALL_NAME = spark.conf.get("fusion.install_name")
API_KEY = spark.conf.get("fusion.api_key")

register_lakeflow_source(spark)


def _source(table_name: str):
    return spark.read.format("lakeflow_connect").option("tableName", table_name).option("base_url", BASE_URL).option("event_id", EVENT_ID).option("username", USERNAME).option("password", PASSWORD).option("install_name", INSTALL_NAME).option("api_key", API_KEY).load()


@dp.materialized_view(name="fusion_people")
def fusion_people():
    return _source("people")


@dp.materialized_view(name="fusion_event_tickets")
def fusion_event_tickets():
    return _source("event_tickets")
