# Conformance results: Attedra 0.1.0 reference

This file records how the reference implementation in this repository performed against the conformance suite of the Attedra Specification 0.1.0 (preliminary). It also records the environment the results were obtained in, and what was measured about cost. The results describe these exact contents and that environment only.

## 1. Result

| | |
|---|---|
| Specification | `Attedra_Specification.md`, 0.1.0 (preliminary) |
| Fixtures | 421 in 18 families (T01–T18) |
| Result | 421 passed, 0 failed, 0 errors, 0 blocked |
| Transition check | Run after every fixture (9.5.8, invariant I-17). Empty for every fixture. |
| Package SHA-256 | `6134730dffc62c66654c49ecd1d448f4afb0e1f3e92d052684e891a708c723ee` |
| Date | 2026-10-10 |

The package hash is computed by `conformance/run.py` and written to `conformance/results.json`. It covers every `.py`, `.sql`, `.json`, `.md`, `.toml` and `.sh` file at the repository root and in `conformance/`, `examples/`, `reference/` and `scripts/`, except this file and the results files. It therefore identifies the exact specification, contract, fixtures and library tested.

To reproduce: `bash scripts/run_conformance.sh` from a clean checkout (README, "Running the reference checks").

## 2. Environment

| | |
|---|---|
| Database | PostgreSQL 18.6, image `postgres@sha256:74935e72241653ca55e0414067e6d8763aceb8a810eb51b452253ec3dcfc4336` (postgres:18), started fresh by the script |
| Python | 3.12.13, provided by uv (`uv run --no-project --python 3.12`) |
| Driver | psycopg 3.3.6 (`psycopg[binary]==3.3.6`); the library uses nothing else outside the Python standard library |
| Host | macOS 26.6.2 on arm64 (Apple A18 Pro, 8 GB); Docker Desktop 29.6.1 (linux/arm64 VM, 6 CPUs, about 3.8 GiB) |

The store is the three tables of `reference/schema.sql` (items, connections, assertions), with indexes and four IMMUTABLE helper functions for discovery. It has no other tables, views, triggers or sequences.

## 3. By family

| Family | Subject | Fixtures |
|---|---|---|
| T01 | Primitive integrity and references | 47 |
| T02 | Sparse carry-forward | 13 |
| T03 | Structured replacement | 8 |
| T04 | Value comparison | 13 |
| T05 | Current-value withdrawal | 14 |
| T06 | Partial and bulk withdrawal | 19 |
| T07 | Expectation identity and support | 19 |
| T08 | Source qualification | 18 |
| T09 | Fulfillment | 32 |
| T10 | Time and distribution | 28 |
| T11 | Comparison paths | 18 |
| T12 | Review and attention | 18 |
| T13 | Story chronology | 42 |
| T14 | Recorded basis | 7 |
| T15 | Error operations | 28 |
| T16 | Structural history and scope | 18 |
| T17 | Portability and extension handling | 12 |
| T18 | Recorded beginnings and endings, ending policies and normalization | 67 |

Every fixture lists the rule identifiers it exercises. `examples/README.md` maps the worked examples of §12 to their fixtures.

## 4. Cost (what was measured, not a guarantee)

The specification states no performance guarantee (§11.4). The following was measured with this library, on the host above, by the scripts in `scripts/`. The library measured is identical in behaviour to this release; the two differ only in comments and fixture notes.

**Locality** (`scripts/measure_locality.py`). The test holds the relevant records fixed and grows unrelated data from 1× to 1000× (82 to 41,041 assertions). The scoped reads load the same records and rows, and issue the same number of queries, at every size:

| Read | Records | Rows | Queries |
|---|---|---|---|
| `open_work` | 63 | 81 | 15 |
| `story` | 84 | 113 | 13 |

From 10× upwards, no discovery query plans a sequential scan. With a normalization in every scope, the reads stay constant as well: 66 records, 86 rows and 21 queries for `open_work`, and 89, 120 and 20 for `story`.

**Scale** (`scripts/measure_scale.py`). A synthetic project of 20,100 subjects was written through the library's public API. It has doors, frames and hardware sets in 6,700 rooms on 67 floors, and holds:
- about 56,000 statements;
- 4,020 stories;
- 5,360 expectations.

An unrelated project of equal size was then copied into the same store, which made 175,788 assertions in all. Medians of 5 runs:

| Read (record perspective) | Before a normalization | After a project-wide normalization |
|---|---|---|
| `what_remains` | 2.0 s | 2.6–2.9 s |
| `open_stories` | 1.6 s | 2.1 s |
| `pending_review` | 1.6–1.7 s | 2.1 s |
| `open_work` | 1.6–1.7 s | 2.0–2.1 s |

Other results from the scale run:
- Each read gave the same answer, queries and rows before and after the unrelated project was added.
- The same reads computed by full derivation, instead of from the recorded beginnings and endings, gave identical answers and took 3–8 s.
- Writing the project-wide normalization took 5.8 s in one transaction. It ended the 335 conflict stories it resolved.
- The transition check over the project took 3.9 s, and it was empty.
- Statement writes took a median of 5.1 ms (p95 13 ms), and acts a median of 9.7 ms (p95 20 ms). Neither grew over the build.

These figures describe that host and that data only.

## 5. Not covered by measurement

The scale run did not exercise corrections, backfilled evidence, participant perspectives, the attention filter, expectations that name their own interpretation, or several normalizations at once. The conformance fixtures cover each of these for correctness.
