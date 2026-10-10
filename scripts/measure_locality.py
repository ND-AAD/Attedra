"""Locality measurement of the reference library (9.10.1).

Measures one scoped open-work read and one story read of the reference library:

1. with unrelated scopes grown 1x, 10x and 100x (and 1000x) while the relevant scope is fixed;
2. with the relevant scope's history and fan-out grown while unrelated data is fixed.

For each run it reports, per read:

- the records loaded (Items, Assertions and Connections in the record set the read evaluated)
  and the rows the read fetched from the store;
- the wall time of the read (median of several repetitions) and the part of it spent in
  reference-discovery queries, the queries that find Assertions by the references in their
  values;
- the number of queries the read issued, and how many of them were discovery queries;
- for every discovery query of one execution, PostgreSQL's plan under EXPLAIN (ANALYZE,
  BUFFERS): the distinct top nodes, how many plans contain a sequential scan, and the shared
  buffers the queries touched in all.

The result describes this environment and revision only (spec 11.4); it is not a performance
claim.

Every scope has the same shape: a project Item, a door-schedule Item and doors, connected
project -> schedule -> door. Each door has a schedule statement (re-issued once per history
step with a new finish), a specification statement that disagrees with it, a recorded conflict
story (whose later evidence the library records as continuation detections, 7.2.5) and an
expectation established by one instruction that targets every door's expectation. Unrelated
scopes have their own Items throughout and share nothing with the relevant scope.

The relevant scope is always written through the library. Unrelated scopes are written once
through the library as a template and then copied in SQL with their identifiers renamed, so
that they are exactly the records the library writes, without rewriting each copy.

With ATTEDRA_LOCALITY_NORMALIZE=1, every scope also records a normalization of its project
Item (7.3.8), under the fixture fire-rating interpretation (conformance README §5), after its
other records, so that every scope, the relevant one included, holds a normalization; the
results are then written to scripts/locality_normalized_results.json.

Usage (starts and removes a disposable container of the pinned image unless ATTEDRA_DSN is set):

    uv run --no-project --python 3.12 --with "psycopg[binary]==3.3.6" python scripts/measure_locality.py
"""
from __future__ import annotations

import json
import os
import platform
import statistics
import subprocess
import sys
import time
from pathlib import Path

PACKAGE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PACKAGE / "reference"))

import psycopg  # noqa: E402

import attedra_ref.reads as reads_module  # noqa: E402
from attedra_ref.account import Account  # noqa: E402
from attedra_ref.api import Session  # noqa: E402
from attedra_ref.store import Store  # noqa: E402

IMAGE = "postgres@sha256:74935e72241653ca55e0414067e6d8763aceb8a810eb51b452253ec3dcfc4336"  # postgres:18 (18.6)
SCHEMA_SQL = (PACKAGE / "reference" / "schema.sql").read_text()
CUTOFF = "2026-12-31-07:00"
REPEAT = 5
NORMALIZE = os.environ.get("ATTEDRA_LOCALITY_NORMALIZE") == "1"

BASE_DOORS, BASE_HISTORY = 5, 2
UNRELATED = [1, 10, 100, 1000]              # unrelated scopes, each the size of the base relevant scope
RELEVANT = [(5, 2), (10, 4), (20, 8)]       # (doors, schedule issues per door) of the relevant scope


# ---------------------------------------------------------------------------------------
# data


def _ev(at: str) -> dict:
    return {"@context": {"role": "event", "at": at}}


def _ref(i: str, c: str, s: str, prop: str | None = None) -> dict:
    r = {"@ref": "assertion", "item": i, "context": c, "source": s}
    if prop:
        r["property"] = prop
    return r


def write_scope(s: Session, p: str, doors: int, history: int) -> None:
    """One scope with prefix ``p``, written through the library."""
    item = s.create_item
    item(f"{p}project", "project")
    item(f"{p}schedule", "door-schedule")
    item(f"{p}a-601", "schedule-sheet")
    item(f"{p}spec", "specification")
    item(f"{p}instr", "instruction")
    item(f"{p}instr-at", "event", None, _ev("2026-06-01T10:00-07:00"))
    item(f"{p}ev-spec", "event", None, _ev("2026-06-01T11:00-07:00"))
    for k in range(history):
        day = 1 + k
        month, dom = (6, day) if day <= 30 else (7, day - 30) if day <= 61 else (8, day - 61)
        item(f"{p}ev-a-{k}", "event", None, _ev(f"2026-{month:02d}-{dom:02d}T09:00-07:00"))
    item(f"{p}e-by", "expectation-context", None,
         {"@context": {"role": "expectation", "timing": {"type": "by", "instant": "2026-07-01-07:00"}, "fresh": False}})
    s.connect(f"{p}project", f"{p}schedule", "2026-05-01-07:00")
    for i in range(doors):
        d = f"{p}door-{i}"
        item(d, "door")
        s.connect(f"{p}schedule", d, "2026-05-01-07:00")
        s.assert_(d, f"{p}ev-a-0", f"{p}a-601", json.dumps({"finish": "paint-0", "hardware": "HW-1"}))
        s.assert_(d, f"{p}ev-spec", f"{p}spec", json.dumps({"finish": "stain"}))
        st = f"{p}story-{i}"
        item(st, "story")
        item(f"{st}/d1", "event", None, _ev("2026-06-01T17:00-07:00"))
        s.assert_(st, f"{st}/d1", st, json.dumps({
            "@action": "detect",
            "@story": {"kind": "conflict", "subject": {"@ref": "item", "id": d}, "property": "finish"},
            "@basis": [_ref(d, f"{p}ev-a-0", f"{p}a-601", "finish"), _ref(d, f"{p}ev-spec", f"{p}spec", "finish")],
            "@frame": {"scope": {"@ref": "item", "id": f"{p}project"}, "cutoff": "2026-06-01T17:00-07:00",
                       "perspective": "record", "interpretation": None, "interpretation_version": None}}))
        s.assert_(d, f"{p}e-by", f"{p}a-601", json.dumps({"hardware": "HW-2"}))
    s.assert_(f"{p}instr", f"{p}instr-at", f"{p}instr", json.dumps({
        "@action": "establish", "@targets": [_ref(f"{p}door-{i}", f"{p}e-by", f"{p}a-601") for i in range(doors)]}))
    for k in range(1, history):
        for i in range(doors):
            s.assert_(f"{p}door-{i}", f"{p}ev-a-{k}", f"{p}a-601", json.dumps({"finish": f"paint-{k}"}))
    if NORMALIZE:
        # 7.3.8: a normalization of the scope's project, effective after its other records
        item(f"{p}norm", "normalization")
        item(f"{p}norm-at", "event", None, _ev("2026-09-01T10:00-07:00"))
        res = s.assert_(f"{p}norm", f"{p}norm-at", f"{p}norm", json.dumps({
            "@action": "reinterpret", "@targets": [{"@ref": "item", "id": f"{p}project"}],
            "@interpretation": {"name": "fixture-fire-rating", "version": "1"}}))
        if res.get("status") != "inserted":
            raise SystemExit(f"normalization of {p}project: {res}")


def clone_scope(conn, src: str, dst: str) -> None:
    """Copy every record whose identifiers carry prefix ``src`` under prefix ``dst``. The
    expectation property acts that maintenance records (README §7) are Items named
    ``exp:<item>/<context>/<source>/<property>/...``, so the prefix is also renamed after
    ``exp:`` and after ``/`` in identifiers and in the values that reference them."""
    def ren(expr: str) -> str:
        return (f"replace(replace(CASE WHEN starts_with({expr}, %(src)s) THEN %(dst)s || substr({expr}, %(n)s) "
                f"ELSE {expr} END, 'exp:' || %(src)s, 'exp:' || %(dst)s), '/' || %(src)s, '/' || %(dst)s)")

    def ren_json(expr: str) -> str:
        return (f"replace(replace(replace({expr}::text, '\"' || %(src)s, '\"' || %(dst)s), "
                f"'exp:' || %(src)s, 'exp:' || %(dst)s), '/' || %(src)s, '/' || %(dst)s)::jsonb")

    mine = "(starts_with({c}, %(src)s) OR starts_with({c}, 'exp:' || %(src)s))"
    params = {"src": src, "dst": dst, "n": len(src) + 1}
    with conn.cursor() as cur:
        cur.execute(f"INSERT INTO items SELECT {ren('id')}, kind, label, {ren_json('definition')} "
                    f"FROM items WHERE {mine.format(c='id')}", params)
        cur.execute(f'INSERT INTO assertions SELECT {ren("item_id")}, {ren("context_id")}, {ren("source_id")}, '
                    f'{ren_json(chr(34) + "values" + chr(34))}, recorded_at, recorded_by '
                    f"FROM assertions WHERE {mine.format(c='item_id')}", params)
        cur.execute(f"INSERT INTO connections SELECT {ren('from_id')}, {ren('to_id')}, properties "
                    f"FROM connections WHERE starts_with(from_id, %(src)s)", params)
    conn.commit()


def counts(conn) -> dict:
    with conn.cursor() as cur:
        out = {}
        for t in ("items", "assertions", "connections"):
            cur.execute(f"SELECT count(*) FROM {t}")
            out[t] = cur.fetchone()[0]
    conn.rollback()
    return out


def analyze(conn) -> None:
    """Refresh planner statistics after bulk loading, so plans reflect the data measured."""
    with conn.cursor() as cur:
        cur.execute("ANALYZE")
    conn.commit()


def fresh(conn) -> None:
    with conn.cursor() as cur:
        cur.execute("DROP SCHEMA IF EXISTS public CASCADE")
        cur.execute("CREATE SCHEMA public")
        cur.execute(SCHEMA_SQL)
    conn.commit()


# ---------------------------------------------------------------------------------------
# measurement


class _CountingAccount(Account):
    """Records the size of every record set a read evaluates."""

    sizes: list[int] = []

    def __init__(self, rs, *a, **k):
        _CountingAccount.sizes.append(rs.size())
        super().__init__(rs, *a, **k)


def _is_discovery(sql: str) -> bool:
    """A query that finds Assertions by the references in their values: by JSON containment,
    through the identifier index, or through the discovery and target indexes (store.py)."""
    return ('"values" @>' in sql or 'identifier_entries("values")' in sql or 'discovery_entries("values")' in sql
            or 'target_entries("values")' in sql or "{@story,subject,id}" in sql)


def _plan_nodes(node: dict):
    yield node
    for child in node.get("Plans", []):
        yield from _plan_nodes(child)


def explain_discovery(conn, queries: list[tuple]) -> dict:
    """EXPLAIN (ANALYZE, BUFFERS) every discovery query of one execution of a read."""
    tops, seq, buffers = set(), 0, 0
    for sql, params in queries:
        with conn.cursor() as cur:
            cur.execute("EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) " + sql, params)
            plan = cur.fetchone()[0][0]["Plan"]
        conn.rollback()
        tops.add(plan["Node Type"])
        seq += any(n["Node Type"] == "Seq Scan" for n in _plan_nodes(plan))
        buffers += plan.get("Shared Hit Blocks", 0) + plan.get("Shared Read Blocks", 0)
    return {"discovery_plans": sorted(tops), "discovery_seq_scans": seq, "discovery_buffers": buffers}


def measure(s: Session, name: str, args: dict) -> dict:
    """Run one read REPEAT times. Besides the records loaded and the wall time, it reports
    the queries the read issued, the time spent in the reference-discovery queries and their
    plans, because those are the queries whose cost the database can tie to table size."""
    store = s.store
    plain_q = Store._q
    discovery: list[float] = []
    issued: list[tuple] = []

    def timed_q(self, sql, params=()):
        t = time.perf_counter()
        try:
            return plain_q(self, sql, params)
        finally:
            issued.append((sql, params))
            if _is_discovery(sql):
                discovery.append(time.perf_counter() - t)

    reads_module.Account = _CountingAccount
    Store._q = timed_q
    try:
        times, loaded, rows, disc = [], None, None, []
        for _ in range(REPEAT):
            _CountingAccount.sizes = []
            discovery.clear()
            issued.clear()
            before = store.loaded_rows
            t0 = time.perf_counter()
            res = s.read(name, args)
            times.append(time.perf_counter() - t0)
            disc.append(sum(discovery))
            rows = store.loaded_rows - before
            loaded = max(_CountingAccount.sizes or [0])
    finally:
        reads_module.Account = Account
        Store._q = plain_q
    if "limitation" in res:
        raise SystemExit(f"{name} returned a limitation: {res}")
    found = [q for q in issued if _is_discovery(q[0])]
    out = {"records_loaded": loaded, "rows_fetched": rows, "queries": len(issued), "discovery_queries": len(found),
           "wall_ms_median": round(statistics.median(times) * 1000, 1), "wall_ms_min": round(min(times) * 1000, 1),
           "discovery_ms_median": round(statistics.median(disc) * 1000, 1)}
    out.update(explain_discovery(store.conn, found))
    out["result_size"] = len(json.dumps(res, default=str))
    return out


def reads_for(p: str) -> list[tuple[str, str, dict]]:
    frame = {"scope": f"{p}project", "cutoff": CUTOFF}
    return [("open_work", "open_work", {"frame": frame}),
            ("story", "story", {"story": f"{p}story-0", "frame": frame})]


def run(dsn: str) -> dict:
    out = {"unrelated_growth": [], "relevant_growth": []}
    with psycopg.connect(dsn) as conn:
        with conn.cursor() as cur:
            cur.execute("SHOW server_version")
            server = cur.fetchone()[0]
        conn.rollback()
        # 1. unrelated scopes grown, relevant fixed
        for n in UNRELATED:
            fresh(conn)
            s = Session(conn)
            write_scope(s, "r-", BASE_DOORS, BASE_HISTORY)
            write_scope(s, "u0-", BASE_DOORS, BASE_HISTORY)
            for k in range(1, n):
                clone_scope(conn, "u0-", f"u{k}-")
            analyze(conn)
            row = {"unrelated_scopes": n, "store": counts(conn)}
            for label, name, args in reads_for("r-"):
                row[label] = measure(s, name, args)
            out["unrelated_growth"].append(row)
            print(json.dumps(row), flush=True)
        # 2. relevant history and fan-out grown, unrelated fixed (10 unrelated scopes)
        for doors, history in RELEVANT:
            fresh(conn)
            s = Session(conn)
            write_scope(s, "u0-", BASE_DOORS, BASE_HISTORY)
            for k in range(1, 10):
                clone_scope(conn, "u0-", f"u{k}-")
            t0 = time.perf_counter()
            write_scope(s, "r-", doors, history)
            analyze(conn)
            row = {"relevant_doors": doors, "relevant_issues_per_door": history, "unrelated_scopes": 10,
                   "write_s": round(time.perf_counter() - t0, 1), "store": counts(conn)}
            for label, name, args in reads_for("r-"):
                row[label] = measure(s, name, args)
            out["relevant_growth"].append(row)
            print(json.dumps(row), flush=True)
    out["environment"] = {"postgresql": server, "image": os.environ.get("ATTEDRA_IMAGE", IMAGE),
                          "python": platform.python_version(), "psycopg": psycopg.__version__,
                          "machine": platform.machine(), "system": platform.system(), "repeat": REPEAT,
                          "normalization_in_every_scope": NORMALIZE}
    return out


def _container() -> tuple[str, str]:
    name = f"attedra-locality-{os.getpid()}"
    port = os.environ.get("ATTEDRA_PG_PORT", "55434")
    subprocess.run(["docker", "run", "--rm", "-d", "--name", name, "-e", "POSTGRES_PASSWORD=attedra",
                    "-e", "POSTGRES_DB=attedra", "-p", f"{port}:5432", IMAGE], check=True, stdout=subprocess.DEVNULL)
    for _ in range(60):
        if subprocess.run(["docker", "exec", name, "pg_isready", "-U", "postgres", "-d", "attedra"],
                          stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0:
            break
        time.sleep(1)
    time.sleep(1)
    return name, f"postgresql://postgres:attedra@localhost:{port}/attedra"


def main() -> int:
    dsn = os.environ.get("ATTEDRA_DSN")
    name = None
    if not dsn:
        name, dsn = _container()
    try:
        result = run(dsn)
    finally:
        if name:
            subprocess.run(["docker", "stop", name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    path = PACKAGE / "scripts" / ("locality_normalized_results.json" if NORMALIZE else "locality_results.json")
    path.write_text(json.dumps(result, indent=1))
    print(f"wrote {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
