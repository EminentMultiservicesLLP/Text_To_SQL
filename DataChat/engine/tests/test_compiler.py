from datetime import date

import pytest

from datachat.compiler import CompileError, compile_plan, distinct_values_sql
from datachat.guard import GuardError, check_sql
from datachat.pack import Pack
from datachat.plan import Filter, Plan, Sort, TimeRange

LAST_MONTH = TimeRange(start=date(2026, 8, 1), end=date(2026, 9, 1), label="August 2026", unit="month")


def compiled(pack, plan):
    cq = compile_plan(plan, pack, 500)
    check_sql(cq.sql, pack.database.dialect, pack.allowed_table_names())
    return cq


def test_tsql_top_branches(pack):
    plan = Plan(area="sales", metrics=["revenue"], group_by=["branch"], time=LAST_MONTH,
                sort=Sort(metric="revenue", desc=True), limit=5)
    sql = compiled(pack, plan).sql
    assert sql.startswith("SELECT TOP (5) [inv].[branchCode] AS [branch]")
    assert "SUM([inv].[TotalAmount]) AS [revenue]" in sql
    assert "CAST([inv].[InvoiceDate] AS DATE) >= '2026-08-01'" in sql
    assert "CAST([inv].[InvoiceDate] AS DATE) < '2026-09-01'" in sql
    assert "([inv].[Status] IS NULL OR [inv].[Status] <> 'Cancelled')" in sql
    assert "GROUP BY [inv].[branchCode]" in sql and sql.rstrip().endswith("ORDER BY [revenue] DESC")
    assert "JOIN" not in sql


def test_item_area_joins_invoices(pack):
    plan = Plan(area="items", metrics=["item_sales"], group_by=["category", "branch"])
    sql = compiled(pack, plan).sql
    assert "FROM [dbo].[Rista_SaleItems] AS [item]" in sql
    assert "LEFT JOIN [dbo].[Rista_SaleInvoices] AS [inv] ON [item].[InvoiceID] = [inv].[InvoiceID]" in sql


def test_one_to_one_join_works_from_invoices(pack):
    plan = Plan(area="sales", metrics=["orders"], group_by=["source"])
    sql = compiled(pack, plan).sql
    assert "LEFT JOIN [dbo].[Rista_SaleSourceInfo] AS [src] ON [inv].[InvoiceID] = [src].[InvoiceID]" in sql


def test_items_cannot_be_reached_from_bill_level_area(pack):
    with pytest.raises(CompileError):
        compile_plan(Plan(area="sales", metrics=["revenue"], group_by=["category"]), pack, 500)


def test_values_are_escaped(pack):
    plan = Plan(area="sales", metrics=["revenue"], filters=[Filter(dimension="branch", values=["O'Brien"])])
    assert "IN ('O''Brien')" in compiled(pack, plan).sql


def test_negated_filter_keeps_nulls(pack):
    plan = Plan(area="payments", metrics=["payment_amount"],
                filters=[Filter(dimension="payment_mode", values=["Cash"], negate=True)])
    assert "([pay].[Mode] IS NULL OR [pay].[Mode] NOT IN ('Cash'))" in compiled(pack, plan).sql


def test_no_limit_fetches_one_more_than_cap(pack):
    cq = compiled(pack, Plan(area="sales", metrics=["revenue"], group_by=["branch"]))
    assert cq.sql.startswith("SELECT TOP (501)") and cq.fetch_limit == 501 and cq.cap == 500


def test_time_grains_tsql(pack):
    for grain in ("hour", "day", "week", "month", "year", "weekday"):
        cq = compiled(pack, Plan(area="sales", metrics=["revenue"], group_by=[f"time:{grain}"], time=LAST_MONTH))
        assert f"AS [{grain}]" in cq.sql and f"ORDER BY [{grain}]" in cq.sql


def test_distinct_values_sql(pack):
    sql = distinct_values_sql(pack, "branch")
    assert sql.startswith("SELECT DISTINCT TOP (5000) [inv].[branchCode]")
    check_sql(sql, "tsql", pack.allowed_table_names())


PG_PACK = {
    "client": "pgdemo", "display_name": "PG demo",
    "database": {"dialect": "postgres", "dsn_env": "PGDEMO_DSN"},
    "tables": {"o": {"name": "public.orders"}, "c": {"name": "public.customers"}},
    "joins": [{"from": "o", "to": "c", "columns": [["customer_id", "id"]]}],
    "dimensions": {"city": {"column": "c.City", "label": "City"}},
    "areas": {"orders": {"label": "Orders", "fact": "o", "time_column": "o.created_at", "default_metric": "revenue",
                         "metrics": {"revenue": {"expr": "SUM({o.total})", "label": "Revenue"}}}},
}


def test_postgres_dialect():
    pack = Pack.model_validate(PG_PACK)
    plan = Plan(area="orders", metrics=["revenue"], group_by=["city", "time:month"], time=LAST_MONTH, limit=10)
    sql = compiled(pack, plan).sql
    assert sql.startswith('SELECT "c"."City" AS "city"')
    assert "CAST(DATE_TRUNC('month', \"o\".\"created_at\") AS DATE) AS \"month\"" in sql
    assert 'LEFT JOIN "public"."customers" AS "c" ON "o"."customer_id" = "c"."id"' in sql
    assert "\"o\".\"created_at\" >= '2026-08-01'" in sql
    assert sql.rstrip().endswith("LIMIT 10")


@pytest.mark.parametrize("sql", [
    "DELETE FROM dbo.Rista_SaleInvoices",
    "SELECT * FROM dbo.SomeOtherTable",
    "SELECT 1; DROP TABLE dbo.Rista_SaleInvoices",
    "UPDATE dbo.Rista_SaleInvoices SET TotalAmount = 0",
    "SELECT * INTO dbo.copy FROM dbo.Rista_SaleInvoices",
])
def test_guard_rejects(pack, sql):
    with pytest.raises(GuardError):
        check_sql(sql, "tsql", pack.allowed_table_names())
