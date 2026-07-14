# Ontology Policy

Store legally usable ICD and RxNorm snapshots under `ontologies/icd/` and `ontologies/rxnorm/` with source, version, license, checksum, and acquisition date.
Never emit a code absent from a pinned local snapshot.

Raw ontology snapshots are untracked and must not be redistributed unless their recorded license permits redistribution.
Tracked `PROVENANCE.json` files identify the exact local snapshot, checksum, acquisition procedure, and use restrictions.

For RxNorm, retain active and historical concepts plus replacement relationships when legally available.
Keep active status, term type, branded or generic level, combination or component behavior, and candidate-output policy configurable.
Never assume the newest replacement RXCUI is the evaluator target.

For ICD-10, keep the national catalog branch and candidate cardinality configurable because the organizer namespace and release are hidden.
The current baseline pins the Vietnamese `ICD10` branch separately from the June 2026 `ICD10_TT06` branch.
