"""Lakeflow Declarative Pipeline for the Visit Create v2 connector."""

from pyspark import pipelines as dp

from _generated_visit_create_v2_python_source import register_lakeflow_source


register_lakeflow_source(spark)


def _read_visit_table(table_name: str):
    return (
        spark.read.format("lakeflow_connect")
        .option("tableName", table_name)
        .option("base_url", spark.conf.get("visit_create_v2.base_url"))
        .option("api_key", spark.conf.get("visit_create_v2.api_key"))
        .option("expo_id", spark.conf.get("visit_create_v2.expo_id"))
        .option("limit", "100")
        .load()
    )


@dp.materialized_view(name="visit_create_v2_expos")
def visit_create_v2_expos():
    return _read_visit_table("expos")


@dp.materialized_view(name="visit_create_v2_visitors")
def visit_create_v2_visitors():
    return _read_visit_table("visitors")


@dp.materialized_view(name="visit_create_v2_partners")
def visit_create_v2_partners():
    return _read_visit_table("partners")


@dp.materialized_view(name="visit_create_v2_participants")
def visit_create_v2_participants():
    return _read_visit_table("participants")


@dp.materialized_view(name="visit_create_v2_contents")
def visit_create_v2_contents():
    return _read_visit_table("contents")


@dp.materialized_view(name="visit_create_v2_licenses")
def visit_create_v2_licenses():
    return _read_visit_table("licenses")


@dp.materialized_view(name="visit_create_v2_payments")
def visit_create_v2_payments():
    return _read_visit_table("payments")


@dp.materialized_view(name="visit_create_v2_actions")
def visit_create_v2_actions():
    return _read_visit_table("actions")


@dp.materialized_view(name="visit_create_v2_connections")
def visit_create_v2_connections():
    return _read_visit_table("connections")


@dp.materialized_view(name="visit_create_v2_activities")
def visit_create_v2_activities():
    return _read_visit_table("activities")


@dp.materialized_view(name="visit_create_v2_touchpoints")
def visit_create_v2_touchpoints():
    return _read_visit_table("touchpoints")


@dp.materialized_view(name="visit_create_v2_orders")
def visit_create_v2_orders():
    return _read_visit_table("orders")


@dp.materialized_view(name="visit_create_v2_questions")
def visit_create_v2_questions():
    return _read_visit_table("questions")


@dp.materialized_view(name="visit_create_v2_registration_types")
def visit_create_v2_registration_types():
    return _read_visit_table("registrationTypes")


@dp.materialized_view(name="visit_create_v2_registration_forms")
def visit_create_v2_registration_forms():
    return _read_visit_table("registrationForms")


@dp.materialized_view(name="visit_create_v2_webhooks")
def visit_create_v2_webhooks():
    return _read_visit_table("webhooks")
