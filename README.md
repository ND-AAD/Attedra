# Attedra

Attedra is an open data model that follows the changes and conflicts in what several sources assert about the same things, and from those assertions builds the record of a project. It is meant for any work in which several parties make claims about the same items on their own schedules and often disagree. Its examples come from building design and construction, where drawings, schedules, specifications, meeting minutes and submittals describe the same doors, rooms and equipment on different clocks.

Attedra stores **assertions, not values**. Every statement keeps three coordinates:
- **what** is described (the Item);
- **when** it applies (the context);
- **who** says so (the source).

From that structure the model derives what changed, who disagrees, what was required, what has been fulfilled, what was withdrawn and what was reviewed. Most importantly, it derives **what still remains to be done**.

> **Status: 0.1.0, preliminary.** This is the first public release. Breaking changes may occur in any later version, and no compatibility is guaranteed for records, reads or conformance claims across versions. See the specification, §11.

## The model in one page

The model has three primitives:
- **Items**: anything you can talk about, such as a door, a document, a milestone, a party or a story.
- **Connections**: untyped, ordered pairs of Items, such as "Room 12 contains Door 101". They carry lifecycle only.
- **Assertions**: what a source says about an Item at a context, keyed by the triple `(item, context, source)`.

Its main commitments:
- **Disagreement is data.** Two sources differing at one moment is a *conflict*. One source differing from its own earlier position is a *change*. Two requirements for different values are also a conflict. Comparing two assertions is one operation.
- **The record never ranks its authors.** When sources disagree, every position is kept and the disagreement is reported. A review records a decision; it does not make a value true. Only aligned evidence, the end of one side, or a correction showing there was never a disagreement ends a conflict.
- **Requirements are assertions too.** An *expectation* describes a future state of the same Item, in an expectation context. Evidence fulfills it; a withdrawal ends it.
- **Every unit of work is a story with a recorded beginning and end.** Conflicts, changes and each property of an expectation are units of work. Open means it has begun and has no end. Stories nest: a directive that resolves a change creates a requirement inside that change's story. Reading what remains is therefore a lookup, not a recomputation.
- **What ends a story is a declared policy.** The specification's endings are the baseline. An application may declare its own, named and versioned, but a policy never changes the facts the model derives.
- **Nothing is overwritten.** Revisions are new assertions. Withdrawals, corrections, reviews and reconciliations are recorded acts. Permanent removal exists only for misrecorded entries that nothing depends on.

[`Attedra_Specification.md`](Attedra_Specification.md) is the normative document. Read §1.5, "A story, end to end", first.

## Quickest path to a worked example

§1.5 of the specification follows Door 101 through two issues of a door schedule:
1. A change from paint to stain is detected.
2. The owner directs lacquer, which creates a requirement.
3. A later issue showing lacquer fulfils it.

The conformance suite includes this example in executable form:
- `T13_01_section_1_5_walkthrough_day_by_day` replays it day by day.
- `T18_18_what_remains_on_the_section_1_5_example_at_each_rows_cutoff` reads "what remains" at the end of each day.

```bash
bash scripts/run_conformance.sh section_1_5
```

Each fixture is a readable JSON file in `conformance/fixtures/`, made of steps (writes) and reads with their expected results. [`examples/README.md`](examples/README.md) maps every worked example in §12 of the specification to its fixtures.

## Running the reference checks

**Requirements:** Docker, and [uv](https://docs.astral.sh/uv/). uv provides Python 3.12 and psycopg 3.3.6 on demand.

```bash
bash scripts/run_conformance.sh
```

**What the script does:**
- It starts a disposable PostgreSQL 18.6 container, pinned by image digest.
- It runs every fixture against the reference library on a fresh schema, and prints one line per fixture.
- It writes `conformance/results.json`, including the environment and a SHA-256 of the package contents.
- It exits non-zero if any fixture fails.
- After every fixture, it also checks that the recorded beginnings and endings equal what the rules derive (9.5.8, invariant I-17).

**Options:**
- Set `ATTEDRA_PG_PORT` to use a port other than 55432.
- Pass fixture-name fragments to run a subset.

[`CONFORMANCE.md`](CONFORMANCE.md) records the results for this release, with the exact environment and package hash.

## What is in this repository

| Path | Contents |
|---|---|
| `Attedra_Specification.md` | The specification, 0.1.0 (preliminary). Numbered rules are the targets of the fixtures. |
| `conformance/README.md` | The fixture contract: step and read formats, result shapes, matching, error codes. |
| `conformance/fixtures/` | 421 fixtures in 18 families (T01–T18), each keyed to the rules it exercises. |
| `conformance/run.py` | The runner. |
| `reference/schema.sql` | The reference store: three tables (items, connections, assertions), with indexes. |
| `reference/attedra_ref/` | The reference library, Python 3.12 over PostgreSQL. It implements every write and read of the specification. |
| `scripts/` | `run_conformance.sh` runs the checks; `measure_locality.py` and `measure_scale.py` are the measurements reported in `CONFORMANCE.md`. |
| `examples/` | A guide from the specification's worked examples to the fixtures. |
| `CONFORMANCE.md`, `CHANGELOG.md`, `LICENSE`, `NOTICE` | Evidence, history, license and copyright notice. |

The reference library is a reference, not a product. It shows that the rules can be implemented over the three primitives alone, and it is the subject of the conformance results. Its public surface is `attedra_ref.api.Session`:

```python
import psycopg
from attedra_ref.api import Session

with psycopg.connect("postgresql://…") as conn:      # a database holding reference/schema.sql
    s = Session(conn)
    s.create_item("door-101", "door")
    # … create the source and context Items, then write Assertions:
    s.assert_("door-101", "arch-100cd", "a-601", '{"finish": "stain"}')
    s.read("what_remains", {"frame": {"scope": "project"}})
```

Read names, arguments and result shapes are in `conformance/README.md` §5.

## Supported limits

- **Performance.** The specification makes no performance guarantee (§11.4). Reads are scoped: they never traverse the whole store (9.10). `CONFORMANCE.md` reports what was measured on one documented machine. For example, at about 20,000 subjects the status reads ("what remains", open stories, pending review, open work) took about 1.6 to 2.9 seconds. Those figures describe that environment only.
- **Known limitations** are declared in §11.7. They cover moving records between implementations that lack an application's comparison rules, literal comparison named on a single requirement, recorded frames, and a few rare normalization cases.
- **Not provided by the model** (§11.3): identity registries, authorization and roles, notifications, read receipts, unit and equivalence registries, and replay of the store as it was at a past recording time.
- **Comparison rules are the application's.** Attedra compares literally unless an application declares a named, versioned interpretation. An interpretation might treat `1/8"` and `.125"` as equal, read `3'0"` as `3'-0"`, absorb common misspellings, or equate "90 min" with "1.5 h".
  - The rules, and the logic behind them, belong to the program.
  - The model records which interpretation applies and from when. A project-wide normalization takes effect when it is made, closes the disagreements it resolves, and is cited wherever it makes two values match (7.3.8).
  - The reference ships only small fixture interpretations used by the tests.

## Roadmap

These capabilities are deferred to the first revision after 0.1.0 (§11.2):
- shared obligations: one requirement obligating several named sources;
- identity continuity: when a replaced or reassembled thing is still the same Item;
- applying an application's ending policy in participant perspectives.

The known limitations of §11.7 are candidates for the same revision.

## License

Apache License 2.0. See [`LICENSE`](LICENSE) and [`NOTICE`](NOTICE).

Copyright 2026 Nick Duch.
