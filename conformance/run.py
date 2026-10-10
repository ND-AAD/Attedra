"""Attedra 0.1.0 conformance runner.

Runs every fixture in conformance/fixtures against the reference library on a fresh
schema in the database named by ATTEDRA_DSN. Prints one line per fixture, writes
conformance/results.json and exits non-zero if any fixture fails or errors.

After a fixture's steps have all passed, the runner runs `transition_check` with frame {}
(the whole store, cutoff "now", record perspective) and fails the fixture when its
`differences` are not empty (README §8, spec 9.5.8, I-17). A fixture opts out only with
`"transition_check": false` and a `note` quoting the rule that makes the check
inapplicable (README §1).

Usage: python conformance/run.py [fixture-id-substring ...]
"""
from __future__ import annotations

import decimal
import hashlib
import json
import os
import platform
import sys
import traceback
from pathlib import Path

HERE = Path(__file__).resolve().parent
PACKAGE = HERE.parent
sys.path.insert(0, str(PACKAGE / "reference"))

import psycopg  # noqa: E402

from attedra_ref.api import Session  # noqa: E402
from attedra_ref.errors import WriteError  # noqa: E402

SCHEMA_SQL = (PACKAGE / "reference" / "schema.sql").read_text()


# ---------------------------------------------------------------------------
# Matching (README §3)

class Mismatch(Exception):
    pass


def _num(x):
    return isinstance(x, (int, float, decimal.Decimal)) and not isinstance(x, bool)


def match(pattern, actual, path="$"):
    if pattern == "~any":
        return
    if isinstance(pattern, dict):
        if not isinstance(actual, dict):
            raise Mismatch(f"{path}: expected object, got {actual!r}")
        for key, sub in pattern.items():
            if sub == "~absent":
                if key in actual:
                    raise Mismatch(f"{path}.{key}: expected absent, got {actual[key]!r}")
                continue
            if key not in actual:
                raise Mismatch(f"{path}.{key}: missing (have {sorted(actual)})")
            match(sub, actual[key], f"{path}.{key}")
        return
    if isinstance(pattern, list):
        if not isinstance(actual, list):
            raise Mismatch(f"{path}: expected list, got {actual!r}")
        if pattern and pattern[0] == "~unordered":
            want = pattern[1:]
            if len(want) != len(actual):
                raise Mismatch(f"{path}: expected {len(want)} items (unordered), got {len(actual)}: {actual!r}")
            remaining = list(actual)
            for i, sub in enumerate(want):
                for j, cand in enumerate(remaining):
                    try:
                        match(sub, cand, f"{path}[~{i}]")
                    except Mismatch:
                        continue
                    remaining.pop(j)
                    break
                else:
                    raise Mismatch(f"{path}: no unordered match for {sub!r} in {actual!r}")
            return
        if len(pattern) != len(actual):
            raise Mismatch(f"{path}: expected {len(pattern)} items, got {len(actual)}: {actual!r}")
        for i, (sub, act) in enumerate(zip(pattern, actual)):
            match(sub, act, f"{path}[{i}]")
        return
    if _num(pattern) and _num(actual):
        if decimal.Decimal(str(pattern)) != decimal.Decimal(str(actual)):
            raise Mismatch(f"{path}: expected {pattern!r}, got {actual!r}")
        return
    if isinstance(pattern, bool) or isinstance(actual, bool):
        if type(pattern) is not type(actual) or pattern != actual:
            raise Mismatch(f"{path}: expected {pattern!r}, got {actual!r}")
        return
    if pattern != actual:
        raise Mismatch(f"{path}: expected {pattern!r}, got {actual!r}")


# ---------------------------------------------------------------------------
# Execution

def fresh_schema(conn):
    with conn.cursor() as cur:
        cur.execute("DROP SCHEMA IF EXISTS public CASCADE")
        cur.execute("CREATE SCHEMA public")
        cur.execute(SCHEMA_SQL)
    conn.commit()


def run_fixture(conn, fx):
    fresh_schema(conn)
    session = Session(conn)
    plans = {}
    for n, step in enumerate(fx["steps"], 1):
        where = f"step {n} ({step.get('op')}{':' + step['read'] if step.get('op') == 'read' else ''})"
        op = step["op"]
        expect_error = step.get("expect_error")
        try:
            if op == "item":
                result = _create_item(session, step)
            elif op == "items":
                result = [_create_item(session, i) for i in step["items"]]
            elif op == "assert":
                values = step["values_json"] if "values_json" in step else _json_text(step["values"])
                result = session.assert_(step["item"], step["context"], step["source"], values,
                                         recorded_at=step.get("recorded_at"), recorded_by=step.get("recorded_by"))
            elif op == "connect":
                result = session.connect(step["from"], step["to"], step["at"])
            elif op == "plan_removal":
                result = session.plan_removal(step["target"])
                if step.get("as") and result.get("status") == "planned":
                    plans[step["as"]] = result["plan"]
            elif op == "confirm_removal":
                result = session.confirm_removal(plans.get(step["plan"].lstrip("$"), step["plan"]))
            elif op == "cancel_removal":
                result = session.cancel_removal(plans.get(step["plan"].lstrip("$"), step["plan"]))
            elif op == "read":
                result = session.read(step["read"], step.get("args", {}))
            elif op == "retire_interpretation":
                # README §2: from this step the reference does not have the named interpretation
                result = session.retire_interpretation(step["name"])
            else:
                raise Mismatch(f"{where}: unknown op {op!r}")
        except WriteError as e:
            if expect_error is None:
                raise Mismatch(f"{where}: unexpected write error {e.code}: {e}") from None
            if e.code != expect_error:
                raise Mismatch(f"{where}: expected error {expect_error}, got {e.code}: {e}") from None
            continue
        if expect_error is not None:
            raise Mismatch(f"{where}: expected error {expect_error}, but the write succeeded")
        if "expect" in step:
            try:
                match(step["expect"], _plain(result))
            except Mismatch as m:
                raise Mismatch(f"{where}: {m}") from None
    if fx.get("transition_check") is False:
        if not fx.get("note"):
            raise Mismatch('"transition_check": false needs a note quoting the rule that makes the check inapplicable (README §1)')
        return
    check = session.read("transition_check", {"frame": {}})
    if check.get("differences"):
        raise Mismatch("transition_check: " + json.dumps(_plain(check["differences"]), default=str))


def _create_item(session, step):
    """An `item` step: `definition`, or `definition_json` as raw JSON text (README §2)."""
    return session.create_item(step["id"], step["kind"], step.get("label"), step.get("definition"),
                               definition_json=step.get("definition_json"))


def _plain(o):
    """The result as plain JSON data, keeping exact numbers (README §3: numbers compare by
    decimal value). A non-JSON value is an error, as a JSON round trip would make it."""
    if isinstance(o, dict):
        if not all(isinstance(k, str) for k in o):
            raise TypeError(f"non-string key in {o!r}")
        return {k: _plain(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [_plain(v) for v in o]
    if o is None or isinstance(o, (str, bool, int, decimal.Decimal)):
        return o
    if isinstance(o, float):
        return decimal.Decimal(repr(o))
    raise TypeError(repr(o))


def _json_text(o) -> str:
    """JSON text for a step's `values`, writing fixture numbers (parsed as Decimal) exactly."""
    if isinstance(o, dict):
        return "{" + ", ".join(json.dumps(k) + ": " + _json_text(v) for k, v in o.items()) + "}"
    if isinstance(o, list):
        return "[" + ", ".join(_json_text(v) for v in o) + "]"
    if isinstance(o, decimal.Decimal):
        if not o.is_finite():
            raise TypeError(repr(o))
        return str(o)
    return json.dumps(o)


# Outputs of a run are not part of the contents it tested: result files and the report.
_OUTPUTS = {"CONFORMANCE.md"}


# The package hash covers the published tree: the files at the root and these directories.
_HASHED_DIRS = ("conformance", "examples", "reference", "scripts")


def package_hash():
    h = hashlib.sha256()
    for p in sorted(PACKAGE.rglob("*")):
        rel = p.relative_to(PACKAGE)
        if len(rel.parts) > 1 and rel.parts[0] not in _HASHED_DIRS:
            continue
        if (p.is_file() and "__pycache__" not in p.parts and not p.name.endswith("results.json")
                and p.name not in _OUTPUTS and p.suffix in {".py", ".sql", ".json", ".md", ".toml", ".sh"}):
            h.update(str(p.relative_to(PACKAGE)).encode())
            h.update(p.read_bytes())
    return h.hexdigest()


def main(argv):
    dsn = os.environ.get("ATTEDRA_DSN")
    if not dsn:
        print("ATTEDRA_DSN is not set; use scripts/run_conformance.sh", file=sys.stderr)
        return 2
    # ATTEDRA_FIXTURES_DIR points the runner at another fixture directory (default: conformance/fixtures).
    # Results for another directory are written beside it, so conformance/results.json is untouched.
    fixtures_env = os.environ.get("ATTEDRA_FIXTURES_DIR")
    fixtures_dir = Path(fixtures_env).resolve() if fixtures_env else HERE / "fixtures"
    results_path = fixtures_dir.with_name(fixtures_dir.name + ".results.json") if fixtures_env else HERE / "results.json"
    files = sorted(fixtures_dir.glob("*.json"))
    if argv:
        files = [f for f in files if any(a in f.stem for a in argv)]
    results = []
    counts = {"PASS": 0, "FAIL": 0, "ERROR": 0, "BLOCKED": 0}
    with psycopg.connect(dsn) as conn:
        with conn.cursor() as cur:
            cur.execute("SHOW server_version")
            server_version = cur.fetchone()[0]
        for f in files:
            fx = json.loads(f.read_text(), parse_float=decimal.Decimal)
            if fx.get("blocked_on_spec"):
                status, detail = "BLOCKED", fx["blocked_on_spec"]
            else:
                try:
                    run_fixture(conn, fx)
                    status, detail = "PASS", ""
                except Mismatch as m:
                    conn.rollback()
                    status, detail = "FAIL", str(m)
                except Exception as e:  # noqa: BLE001
                    conn.rollback()
                    status, detail = "ERROR", f"{type(e).__name__}: {e}\n{traceback.format_exc(limit=4)}"
            counts[status] += 1
            results.append({"id": fx["id"], "family": fx.get("family"), "rules": fx.get("rules", []), "status": status, "detail": detail})
            print(f"{status:7} {fx['id']}" + (f"\n        {detail.splitlines()[0]}" if detail else ""))
    summary = {
        "counts": counts,
        "total": len(results),
        "environment": {
            "postgresql": server_version,
            "image": os.environ.get("ATTEDRA_IMAGE", "unknown"),
            "python": platform.python_version(),
            "psycopg": psycopg.__version__,
            "package_sha256": package_hash(),
        },
        "results": results,
    }
    results_path.write_text(json.dumps(summary, indent=1))
    print(f"\n{counts['PASS']} passed, {counts['FAIL']} failed, {counts['ERROR']} errors, {counts['BLOCKED']} blocked, of {len(results)}")
    return 0 if counts["FAIL"] == 0 and counts["ERROR"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
