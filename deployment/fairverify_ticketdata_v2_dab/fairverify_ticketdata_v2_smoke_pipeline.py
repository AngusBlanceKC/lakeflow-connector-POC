from pyspark import pipelines as dp
from _generated_fairverify_ticketdata_v2_python_source import register_lakeflow_source

register_lakeflow_source(spark)


@dp.materialized_view(name="fairverify_smoke_tickets")
def fairverify_smoke_tickets():
    return (spark.read.format("lakeflow_connect").option("tableName", "tickets")
            .option("base_url", spark.conf.get("fairverify.base_url"))
            .option("event_id", spark.conf.get("fairverify.event_id"))
            .option("api_key", spark.conf.get("fairverify.api_key")).load())
