from pyspark import pipelines as dp

from _generated_gevme_python_source import register_lakeflow_source


register_lakeflow_source(spark)


@dp.materialized_view(name="gevme_smoke_attendees")
def gevme_smoke_attendees():
    return (
        spark.read.format("lakeflow_connect")
        .option("tableName", "attendees")
        .option("base_url", spark.conf.get("gevme.base_url"))
        .option("event_id", spark.conf.get("gevme.event_id"))
        .option("access_token", spark.conf.get("gevme.access_token"))
        .load()
    )
