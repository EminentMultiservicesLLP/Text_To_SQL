import sys
from pathlib import Path

import yaml

ENGINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ENGINE / "tools"))
from add_table import build_area, candidate_pack, insert_in_section  # noqa: E402
from datachat.pack import Pack, load_pack  # noqa: E402
from draft_area import Draft  # noqa: E402
from introspect_postgres import Column, Table  # noqa: E402

PACK = ENGINE / "packs" / "bis" / "semantic.yaml"


def draft() -> Draft:
    cols = [Column("loanid", "integer", False, None, role="hidden"),
            Column("empid", "integer", True, None, role="hidden"),
            Column("startdate", "date", True, None, role="time"),
            Column("loanamount", "numeric", True, None, role="metric"),
            Column("balanceprincipal", "numeric", True, None, role="metric"),
            Column("status", "character varying", True, None, role="hidden")]
    d = Draft("bis", "public", "smtbtloandetails", "loan", 1000, Table("public", "smtbtloandetails", 0, 0, 0, 0, None,
                                                                      cols, ["loanid"]), load_pack(PACK), PACK)
    d.joins = [{"from": "loan", "to": "emp", "columns": [["empid", "empid"]]}]
    d.profile = [(cols[2], {"min": None, "max": None, "empty": 0, "too_old": 0, "future": 0}),
                 (cols[3], {"min": 0, "max": 1, "sum": 1, "zero": 0, "empty": 0}),
                 (cols[4], {"min": 0, "max": 1, "sum": 1, "zero": 0, "empty": 0})]
    d.flags = {"loan.status": [("Open", 700), ("Closed", 250), ("Cancelled", 50)], "emp.active": [("1", 900), ("0", 100)]}
    d.dims = ["branch", "department"]
    return d


MODEL = {
    "area_name": "Employee Loans", "label": "Employee loans", "synonyms": ["loan", "karz"],
    "row_meaning": "current_state", "time_column": "startdate",
    "active_flag": {"column": "emp.active", "value": "1"},
    "exclude": [{"column": "status", "value": "Cancelled", "reason": "cancelled"},
                {"column": "status", "value": "Deleted", "reason": "no such value"}],
    "measures": [
        {"name": "loan_balance", "kind": "sum", "column": "balanceprincipal", "label": "Loan balance",
         "synonyms": ["baki loan"], "format": "currency"},
        {"name": "loan_count", "kind": "count", "column": "", "label": "Loans", "synonyms": [], "format": "integer"},
        {"name": "salary", "kind": "sum", "column": "basicsalary", "label": "Salary", "synonyms": [], "format": "number"},
        {"name": "avg_loan", "kind": "average", "column": "loanamount", "label": "Average loan", "synonyms": [],
         "format": "currency"}],
    "sensitive_columns": [],
    "test_questions": [{"question": "loan balance by branch", "measure": "loan_balance", "by": "branch"},
                       {"question": "made up", "measure": "nothing", "by": ""},
                       {"question": "loans by colour", "measure": "loan_count", "by": "colour"}],
    "open_questions": [],
}


def test_model_answer_is_checked_and_sql_is_built_in_code():
    name, area, problems, tests = build_area(draft(), MODEL)
    assert name == "employee_loans"
    m = area["metrics"]
    assert set(m) == {"loan_balance", "loan_count", "avg_loan"}  # salary column doesn't exist
    assert m["loan_balance"]["expr"] == "SUM(CASE WHEN {emp.active} = 1 THEN {loan.balanceprincipal} ELSE 0 END)"
    assert m["loan_count"]["expr"] == "SUM(CASE WHEN {emp.active} = 1 THEN 1 ELSE 0 END)"
    assert m["avg_loan"]["expr"].endswith("/ NULLIF(SUM(CASE WHEN {emp.active} = 1 THEN 1 ELSE 0 END), 0)")
    assert all(x.get("snapshot") for x in m.values())
    assert area["default_filters"] == [{"column": "loan.status", "op": "neq", "value": "Cancelled"}]
    assert area["time_column"] == "loan.startdate"
    assert any("basicsalary" in p for p in problems) and any("Deleted" in p for p in problems)
    assert [t["by"] for t in tests] == ["branch", ""]
    Pack.model_validate(candidate_pack(draft(), name, area))


def test_sensitive_column_is_never_a_measure():
    name, area, problems, _ = build_area(draft(), {**MODEL, "sensitive_columns": ["loan.balanceprincipal"]})
    assert "loan_balance" not in area["metrics"]
    assert any("sensitive" in p for p in problems)


def test_merge_writes_a_valid_pack_and_unique_scenarios(tmp_path, monkeypatch):
    import add_table
    (tmp_path / "packs" / "bis").mkdir(parents=True)
    (tmp_path / "scenarios").mkdir()
    pack_copy = tmp_path / "packs" / "bis" / "semantic.yaml"
    pack_copy.write_text(PACK.read_text(encoding="utf-8"), encoding="utf-8")
    scen = ENGINE / "scenarios" / "bis.yaml"
    (tmp_path / "scenarios" / "bis.yaml").write_text(scen.read_text(encoding="utf-8"), encoding="utf-8")
    monkeypatch.setattr(add_table, "ENGINE_ROOT", tmp_path)
    d = draft()
    d.pack_path = pack_copy
    name, area, problems, tests = build_area(d, MODEL)
    results = [{**t, "ok": i == 0} for i, t in enumerate(tests)]
    added = add_table.merge(d, name, area, problems, results)
    text = pack_copy.read_text(encoding="utf-8")
    pack = load_pack(pack_copy)
    assert name in pack.areas and pack.tables["loan"].name == "public.smtbtloandetails"
    assert "# CHECK:" in text and text.count("\n# ") >= PACK.read_text(encoding="utf-8").count("\n# ")
    scenarios = yaml.safe_load((tmp_path / "scenarios" / "bis.yaml").read_text(encoding="utf-8"))["scenarios"]
    ids = [s["id"] for s in scenarios]
    assert len(ids) == len(set(ids)) and set(added) <= set(ids)
    new = [s for s in scenarios if s["id"] in added]
    assert not new[0].get("needs_model") and new[1]["needs_model"]
    assert new[0]["expect"]["group_by"] == ["branch"]


def test_insert_keeps_comments_and_order():
    text = "# head\ntables:\n  a: { name: x.a }\n  # note\n  b: { name: x.b }\n\njoins:\n  - {}\n"
    out = insert_in_section(text, "tables", "  c: { name: x.c }")
    assert out.index("c: { name: x.c }") > out.index("b: { name: x.b }") < out.index("joins:")
    assert "# note" in out and "# head" in out
    assert list(yaml.safe_load(out)["tables"]) == ["a", "b", "c"]
