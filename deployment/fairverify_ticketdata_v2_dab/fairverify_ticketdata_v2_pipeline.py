from pyspark import pipelines as dp
from _generated_fairverify_ticketdata_v2_python_source import register_lakeflow_source

register_lakeflow_source(spark)
BASE_URL = spark.conf.get("fairverify.base_url")
EVENT_ID = spark.conf.get("fairverify.event_id")
API_KEY = spark.conf.get("fairverify.api_key")
ACCESS_TOKEN = spark.conf.get("fairverify.access_token")


def source(table_name: str):
    return (spark.read.format("lakeflow_connect").option("tableName", table_name)
            .option("base_url", BASE_URL).option("event_id", EVENT_ID)
            .option("api_key", API_KEY).option("access_token", ACCESS_TOKEN).load())


@dp.materialized_view(name="fairverify_events")
def fairverify_events():
    return source("events")


@dp.materialized_view(name="fairverify_tickets")
def fairverify_tickets():
    return source("tickets")
