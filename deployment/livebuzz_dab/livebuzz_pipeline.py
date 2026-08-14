from pyspark import pipelines as dp
from _generated_livebuzz_python_source import register_lakeflow_source

register_lakeflow_source(spark)
OPTIONS = {
    "base_url": spark.conf.get("livebuzz.base_url"),
    "campaign": spark.conf.get("livebuzz.campaign"),
    "api_key": spark.conf.get("livebuzz.api_key"),
}


def source(table_name: str):
    reader = spark.read.format("lakeflow_connect").option("tableName", table_name)
    for key, value in OPTIONS.items():
        reader = reader.option(key, value)
    return reader.load()


@dp.materialized_view(name="livebuzz_exhibitors")
def livebuzz_exhibitors():
    return source("exhibitors")


@dp.materialized_view(name="livebuzz_speakers")
def livebuzz_speakers():
    return source("speakers")


@dp.materialized_view(name="livebuzz_sessions")
def livebuzz_sessions():
    return source("sessions")


@dp.materialized_view(name="livebuzz_attendees")
def livebuzz_attendees():
    return source("attendees")
