# Changelog

## 0.1.0 (preliminary)

This is the first public release of the Attedra specification, its fixture contract, its conformance suite and its reference implementation.

**Specification**
- Three primitives: Items, Connections and Assertions. Assertion identity is `(item, context, source)`, and references are exact.
- Source attribution, evidence and eligibility.
- Contexts, instants, milestones, distribution and evaluation frames.
- Values: omission and carry-forward, explicit emptiness, structured replacement, and comparison.
- Expectations: support, qualification, fulfillment and explicit withdrawal.
- Stories of changes and conflicts, recorded review, related stories, reconciliation and reconstructed history.
- Recorded beginnings and endings for every unit of work, ending policies, and project-wide normalizations.
- Writes, revision versus correction, permanent removal of misrecorded entries, and the Connection lifecycle.
- Required reads, including "what remains" and the transition check.
- Integrity rules, validation, extension boundaries and conformance.
- Version, stability and declared limitations (§11).

**Conformance and reference**
- The fixture contract: `conformance/README.md`.
- 421 fixtures in 18 families, T01–T18.
- A reference library over PostgreSQL that uses three tables only.
- A runner that checks recorded beginnings and endings after every fixture.
- Locality and scale measurements, recorded in `CONFORMANCE.md`.

**Known limitations and deferred capabilities**
- See the specification, §11.2 and §11.7.
