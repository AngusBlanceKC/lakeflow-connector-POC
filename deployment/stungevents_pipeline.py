"""Run the generated StungEvents connector in a Lakeflow pipeline."""

from pyspark import pipelines as dp

from _generated_stungevents_python_source import register_lakeflow_source


register_lakeflow_source(spark)


@dp.materialized_view(name="stungevents_events")
def stungevents_events():
    return (
        spark.read.format("lakeflow_connect")
        .option("tableName", "events")
        .option("base_url", "https://api.stungevents.com")
        .option("limit", "100")
        .load()
    )
