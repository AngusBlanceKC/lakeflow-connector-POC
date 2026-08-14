from pyspark import pipelines as dp

from _generated_fusion_python_source import register_lakeflow_source


register_lakeflow_source(spark)


@dp.materialized_view(name="fusion_smoke_people")
def fusion_smoke_people():
    return (
        spark.read.format("lakeflow_connect")
        .option("tableName", "people")
        .option("base_url", spark.conf.get("fusion.base_url"))
        .option("event_id", spark.conf.get("fusion.event_id"))
        .option("username", spark.conf.get("fusion.username"))
        .option("password", spark.conf.get("fusion.password"))
        .option("install_name", spark.conf.get("fusion.install_name"))
        .option("api_key", spark.conf.get("fusion.api_key"))
        .load()
    )
