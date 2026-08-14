"""One-table diagnostic pipeline for Visit Create connectivity."""

from pyspark import pipelines as dp

from _generated_visit_create_v2_python_source import register_lakeflow_source


register_lakeflow_source(spark)


@dp.materialized_view(name="visit_create_v2_smoke_expos")
def visit_create_v2_smoke_expos():
    return (
        spark.read.format("lakeflow_connect")
        .option("tableName", "expos")
        .option("base_url", spark.conf.get("visit_create_v2.base_url"))
        .option("api_key", spark.conf.get("visit_create_v2.api_key"))
        .option("expo_id", spark.conf.get("visit_create_v2.expo_id"))
        .option("limit", "10")
        .load()
    )
