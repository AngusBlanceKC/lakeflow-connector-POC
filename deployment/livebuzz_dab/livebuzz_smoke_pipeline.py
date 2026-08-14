from pyspark import pipelines as dp
from _generated_livebuzz_python_source import register_lakeflow_source

register_lakeflow_source(spark)


@dp.materialized_view(name="livebuzz_exhibitors_smoke")
def livebuzz_exhibitors_smoke():
    return (
        spark.read.format("lakeflow_connect")
        .option("tableName", "exhibitors")
        .option("base_url", spark.conf.get("livebuzz.base_url"))
        .option("campaign", spark.conf.get("livebuzz.campaign"))
        .option("api_key", spark.conf.get("livebuzz.api_key"))
        .load()
    )
