"""Scale benchmark of the reference library (9.10.1).

Builds one synthetic project through the library's public API (api.Session), so that story
maintenance (7.2.8) and the recording of begin and end acts (7.6.9) run on every write, and
then times the record-perspective listing reads by the recorded path and by the reference's
derivation switch (Session(conn, derive_listing=True), 7.6.14), and the transition check
(9.5.8) over the scope.

The project, written floor by floor until the target is reached or the write budget is spent:

- a project Item, floors, rooms, and in each room a door, a frame and a hardware set (the
  subjects), connected project -> floor -> room -> subject;
- one issue schedule with three milestones (50% CD, 100% CD, issued for construction), each
  published once, before any statement at it is written;
- four sources: the door schedule (doors and frames), the hardware schedule (hardware sets),
  the specification (doors and half of the hardware sets) and the contractor's submittals;
- every subject issued at the first two milestones, half the doors again at the third;
- conflicts on 10% of subjects (door fire rating, hardware closer), each recorded as a conflict
  story by an explicit detection; some align at the second milestone, some end by withdrawal of
  the specification statement, the rest keep disagreeing, so maintenance records continuations;
- revisions on 10% of subjects (door finish, frame gauge), each recorded as a change story;
- reviews of most change stories: approvals and directives, a directive establishing an
  expectation about the door that the third issue fulfils for half of them; half of the
  directed stories are governed by the fixture ending policy (conformance README §5);
- about 5,000 expectations: a submittal expectation on three quarters of the hardware sets,
  each established by its own instruction, about half fulfilled (some late), and the
  directive expectations;
- withdrawals of specification statements, of reviews (approvals and directives) and of
  expectations.

Every establish act, review and withdrawal names its party, and every detection and review its
frame, as the specification's examples do. An unrelated scope of the same size and shape is then added beside the project.
It is a copy of the project's records made in SQL with every identifier renamed, as
scripts/measure_locality.py makes its unrelated scopes. Its records are exactly those the
library wrote for the project, but they were not written through the API.

Reads at the latest cutoff and at a mid-project cutoff: what_remains, open_stories,
pending_review and open_work, each by the recorded path (median of --repeat runs) and by the
derivation switch (--derive-repeat runs, default one, since it is only a comparison), with a
--cap-s cap per run ("> cap" when exceeded). The recorded and derived answers are compared.
Each recorded read is also run before the unrelated scope is added, and its time and answer
are compared with the same read after. transition_check runs over the scope, and its result
must be empty.

Then a project-wide normalization (7.3.8) is recorded through the API, after the build and
with the unrelated scope in the store: a ``reinterpret`` act targeting the project Item, with
the fixture interpretation ``fixture-fire-rating`` (conformance README §5), effective at an
event after every event of the build and after the mid cutoff. So that it matches open
conflict stories, the door schedule issues ``"1.5 h"`` at 100% CD for the doors with n % 20 ==
10, which keep disagreeing with the specification's ``"90 min"`` literally (a continuation)
and match under that interpretation: 335 open
conflict stories at full size. The write's time, queries and rows, and the stories it ends,
are reported, and then the four listing reads at both cutoffs again (recorded path, median of
--repeat runs; derivation switch once), compared with the reads before it, a few story and
conflicts reads of affected and unaffected doors, and transition_check over the scope. A
sample of statement writes about doors, by a source no story or expectation involves, is
timed before and after the normalization.

The result describes this environment and revision only (spec 11.4); it is not a
performance claim. When the output file exists, its runs are kept under ``previous_runs``,
most recent first.

Usage (starts and removes a disposable container of the pinned image on ATTEDRA_PG_PORT,
default 55581):

    uv run --no-project --python 3.12 --with "psycopg[binary]==3.3.6" python scripts/measure_scale.py

Options: --target-subjects N (default 20000), --min-subjects N (default 10000),
--write-budget-s S (default 2700), --rooms-per-floor N (default 100), --repeat N (default 5),
--derive-repeat N (default 1), --check-repeat N (default 5), --cap-s S (default 300),
--norm-cap-s S (cap on the normalization write, default 3600), --norm-check-repeat N
(default 1), --sample-writes N (default 50), --run-label TEXT, --out PATH (default
scripts/scale_results.json).
"""
from __future__ import annotations

import argparse
import datetime
import gc
import importlib.util
import json
import os
import platform
import resource
import signal
import statistics
import subprocess
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

PACKAGE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PACKAGE / "reference"))

import psycopg  # noqa: E402

from attedra_ref.api import Session  # noqa: E402
from attedra_ref.reads import _strip  # noqa: E402  (the library's own audit comparison, reads.py)
from attedra_ref.store import Store  # noqa: E402

IMAGE = "postgres@sha256:74935e72241653ca55e0414067e6d8763aceb8a810eb51b452253ec3dcfc4336"  # postgres:18 (18.6)
SCHEMA_SQL = (PACKAGE / "reference" / "schema.sql").read_text()

CUTOFF_LATEST = "2026-12-31-07:00"
CUTOFF_MID = "2026-06-10-07:00"
LISTING = ("what_remains", "open_stories", "pending_review", "open_work")
POLICY = {"policy": "fixture-change-closes-with-directive", "policy_version": "1"}

# event times of the synthetic project (all -07:00)
T_M1, T_M2, T_M3 = "2026-03-02T10:00-07:00", "2026-05-04T10:00-07:00", "2026-07-06T10:00-07:00"
T_CONFLICT_DETECT = "2026-03-05T17:00-07:00"
T_CHANGE_DETECT = "2026-05-06T17:00-07:00"
T_ESTABLISH = "2026-05-12T10:00-07:00"
T_REVIEW = "2026-05-20T15:00-07:00"
T_SUB_ON_TIME = "2026-06-01T09:00-07:00"
T_WD_SPEC = "2026-06-05T11:00-07:00"
T_WD_REVIEW = "2026-06-08T11:00-07:00"
T_DEADLINE = "2026-06-15-07:00"
T_WD_EXP = "2026-06-20T11:00-07:00"
T_SUB_LATE = "2026-06-25T09:00-07:00"
T_NORMALIZE = "2026-08-03T10:00-07:00"  # after every event of the build and after CUTOFF_MID
T_SURVEY = "2026-09-01T10:00-07:00"
NORMALIZATION = {"name": "fixture-fire-rating", "version": "1"}  # conformance README §5


# ---------------------------------------------------------------------------------------
# records


def _ev(at: str) -> dict:
    return {"@context": {"role": "event", "at": at}}


def _ref(i: str, c: str, s: str, prop: str | None = None) -> dict:
    r = {"@ref": "assertion", "item": i, "context": c, "source": s}
    if prop:
        r["property"] = prop
    return r


def _item(i: str) -> dict:
    return {"@ref": "item", "id": i}


class Writes:
    """The public API, with the wall time, category and fetched rows of every write."""

    def __init__(self, s: Session) -> None:
        self.s = s
        self.samples: dict[str, list[float]] = defaultdict(list)
        self.rows: dict[str, list[int]] = defaultdict(list)
        self.series: list[tuple[str, float, int]] = []  # (category, seconds, rows) in write order
        self.generated = 0
        self.transition_acts = 0
        self.by_action_generated: Counter = Counter()
        self.by_action_transitions: Counter = Counter()

    def _note(self, cat: str, t0: float, rows0: int) -> None:
        dt = time.perf_counter() - t0
        rows = self.s.store.loaded_rows - rows0
        self.samples[cat].append(dt)
        self.rows[cat].append(rows)
        self.series.append((cat, dt, rows))

    def item(self, iid: str, kind: str, definition: dict | None = None) -> None:
        t0, r0 = time.perf_counter(), self.s.store.loaded_rows
        res = self.s.create_item(iid, kind, None, definition)
        if res["status"] != "created":
            raise SystemExit(f"item {iid}: {res}")
        self._note("item", t0, r0)

    def connect(self, a: str, b: str, at: str) -> None:
        t0, r0 = time.perf_counter(), self.s.store.loaded_rows
        res = self.s.connect(a, b, at)
        if res["status"] != "created":
            raise SystemExit(f"connect {a}->{b}: {res}")
        self._note("connect", t0, r0)

    def assert_(self, i: str, c: str, s: str, values: dict, cat: str | None = None) -> dict:
        cat = cat or (f"act:{values['@action']}" if "@action" in values else "statement")
        t0, r0 = time.perf_counter(), self.s.store.loaded_rows
        res = self.s.assert_(i, c, s, json.dumps(values))
        if res["status"] != "inserted":
            raise SystemExit(f"assert {i}|{c}|{s}: {res}")
        self._note(cat, t0, r0)
        self.generated += len(res["generated"])
        self.transition_acts += len(res["transition_acts"])
        self.by_action_generated[cat] += len(res["generated"])
        self.by_action_transitions[cat] += len(res["transition_acts"])
        return res


class Project:
    """One synthetic project with id prefix ``p`` (README of this script)."""

    def __init__(self, w: Writes, p: str, rooms_per_floor: int) -> None:
        self.w, self.p, self.rpf = w, p, rooms_per_floor
        P = p
        self.project, self.schedule, self.log = f"{P}project", f"{P}arch-schedule", f"{P}issue-log"
        self.m1, self.m2, self.m3 = f"{P}m-50cd", f"{P}m-100cd", f"{P}m-ifc"
        self.a601, self.hws, self.spec, self.sub = f"{P}a-601", f"{P}hw-schedule", f"{P}spec-08", f"{P}submittals"
        self.owner, self.architect, self.contractor = f"{P}owner", f"{P}architect", f"{P}contractor"
        self.e_sub, self.e_dir = f"{P}e-submittal", f"{P}e-directive"
        self.ctx = {k: f"{P}ev-{k}" for k in ("establish", "review", "sub-on-time", "wd-spec", "wd-review",
                                                  "wd-exp", "sub-late")}
        self.minutes = f"{P}minutes"
        self.floors = 0
        self.rooms = 0

    # -- shared records ----------------------------------------------------------------

    def setup(self) -> None:
        w = self.w
        for iid, kind in ((self.project, "project"), (self.schedule, "issue-schedule"), (self.log, "issue-log"),
                          (self.a601, "door-schedule"), (self.hws, "hardware-schedule"),
                          (self.spec, "specification"), (self.sub, "submittal-log"), (self.owner, "party"),
                          (self.architect, "party"), (self.contractor, "party"), (self.minutes, "minutes")):
            w.item(iid, kind)
        for mid, stage, ordinal in ((self.m1, "50% CD", 50), (self.m2, "100% CD", 100), (self.m3, "IFC", 200)):
            w.item(mid, "milestone", {"@context": {"role": "milestone", "schedule": _item(self.schedule),
                                                    "stage": stage, "ordinal": ordinal}})
        w.item(self.e_sub, "expectation-context",
               {"@context": {"role": "expectation", "timing": {"type": "by", "instant": T_DEADLINE}, "fresh": True}})
        w.item(self.e_dir, "expectation-context",
               {"@context": {"role": "expectation", "timing": {"type": "at", "milestone": _item(self.m3)},
                             "fresh": False}})
        for key, at in (("establish", T_ESTABLISH), ("review", T_REVIEW), ("sub-on-time", T_SUB_ON_TIME),
                        ("wd-spec", T_WD_SPEC), ("wd-review", T_WD_REVIEW), ("wd-exp", T_WD_EXP),
                        ("sub-late", T_SUB_LATE)):
            w.item(self.ctx[key], "event", _ev(at))
        # publications first, so that no statement waits for its occurrence time (4.2.4)
        for mid, at in ((self.m1, T_M1), (self.m2, T_M2), (self.m3, T_M3)):
            w.assert_(mid, mid, self.log, {"@published": at, "@distribution": [_item(self.owner), _item(self.contractor)]},
                      cat="publication")

    # -- one floor -----------------------------------------------------------------------

    def frame_(self, cutoff: str, policy: bool = False) -> dict:
        f = {"scope": _item(self.project), "cutoff": cutoff, "perspective": "record",
             "interpretation": None, "interpretation_version": None}
        if policy:
            f.update(POLICY)
        return f

    def floor(self) -> None:
        """Write one floor of rooms, in event order."""
        w, P = self.w, self.p
        f = self.floors
        fl = f"{P}fl-{f}"
        w.item(fl, "floor")
        w.connect(self.project, fl, "2026-02-01-07:00")
        ns = list(range(self.rooms, self.rooms + self.rpf))
        door = {n: f"{P}door-{n}" for n in ns}
        frame = {n: f"{P}frame-{n}" for n in ns}
        hw = {n: f"{P}hw-{n}" for n in ns}
        for n in ns:
            rm = f"{P}rm-{n}"
            w.item(rm, "room")
            w.connect(fl, rm, "2026-02-01-07:00")
            for sid, kind in ((door[n], "door"), (frame[n], "frame"), (hw[n], "hardware-set")):
                w.item(sid, kind)
                w.connect(rm, sid, "2026-02-01-07:00")

        def door_conflict(n):
            return n % 10 in (0, 1)

        def hw_conflict(n):
            return n % 10 == 2

        def door_change(n):
            return n % 10 in (3, 4)

        def frame_change(n):
            return n % 10 == 5

        def directive(n):
            return n % 20 == 13

        def dir_policy(n):
            return (n // 20) % 2 == 0

        def dir_fulfilled(n):
            return (n // 40) % 2 == 0

        def has_sub_exp(n):
            return n % 4 != 0

        # 50% CD: door schedule, hardware schedule, specification
        for n in ns:
            w.assert_(door[n], self.m1, self.a601, {"finish": "paint", "fire_rating": "60 min", "width": 900})
            w.assert_(frame[n], self.m1, self.a601, {"material": "hollow metal", "gauge": 16})
            w.assert_(hw[n], self.m1, self.hws, {"set": "HW-01", "closer": "surface"})
            w.assert_(door[n], self.m1, self.spec, {"fire_rating": "90 min" if door_conflict(n) else "60 min"})
            if n % 2 == 0:
                w.assert_(hw[n], self.m1, self.spec, {"closer": "concealed" if hw_conflict(n) else "surface"})
        # conflict stories (10% of subjects)
        for n in ns:
            for cond, subj, prop, a_src in ((door_conflict(n), door[n], "fire_rating", self.a601),
                                            (hw_conflict(n), hw[n], "closer", self.hws)):
                if not cond:
                    continue
                st = f"{P}cs-{n}-{prop}"
                w.item(st, "story")
                w.item(f"{st}/d1", "event", _ev(T_CONFLICT_DETECT))
                w.assert_(st, f"{st}/d1", st, {
                    "@action": "detect",
                    "@story": {"kind": "conflict", "subject": _item(subj), "property": prop},
                    "@basis": [_ref(subj, self.m1, a_src, prop), _ref(subj, self.m1, self.spec, prop)],
                    "@frame": self.frame_(T_CONFLICT_DETECT)})
        # 100% CD: every subject re-issued; door finish and frame gauge revised on 10%; some
        # conflicts align
        f2 = {n: ("stain" if door_change(n) else "paint") for n in ns}
        # 7.2.5: where a side issues a different value and the sides still disagree, maintenance
        # records a continuation detection. "1.5 h" disagrees with "90 min" literally and
        # matches it under fixture-fire-rating, so the normalization ends those stories
        fr2 = {n: ("90 min" if n % 20 == 0 else "1.5 h" if n % 20 == 10 else "60 min") for n in ns}
        cl2 = {n: ("concealed" if n % 20 == 2 else "floor" if n % 20 == 12 else "surface") for n in ns}
        for n in ns:
            w.assert_(door[n], self.m2, self.a601, {"finish": f2[n], "fire_rating": fr2[n], "width": 900})
            w.assert_(frame[n], self.m2, self.a601, {"material": "hollow metal", "gauge": 14 if frame_change(n) else 16})
            w.assert_(hw[n], self.m2, self.hws, {"set": "HW-01", "closer": cl2[n]})
        # change stories (10% of subjects)
        for n in ns:
            for cond, subj, prop in ((door_change(n), door[n], "finish"), (frame_change(n), frame[n], "gauge")):
                if not cond:
                    continue
                st = f"{P}ch-{n}-{prop}"
                prior, new = _ref(subj, self.m1, self.a601), _ref(subj, self.m2, self.a601)
                w.item(st, "story")
                w.item(f"{st}/d1", "event", _ev(T_CHANGE_DETECT))
                w.assert_(st, f"{st}/d1", st, {
                    "@action": "detect", "@story": {"kind": "change", "subject": _item(subj)},
                    "@transitions": [{"property": prop, "transition": "changed", "prior": prior, "new": new}],
                    "@basis": [prior, new],
                    "@frame": self.frame_(T_CHANGE_DETECT, policy=directive(n) and dir_policy(n))})
        # submittal expectations, each established by its own instruction
        for n in ns:
            if not has_sub_exp(n):
                continue
            w.assert_(hw[n], self.e_sub, self.sub, {"set": "HW-01"}, cat="expectation")
            ins = f"{P}instr-{n}"
            w.item(ins, "instruction")
            w.assert_(ins, self.ctx["establish"], self.minutes, {
                "@action": "establish", "@targets": [_ref(hw[n], self.e_sub, self.sub)], "@party": _item(self.owner)})
        # reviews: approvals of door and frame revisions, directives on doors
        for n in ns:
            for cond, subj, prop, outcome in ((n % 20 == 3, door[n], "finish", "no_change"),
                                              (directive(n), door[n], "finish", "change_required"),
                                              (n % 20 == 5, frame[n], "gauge", "no_change")):
                if not cond:
                    continue
                st = f"{P}ch-{n}-{prop}"
                values = {"@action": "review", "@targets": [_ref(st, f"{st}/d1", st)], "@outcome": outcome,
                          "@basis": [_ref(subj, self.m1, self.a601), _ref(subj, self.m2, self.a601)],
                          "@party": _item(self.owner), "@frame": self.frame_(T_REVIEW)}
                if outcome == "change_required":
                    w.assert_(subj, self.e_dir, self.a601, {"finish": "lacquer"}, cat="expectation")
                    values["@establishes"] = [_ref(subj, self.e_dir, self.a601)]
                rv = f"{P}rv-{n}-{prop}"
                w.item(rv, "decision")
                w.assert_(rv, self.ctx["review"], self.minutes, values)
        # submittals: on time, late, or none (half of the submittal expectations fulfilled)
        for n in ns:
            if n % 8 in (1, 5):
                w.assert_(hw[n], self.ctx["sub-on-time"], self.sub, {"set": "HW-01"})
        # withdrawals of specification statements (those conflicts end by withdrawal)
        for n in ns:
            if n % 20 == 11:
                wd = f"{P}wd-spec-{n}"
                w.item(wd, "withdrawal")
                w.assert_(wd, self.ctx["wd-spec"], self.minutes, {
                    "@action": "withdraw", "@targets": [_ref(door[n], self.m1, self.spec)], "@party": _item(self.architect)})
        # withdrawals of reviews: approvals (the change story reopens) and directives
        for n in ns:
            for cond, prop in ((n % 100 == 3, "finish"), (n % 100 == 5, "gauge"), (n % 200 == 13, "finish")):
                if not cond:
                    continue
                rv = f"{P}rv-{n}-{prop}"
                wd = f"{P}wd-rv-{n}-{prop}"
                w.item(wd, "withdrawal")
                w.assert_(wd, self.ctx["wd-review"], self.minutes, {
                    "@action": "withdraw", "@targets": [_ref(rv, self.ctx["review"], self.minutes)],
                    "@party": _item(self.owner)})
        # withdrawals of expectations
        for n in ns:
            if n % 16 == 7:
                wd = f"{P}wd-exp-{n}"
                w.item(wd, "withdrawal")
                w.assert_(wd, self.ctx["wd-exp"], self.minutes, {
                    "@action": "withdraw", "@targets": [_ref(hw[n], self.e_sub, self.sub)], "@party": _item(self.owner)})
        for n in ns:
            if n % 8 == 2:
                w.assert_(hw[n], self.ctx["sub-late"], self.sub, {"set": "HW-01"})
        # issued for construction: half of the doors; half of the directives fulfilled
        for n in ns:
            if n % 2 == 1:
                fin = "lacquer" if directive(n) and dir_fulfilled(n) else f2[n]
                w.assert_(door[n], self.m3, self.a601, {"finish": fin, "fire_rating": fr2[n], "width": 900})
        self.floors += 1
        self.rooms += self.rpf

    @property
    def subjects(self) -> int:
        return 3 * self.rooms


# ---------------------------------------------------------------------------------------
# store helpers


def fresh(conn) -> None:
    with conn.cursor() as cur:
        cur.execute("DROP SCHEMA IF EXISTS public CASCADE")
        cur.execute("CREATE SCHEMA public")
        cur.execute(SCHEMA_SQL)
    conn.commit()


def analyze(conn) -> None:
    with conn.cursor() as cur:
        cur.execute("ANALYZE")
    conn.commit()


def clone_scope(conn, src: str, dst: str) -> None:
    """Copy every record whose identifiers carry prefix ``src`` under prefix ``dst``, as
    scripts/measure_locality.py does: the prefix is also renamed after ``exp:`` (the Items of
    an expectation property's acts, and the contexts of those held on a story, README §7) and
    after ``/`` in identifiers and in the values that reference them."""
    def ren(expr: str) -> str:
        return (f"replace(replace(CASE WHEN starts_with({expr}, %(src)s) THEN %(dst)s || substr({expr}, %(n)s) "
                f"ELSE {expr} END, 'exp:' || %(src)s, 'exp:' || %(dst)s), '/' || %(src)s, '/' || %(dst)s)")

    def ren_json(expr: str) -> str:
        # `exp:` is renamed wherever it occurs: at the start of an expectation property's act
        # Item, and after `/` in the contexts of acts held on a story (README §7)
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


def store_counts(conn, prefix: str | None = None) -> dict:
    out = {}
    with conn.cursor() as cur:
        if prefix is None:
            for t in ("items", "assertions", "connections"):
                cur.execute(f"SELECT count(*) FROM {t}")
                out[t] = cur.fetchone()[0]
        else:
            like = (prefix, "exp:" + prefix)
            cur.execute("SELECT count(*) FROM items WHERE starts_with(id, %s) OR starts_with(id, %s)", like)
            out["items"] = cur.fetchone()[0]
            cur.execute("SELECT count(*) FROM assertions WHERE starts_with(item_id, %s) OR starts_with(item_id, %s)", like)
            out["assertions"] = cur.fetchone()[0]
            cur.execute("SELECT count(*) FROM connections WHERE starts_with(from_id, %s)", (prefix,))
            out["connections"] = cur.fetchone()[0]
        cur.execute("SELECT pg_database_size(current_database())")
        out["database_bytes"] = cur.fetchone()[0]
    conn.rollback()
    return out


def record_census(conn, prefix: str) -> dict:
    """What the project holds, counted in SQL over the stored records."""
    like = (prefix, "exp:" + prefix)
    q = {
        "acts_by_action": """SELECT coalesce("values"->>'@action', '') AS a, count(*) FROM assertions
                              WHERE (starts_with(item_id, %s) OR starts_with(item_id, %s)) GROUP BY a ORDER BY a""",
        "end_acts_by_cause": """SELECT coalesce("values"->'@period'->>'cause', 'null')
                                   || CASE WHEN "values"->'@period'->'policy' IS NULL
                                             OR jsonb_typeof("values"->'@period'->'policy') = 'null'
                                           THEN '' ELSE ' (policy)' END AS c, count(*)
                                FROM assertions WHERE (starts_with(item_id, %s) OR starts_with(item_id, %s))
                                  AND "values"->>'@action' = 'end' GROUP BY c ORDER BY c""",
        "begin_acts_by_cause": """SELECT coalesce("values"->'@period'->>'cause', 'null') AS c, count(*)
                                  FROM assertions WHERE (starts_with(item_id, %s) OR starts_with(item_id, %s))
                                    AND "values"->>'@action' = 'begin' GROUP BY c ORDER BY c""",
        "reconciliations_by_outcome": """SELECT "values"->>'@outcome' AS o, count(*) FROM assertions
                                         WHERE (starts_with(item_id, %s) OR starts_with(item_id, %s))
                                           AND "values"->>'@action' = 'reconcile' GROUP BY o ORDER BY o""",
        "items_by_kind": """SELECT kind, count(*) FROM items WHERE starts_with(id, %s) OR starts_with(id, %s)
                            GROUP BY kind ORDER BY kind""",
    }
    out = {}
    with conn.cursor() as cur:
        for k, sql in q.items():
            cur.execute(sql, like)
            out[k] = {r[0]: r[1] for r in cur.fetchall()}
        cur.execute("""SELECT count(*) FROM assertions a JOIN items c ON c.id = a.context_id
                       WHERE starts_with(a.item_id, %s) AND NOT a."values" ? '@action'
                         AND coalesce(c.definition->'@context'->>'role', '') <> 'expectation'
                         AND NOT a."values" ? '@published'""", (prefix,))
        out["statements"] = cur.fetchone()[0]
        cur.execute("""SELECT count(*) FROM assertions a JOIN items c ON c.id = a.context_id
                       WHERE starts_with(a.item_id, %s) AND c.definition->'@context'->>'role' = 'expectation'""",
                    (prefix,))
        out["expectations"] = cur.fetchone()[0]
        cur.execute("""SELECT "values"->'@story'->>'kind' AS k, count(DISTINCT item_id) FROM assertions
                       WHERE starts_with(item_id, %s) AND "values"->>'@action' = 'detect' GROUP BY k ORDER BY k""",
                    (prefix,))
        out["stories_by_kind"] = {r[0]: r[1] for r in cur.fetchall()}
        cur.execute("""SELECT count(DISTINCT item_id) FROM assertions
                       WHERE starts_with(item_id, %s) AND "values"->>'@action' = 'detect'
                         AND "values"->'@frame'->>'policy' IS NOT NULL""", (prefix,))
        out["stories_under_fixture_policy"] = cur.fetchone()[0]
    conn.rollback()
    return out


# ---------------------------------------------------------------------------------------
# reads


class Capped(Exception):
    pass


def _on_alarm(signum, frame):
    raise Capped()


def _stats(xs: list[float]) -> dict:
    xs = sorted(xs)
    if not xs:
        return {"n": 0}
    p95 = xs[min(len(xs) - 1, max(0, round(0.95 * len(xs)) - 1))]
    return {"n": len(xs), "median_ms": round(statistics.median(xs) * 1000, 2), "p95_ms": round(p95 * 1000, 2),
            "max_ms": round(xs[-1] * 1000, 2), "total_s": round(sum(xs), 1)}


def _frame_interp(res: dict) -> dict:
    """The resolved frame's interpretation members (4.6.1, README §5 *Resolved frame*)."""
    f = res.get("frame") or {}
    return {k: f.get(k) for k in ("interpretation", "normalization") if k in f}


def summarize(name: str, res: dict) -> dict:
    """Sizes of a listing result, to show what was read."""
    if "limitation" in res:
        return {"limitation": res["limitation"]}
    if name == "what_remains":
        return {"counts": res.get("counts"), **{k: len(res.get(k) or []) for k in
                                                ("open", "upcoming", "superseded", "ambiguous", "limitations")},
                "frame": _frame_interp(res)}
    if name in ("open_stories", "pending_review"):
        return {"count": res.get("count"), **{k: len(res.get(k) or []) for k in ("superseded", "ambiguous", "limitations")},
                "frame": _frame_interp(res)}
    if name == "open_work":
        return {**{k: len(res.get(k) or []) for k in ("open", "upcoming", "ambiguous", "limitations")},
                "frame": _frame_interp(res)}
    if name == "transition_check":
        return {"differences": len(res.get("differences") or []), "unverified": len(res.get("unverified") or [])}
    return {}


def _listed(name: str, res: dict) -> dict:
    """The entries a listing result lists, by list and key, to compare two results."""
    out: dict = {}
    lists = {"what_remains": ("open", "upcoming", "superseded", "ambiguous", "limitations"),
             "open_work": ("open", "upcoming", "ambiguous", "limitations"),
             "open_stories": ("stories", "superseded", "ambiguous", "limitations"),
             "pending_review": ("stories", "superseded", "ambiguous", "limitations")}[name]
    for k in lists:
        for e in res.get(k) or []:
            if isinstance(e, str):
                key = e
            elif "unit" in e:
                key = f"{e.get('kind')}:{json.dumps(e['unit'], sort_keys=True)}"
            else:
                key = json.dumps(e.get("expectation"), sort_keys=True)
            out[(k, key)] = e
    return out


def compare_listing(name: str, before: dict, after: dict) -> dict:
    """What a listing read gives after the normalization, against the same read before it."""
    b, a = _listed(name, before), _listed(name, after)
    gone = sorted(set(b) - set(a))
    new = sorted(set(a) - set(b))
    changed = [k for k in set(a) & set(b) if a[k] != b[k]]
    keys: Counter = Counter()
    for k in changed:
        x, y = b[k], a[k]
        if isinstance(x, dict) and isinstance(y, dict):
            for m in set(x) | set(y):
                if x.get(m, "~absent") != y.get(m, "~absent"):
                    keys[m] += 1
    by_list = Counter(k for k, _ in gone)
    return {"same_result": before == after, "frame_before": _frame_interp(before), "frame_after": _frame_interp(after),
            "entries_removed": len(gone), "entries_removed_by_list": dict(by_list),
            "entries_added": len(new), "entries_added_sample": [k for _l, k in new[:5]],
            "entries_changed": len(changed), "changed_members": dict(keys),
            "removed": [k for _l, k in gone]}


class Reads:
    def __init__(self, dsn: str, repeat: int, cap_s: int) -> None:
        self.dsn, self.repeat, self.cap_s = dsn, repeat, cap_s
        self.conn = None
        self._connect()

    def _connect(self) -> None:
        if self.conn is not None:
            try:
                self.conn.close()
            except Exception:
                pass
        self.conn = psycopg.connect(self.dsn)
        self.recorded = Session(self.conn)
        self.derived = Session(self.conn, derive_listing=True)

    def run(self, name: str, args: dict, derive: bool, repeat: int | None = None) -> tuple[dict, dict | None]:
        """Run one read ``repeat`` times; each run is capped. Reports the median, the queries
        and rows of the first run and the peak memory of this process."""
        s = self.derived if derive else self.recorded
        repeat = repeat or self.repeat
        times: list[float] = []
        res = None
        queries = rows = None
        plain_q = Store._q
        count = [0]

        def counting_q(self_, sql, params=()):
            count[0] += 1
            return plain_q(self_, sql, params)

        for k in range(repeat):
            gc.collect()
            count[0] = 0
            rows0 = s.store.loaded_rows
            Store._q = counting_q
            signal.signal(signal.SIGALRM, _on_alarm)
            signal.alarm(self.cap_s)
            t0 = time.perf_counter()
            try:
                res = s.read(name, args)
                dt = time.perf_counter() - t0
            except Capped:
                dt = time.perf_counter() - t0
                signal.alarm(0)
                Store._q = plain_q
                self._connect()
                out = {"runs": k + 1, "capped": True, "cap_s": self.cap_s, "result": "> cap",
                       "completed_runs_ms": [round(x * 1000, 1) for x in times], "capped_after_s": round(dt, 1)}
                print(json.dumps({"read": name, "derive": derive, **out}), flush=True)
                return out, None
            finally:
                signal.alarm(0)
                Store._q = plain_q
            times.append(dt)
            if k == 0:
                queries, rows = count[0], s.store.loaded_rows - rows0
            print(json.dumps({"read": name, "derive": derive, "run": k + 1, "s": round(dt, 2)}), flush=True)
        out = {"runs": len(times), "capped": False, "median_ms": round(statistics.median(times) * 1000, 1),
               "min_ms": round(min(times) * 1000, 1), "max_ms": round(max(times) * 1000, 1),
               "queries": queries, "rows_fetched": rows, "result": summarize(name, res),
               "peak_rss_mb": round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / (1024 * 1024), 0)}
        return out, res


def _comparable(res: dict | None):
    """A result without the members only one path can give: the recorded acts (``act``,
    ``revised_by``) and the resolved frame, as the library's own self-check compares them."""
    return None if res is None else _strip(res)


# ---------------------------------------------------------------------------------------
# the normalization


def timed(s: Session, fn, cap_s: int):
    """Run one operation on ``s`` with a cap; report its time, the queries it issued
    (``Store._q``) and the rows it fetched. Returns (result or None when capped, report)."""
    plain_q = Store._q
    count = [0]

    def counting_q(self_, sql, params=()):
        count[0] += 1
        return plain_q(self_, sql, params)

    gc.collect()
    rows0 = s.store.loaded_rows
    Store._q = counting_q
    signal.signal(signal.SIGALRM, _on_alarm)
    signal.alarm(cap_s)
    t0 = time.perf_counter()
    res, capped = None, False
    try:
        res = fn()
    except Capped:
        capped = True
    finally:
        dt = time.perf_counter() - t0
        signal.alarm(0)
        Store._q = plain_q
    return res, {"s": round(dt, 3), "queries": count[0], "rows_fetched": s.store.loaded_rows - rows0,
                 "capped": capped, "cap_s": cap_s,
                 "peak_rss_mb": round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / (1024 * 1024), 0)}


def statement_sample(s: Session, doors: list[str], label: str) -> dict:
    """Statement writes about doors by a source that no story or expectation involves, at an
    event after the normalization's effective time: what a statement write costs with and
    without a normalization in force for its subject (7.3.8, 9.10.1)."""
    src, ctx = "r-survey", "r-ev-survey"
    for iid, kind, d in ((src, "survey", None), (ctx, "event", _ev(T_SURVEY))):
        if s.create_item(iid, kind, None, d)["status"] not in ("created", "exists"):
            raise SystemExit(f"item {iid}")
    times, rows, acts = [], [], 0
    for d in doors:
        res, rep = timed(s, lambda d=d: s.assert_(d, ctx, src, json.dumps({"hardware_prep": label})), 60)
        if res is None or res["status"] != "inserted":
            raise SystemExit(f"sample write {d}: {res} {rep}")
        times.append(rep["s"])
        rows.append(rep["rows_fetched"])
        acts += len(res["transition_acts"]) + len(res["generated"])
    return {"n": len(times), "median_ms": round(statistics.median(times) * 1000, 2),
            "p95_ms": _stats(times)["p95_ms"], "max_ms": round(max(times) * 1000, 2),
            "rows_fetched_median": statistics.median(rows), "rows_fetched_max": max(rows),
            "records_maintenance_wrote": acts}


def normalization_phase(dsn: str, opts, proj_rooms: int, before: dict) -> dict:
    """A project-wide normalization recorded after the build (7.3.8): its write, the stories
    it ends, and the listing reads after it against ``before`` (the same reads, recorded path,
    before it)."""
    out: dict = {"act": None, "interpretation": NORMALIZATION, "effective": T_NORMALIZE}
    conn = psycopg.connect(dsn)
    s = Session(conn)
    # doors whose conflict stories match under the interpretation and are open at T
    expected = sorted(f"r-cs-{n}-fire_rating" for n in range(proj_rooms) if n % 20 == 10)
    out["expected_to_end"] = {"stories": len(expected), "which": "the door fire-rating conflict stories with n % 20 "
                                                                 "== 10: \"1.5 h\" (door schedule, 100% CD) against "
                                                                 "\"90 min\" (specification, 50% CD)"}
    sample_doors = [f"r-door-{n}" for n in range(0, proj_rooms, max(1, proj_rooms // opts.sample_writes))][:opts.sample_writes]
    after_doors = [f"r-door-{n}" for n in range(1, proj_rooms, max(1, proj_rooms // opts.sample_writes))][:opts.sample_writes]
    out["statement_writes_before"] = statement_sample(s, sample_doors, "standard")
    print(json.dumps({"statement_writes_before": out["statement_writes_before"]}), flush=True)

    norm, ctx, src = "r-norm-1", "r-ev-normalize", "r-minutes"
    s.create_item(norm, "normalization")
    s.create_item(ctx, "event", None, _ev(T_NORMALIZE))
    values = {"@action": "reinterpret", "@targets": [_item("r-project")], "@interpretation": NORMALIZATION,
              "@basis": [{"@ref": "artifact", "id": "minutes-2026-08-03.pdf", "edition": "issued 2026-08-03"}],
              "@party": _item("r-owner")}
    out["act"] = {"ref": f"{norm}|{ctx}|{src}", "values": values}
    res, rep = timed(s, lambda: s.assert_(norm, ctx, src, json.dumps(values)), opts.norm_cap_s)
    out["write"] = rep
    print(json.dumps({"normalization_write": rep}), flush=True)
    if res is None:
        conn.close()
        out["note"] = "the write reached its cap and was rolled back; nothing after it was measured"
        return out
    out["write"].update({"status": res["status"], "generated": len(res["generated"]),
                         "transition_acts": len(res["transition_acts"])})
    # what it recorded, read back from the store
    triples = [r.split("|") for r in res["transition_acts"]]
    by: Counter = Counter()
    ended: set[str] = set()
    with conn.cursor() as cur:
        for i, c, so in triples:
            cur.execute('SELECT "values"::text FROM assertions WHERE item_id = %s AND context_id = %s AND source_id = %s',
                        (i, c, so))
            v = json.loads(cur.fetchone()[0])
            per = v.get("@period") or {}
            key = f"{v.get('@action')}:{per.get('cause') if isinstance(per, dict) else per}"
            by[key] += 1
            if v.get("@action") == "end" and isinstance(per, dict) and per.get("cause") == "normalization":
                ended.add(i)
    conn.rollback()
    out["recorded"] = {"by_action_and_cause": dict(sorted(by.items())), "stories_ended_by_normalization": len(ended),
                       "equals_expected": sorted(ended) == expected,
                       "unexpected": sorted(ended - set(expected))[:10], "missing": sorted(set(expected) - ended)[:10]}
    print(json.dumps({"normalization_recorded": out["recorded"]}), flush=True)
    t0 = time.perf_counter()
    analyze(conn)
    out["analyze_after_s"] = round(time.perf_counter() - t0, 1)
    conn.close()

    # the listing reads after it, against the same reads before it
    r = Reads(dsn, opts.repeat, opts.cap_s)
    reads: dict = {}
    for label, cutoff in (("latest", CUTOFF_LATEST), ("mid", CUTOFF_MID)):
        reads[label] = {}
        for name in LISTING:
            args = {"frame": {"scope": "r-project", "cutoff": cutoff}}
            rec, rres = r.run(name, args, derive=False)
            der, dres = r.run(name, args, derive=True, repeat=opts.derive_repeat)
            entry: dict = {"recorded": rec, "derived": der}
            if dres is not None:
                entry["derived_equals_recorded"] = _comparable(rres) == _comparable(dres)
            b = before.get((label, name))
            if b is not None and rres is not None:
                cmp_ = compare_listing(name, b, rres)
                removed = cmp_.pop("removed")
                story_removed = sorted(k.split(":", 1)[1].strip('"') if ":" in k else k for k in removed)
                cmp_["removed_are_the_normalized_stories"] = (
                    sorted(set(story_removed)) == expected if label == "latest" and name != "open_work" else None)
                cmp_["removed_sample"] = removed[:3]
                entry["against_before"] = cmp_
            reads[label][name] = entry
            print(json.dumps({"after_normalization": label, "read": name,
                              **{k: v for k, v in entry.items() if k != "against_before"},
                              "against_before": {k: v for k, v in (entry.get("against_before") or {}).items()
                                                 if k != "removed_sample"}}), flush=True)
            del rres, dres
            gc.collect()
    out["reads_after"] = reads

    # single reads of an ended story, a story that still disagrees, and a matched door
    spot: dict = {}
    for key, read, args in (
            ("normalized_story_latest", "story", {"story": "r-cs-10-fire_rating", "frame": {"scope": "r-project", "cutoff": CUTOFF_LATEST}}),
            ("normalized_story_mid", "story", {"story": "r-cs-10-fire_rating", "frame": {"scope": "r-project", "cutoff": CUTOFF_MID}}),
            ("disagreeing_story_latest", "story", {"story": "r-cs-1-fire_rating", "frame": {"scope": "r-project", "cutoff": CUTOFF_LATEST}}),
            ("matched_door_conflicts_latest", "conflicts", {"subject": "r-door-10", "frame": {"scope": "r-project", "cutoff": CUTOFF_LATEST}})):
        t0 = time.perf_counter()
        res = r.recorded.read(read, args)
        dt = time.perf_counter() - t0
        keep = ("standing", "ending", "baseline_ending", "interval", "interpretation", "normalization") if read == "story" \
            else ("conflicts", "matched", "interpretation")
        spot[key] = {"ms": round(dt * 1000, 1), **{k: res.get(k) for k in keep if k in res}}
        if read == "story":
            spot[key]["periods"] = [{"end": (p.get("end") or {}).get("cause") if isinstance(p.get("end"), dict) else p.get("end")}
                                    for p in res.get("periods") or []]
    out["spot_reads"] = spot
    print(json.dumps({"spot_reads": spot}), flush=True)

    tc, tres = r.run("transition_check", {"frame": {"scope": "r-project", "cutoff": CUTOFF_LATEST}}, derive=False,
                     repeat=opts.norm_check_repeat)
    tc["empty"] = (tres is not None and not tres.get("differences") and not tres.get("unverified"))
    if tres is not None and tres.get("differences"):
        tc["first_differences"] = tres["differences"][:5]
    out["transition_check_after"] = tc
    print(json.dumps({"transition_check_after_normalization": tc}), flush=True)
    r.conn.close()

    conn = psycopg.connect(dsn)
    s = Session(conn)
    out["statement_writes_after"] = statement_sample(s, after_doors, "standard")
    print(json.dumps({"statement_writes_after": out["statement_writes_after"]}), flush=True)
    conn.close()
    return out


# ---------------------------------------------------------------------------------------
# run


def run(dsn: str, opts) -> dict:
    out: dict = {"measurement": "Attedra 0.1.0 scale measurement, with a project-wide normalization (CONFORMANCE.md section 4)",
                 "parameters": {
                     "target_subjects": opts.target_subjects, "min_subjects": opts.min_subjects,
                     "write_budget_s": opts.write_budget_s, "rooms_per_floor": opts.rooms_per_floor,
                     "read_repeat": opts.repeat, "derive_repeat": opts.derive_repeat, "read_cap_s": opts.cap_s,
                     "check_repeat": opts.check_repeat, "normalization_cap_s": opts.norm_cap_s,
                     "normalization_check_repeat": opts.norm_check_repeat, "sample_writes": opts.sample_writes,
                     "cutoffs": {"latest": CUTOFF_LATEST, "mid": CUTOFF_MID}}}
    conn = psycopg.connect(dsn)
    with conn.cursor() as cur:
        cur.execute("SHOW server_version")
        server = cur.fetchone()[0]
    conn.rollback()
    fresh(conn)
    s = Session(conn)
    w = Writes(s)
    proj = Project(w, "r-", opts.rooms_per_floor)

    # 1. the project, through the API, floor by floor
    t_start = time.perf_counter()
    proj.setup()
    floors = []
    reason = None
    while True:
        t0 = time.perf_counter()
        n0 = len(w.series)
        proj.floor()
        dt = time.perf_counter() - t0
        elapsed = time.perf_counter() - t_start
        ser = w.series[n0:]
        st = [x[1] for x in ser if x[0] == "statement"]
        acts = [x[1] for x in ser if x[0].startswith("act:")]
        fl = {"floor": proj.floors, "subjects": proj.subjects, "floor_s": round(dt, 1), "elapsed_s": round(elapsed, 1),
              "writes": len(ser), "statement_median_ms": round(statistics.median(st) * 1000, 2) if st else None,
              "act_median_ms": round(statistics.median(acts) * 1000, 2) if acts else None,
              "act_rows_median": statistics.median([x[2] for x in ser if x[0].startswith("act:")]) if acts else None}
        floors.append(fl)
        print(json.dumps(fl), flush=True)
        if proj.subjects >= opts.target_subjects:
            reason = "target reached"
            break
        if elapsed >= opts.write_budget_s and proj.subjects >= opts.min_subjects:
            reason = "write budget spent"
            break
    setup_s = time.perf_counter() - t_start
    out["build"] = {"subjects": proj.subjects, "rooms": proj.rooms, "floors": proj.floors,
                    "target_reached": proj.subjects >= opts.target_subjects, "stopped_because": reason,
                    "setup_s": round(setup_s, 1), "per_floor": floors}

    # per-write cost by category, and statements against acts
    cats = {c: {**_stats(v), "rows_fetched_median": statistics.median(w.rows[c]),
                "rows_fetched_max": max(w.rows[c]), "generated": w.by_action_generated.get(c, 0),
                "transition_acts": w.by_action_transitions.get(c, 0)} for c, v in sorted(w.samples.items())}
    acts_all = [x for c, v in w.samples.items() if c.startswith("act:") for x in v]
    out["write_cost"] = {
        "statements": cats.get("statement"),
        "acts": {**_stats(acts_all), "rows_fetched_median": statistics.median(
            [x for c, v in w.rows.items() if c.startswith("act:") for x in v])},
        "by_category": cats,
        "generated_records": w.generated, "transition_acts_recorded": w.transition_acts}
    # cost over the build, in tenths of the write sequence
    tenths = []
    stmts = [(i, x) for i, x in enumerate(w.series) if x[0] == "statement"]
    acts_seq = [(i, x) for i, x in enumerate(w.series) if x[0].startswith("act:")]
    for k in range(10):
        a = stmts[k * len(stmts) // 10:(k + 1) * len(stmts) // 10]
        b = acts_seq[k * len(acts_seq) // 10:(k + 1) * len(acts_seq) // 10]
        tenths.append({"tenth": k + 1,
                       "statement_median_ms": round(statistics.median([x[1] for _i, x in a]) * 1000, 2) if a else None,
                       "statement_rows_median": statistics.median([x[2] for _i, x in a]) if a else None,
                       "act_median_ms": round(statistics.median([x[1] for _i, x in b]) * 1000, 2) if b else None,
                       "act_p95_ms": _stats([x[1] for _i, x in b]).get("p95_ms") if b else None,
                       "act_rows_median": statistics.median([x[2] for _i, x in b]) if b else None})
    out["write_cost"]["over_the_build"] = tenths
    out["census_relevant"] = record_census(conn, "r-")
    out["store_relevant"] = store_counts(conn, "r-")
    print(json.dumps({"census": out["census_relevant"], "store": out["store_relevant"]}), flush=True)
    del w.series
    gc.collect()
    analyze(conn)
    conn.close()

    # every recorded read before the unrelated scope exists, to compare with the same reads after
    r = Reads(dsn, opts.repeat, opts.cap_s)
    latest = {"frame": {"scope": "r-project", "cutoff": CUTOFF_LATEST}}
    before_reads: dict = {}
    for label, cutoff in (("latest", CUTOFF_LATEST), ("mid", CUTOFF_MID)):
        for name in LISTING:
            b, bres = r.run(name, {"frame": {"scope": "r-project", "cutoff": cutoff}}, derive=False)
            before_reads[(label, name)] = (b, bres)
    before, before_res = before_reads[("latest", "what_remains")]
    r.conn.close()

    # 2. the unrelated scope: a renamed copy in SQL
    conn = psycopg.connect(dsn)
    t0 = time.perf_counter()
    clone_scope(conn, "r-", "u-")
    analyze(conn)
    out["unrelated_scope"] = {"how": "SQL copy of the project's records with the prefix r- renamed u- (not written "
                                     "through the API)", "copy_and_analyze_s": round(time.perf_counter() - t0, 1),
                              "store": store_counts(conn, "u-")}
    out["store_total"] = store_counts(conn)
    print(json.dumps({"store_total": out["store_total"]}), flush=True)
    conn.close()

    # 3. reads
    r = Reads(dsn, opts.repeat, opts.cap_s)
    after, after_res = r.run("what_remains", latest, derive=False, repeat=1)
    out["unrelated_scope"]["what_remains_latest_before_and_after"] = {
        "before": {k: before.get(k) for k in ("median_ms", "queries", "rows_fetched", "result")},
        "after": {k: after.get(k) for k in ("median_ms", "queries", "rows_fetched", "result")},
        "same_result": before_res is not None and before_res == after_res}
    del before_res, after_res
    reads = {}
    before_after = {}
    kept: dict = {}  # the recorded answers, compared with the same reads after the normalization
    for label, cutoff in (("latest", CUTOFF_LATEST), ("mid", CUTOFF_MID)):
        reads[label] = {}
        before_after[label] = {}
        for name in LISTING:
            args = {"frame": {"scope": "r-project", "cutoff": cutoff}}
            rec, rres = r.run(name, args, derive=False)
            # the derivation switch is only a comparison: one run per read
            der, dres = r.run(name, args, derive=True, repeat=opts.derive_repeat)
            entry = {"recorded": rec, "derived": der}
            if dres is not None:
                entry["derived_equals_recorded"] = _comparable(rres) == _comparable(dres)
            reads[label][name] = entry
            b, bres = before_reads.pop((label, name))
            before_after[label][name] = {
                "before_ms": b.get("median_ms"), "after_ms": rec.get("median_ms"),
                "before_queries": b.get("queries"), "after_queries": rec.get("queries"),
                "before_rows_fetched": b.get("rows_fetched"), "after_rows_fetched": rec.get("rows_fetched"),
                "same_result": bres is not None and rres is not None
                and {k: v for k, v in bres.items() if k != "frame"} == {k: v for k, v in rres.items() if k != "frame"}}
            print(json.dumps({"cutoff": label, "read": name, **entry, "before_after": before_after[label][name]}),
                  flush=True)
            kept[(label, name)] = rres
            del rres, dres, bres
            gc.collect()
    out["reads"] = reads
    out["unrelated_scope"]["reads_before_and_after"] = before_after
    tc, tres = r.run("transition_check", {"frame": {"scope": "r-project", "cutoff": CUTOFF_LATEST}}, derive=False,
                     repeat=opts.check_repeat)
    tc["empty"] = (tres is not None and not tres.get("differences") and not tres.get("unverified"))
    if tres is not None and tres.get("differences"):
        tc["first_differences"] = tres["differences"][:5]
    out["transition_check"] = tc
    print(json.dumps({"transition_check": tc}), flush=True)
    # the copied scope is checked once, to show that the copy is itself a conforming record
    uc, ures = r.run("transition_check", {"frame": {"scope": "u-project", "cutoff": CUTOFF_LATEST}}, derive=False,
                     repeat=1)
    uc["empty"] = (ures is not None and not ures.get("differences") and not ures.get("unverified"))
    out["unrelated_scope"]["transition_check"] = uc
    print(json.dumps({"transition_check_unrelated": uc}), flush=True)
    r.conn.close()

    # 4. a project-wide normalization, recorded after the build (7.3.8)
    out["normalization"] = normalization_phase(dsn, opts, proj.rooms, kept)
    del kept
    gc.collect()

    out["environment"] = {"postgresql": server, "image": IMAGE, "python": platform.python_version(),
                          "psycopg": psycopg.__version__, "machine": platform.machine(), "system": platform.system(),
                          "platform": platform.platform(), "container_port": opts.port}
    return out


def _container(port: str) -> tuple[str, str]:
    name = f"attedra-scale-{os.getpid()}"
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
    ap = argparse.ArgumentParser()
    ap.add_argument("--target-subjects", type=int, default=20000)
    ap.add_argument("--min-subjects", type=int, default=10000)
    ap.add_argument("--write-budget-s", type=int, default=2700)
    ap.add_argument("--rooms-per-floor", type=int, default=100)
    ap.add_argument("--repeat", type=int, default=5)
    ap.add_argument("--derive-repeat", type=int, default=1)
    ap.add_argument("--check-repeat", type=int, default=5)
    ap.add_argument("--cap-s", type=int, default=300)
    ap.add_argument("--norm-cap-s", type=int, default=3600)
    ap.add_argument("--norm-check-repeat", type=int, default=1)
    ap.add_argument("--sample-writes", type=int, default=50)
    ap.add_argument("--run-label", default=None)
    ap.add_argument("--out", default=str(PACKAGE / "scripts" / "scale_results.json"))
    opts = ap.parse_args()
    opts.port = os.environ.get("ATTEDRA_PG_PORT", "55581")
    dsn = os.environ.get("ATTEDRA_DSN")
    name = None
    # a termination signal unwinds through the finally below, so the container is stopped
    signal.signal(signal.SIGTERM, lambda signum, frame: sys.exit(143))
    t0 = time.perf_counter()
    try:
        if not dsn:
            name, dsn = _container(opts.port)
        result = run(dsn, opts)
    finally:
        if name:
            subprocess.run(["docker", "stop", name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    result["total_s"] = round(time.perf_counter() - t0, 1)
    head = {"run": opts.run_label, "date": datetime.date.today().isoformat(), "package_sha256": _package_hash()}
    result = {**head, **result}
    out = Path(opts.out)
    previous = _previous_runs(out)
    if previous:
        result["previous_runs"] = previous
    out.write_text(json.dumps(result, indent=1))
    print(f"wrote {opts.out}")
    return 0


def _package_hash() -> str:
    """The package hash of conformance/run.py, over the package as it is
    when the run ends."""
    spec = importlib.util.spec_from_file_location("attedra_conformance_run", PACKAGE / "conformance" / "run.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.package_hash()


def _previous_runs(path: Path) -> list:
    """The runs an existing output file holds, most recent first: its own run, then those it
    keeps under ``previous_runs`` or, as earlier files did, under ``previous_run``."""
    if not path.exists():
        return []
    try:
        old = json.loads(path.read_text())
    except ValueError:
        return []
    runs = []
    while isinstance(old, dict):
        nested = old.pop("previous_run", None)
        more = old.pop("previous_runs", None)
        runs.append(old)
        if more:
            runs.extend(more)
            break
        old = nested
    return runs


if __name__ == "__main__":
    sys.exit(main())
