from pyspark import pipelines as dp
from _generated_showoff_asp_v1_4_python_source import register_lakeflow_source

register_lakeflow_source(spark)


@dp.materialized_view(name="showoff_smoke_visitors")
def showoff_smoke_visitors():
    return (spark.read.format("lakeflow_connect").option("tableName", "visitors")
            .option("base_url", spark.conf.get("showoff.base_url"))
            .option("api_key", spark.conf.get("showoff.api_key"))
            .option("api_secret", spark.conf.get("showoff.api_secret"))
            .option("site_uuid", spark.conf.get("showoff.site_uuid")).load())
