from pyspark import pipelines as dp
from _generated_showoff_asp_v1_4_python_source import register_lakeflow_source

register_lakeflow_source(spark)
OPTIONS = {"base_url": spark.conf.get("showoff.base_url"), "api_key": spark.conf.get("showoff.api_key"), "api_secret": spark.conf.get("showoff.api_secret"), "site_uuid": spark.conf.get("showoff.site_uuid")}


def source(table_name: str):
    result = spark.read.format("lakeflow_connect").option("tableName", table_name)
    for key, value in OPTIONS.items(): result = result.option(key, value)
    return result.load()


@dp.materialized_view(name="showoff_visitors")
def showoff_visitors(): return source("visitors")


@dp.materialized_view(name="showoff_exhibitors")
def showoff_exhibitors(): return source("exhibitors")


@dp.materialized_view(name="showoff_seminars")
def showoff_seminars(): return source("seminars")


@dp.materialized_view(name="showoff_sessions")
def showoff_sessions(): return source("sessions")


@dp.materialized_view(name="showoff_speakers")
def showoff_speakers(): return source("speakers")


@dp.materialized_view(name="showoff_sites")
def showoff_sites(): return source("sites")


@dp.materialized_view(name="showoff_products")
def showoff_products(): return source("products")
