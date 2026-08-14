from pyspark import pipelines as dp

from _generated_gevme_python_source import register_lakeflow_source


BASE_URL = spark.conf.get("gevme.base_url")
EVENT_ID = spark.conf.get("gevme.event_id")
ACCESS_TOKEN = spark.conf.get("gevme.access_token")
CLIENT_ID = spark.conf.get("gevme.client_id")
CLIENT_SECRET = spark.conf.get("gevme.client_secret")

register_lakeflow_source(spark)


def _source(table_name: str):
    return (
        spark.read.format("lakeflow_connect")
        .option("tableName", table_name)
        .option("base_url", BASE_URL)
        .option("event_id", EVENT_ID)
        .option("access_token", ACCESS_TOKEN)
        .option("client_id", CLIENT_ID)
        .option("client_secret", CLIENT_SECRET)
        .load()
    )


@dp.materialized_view(name="gevme_attendees")
def gevme_attendees():
    return _source("attendees")
