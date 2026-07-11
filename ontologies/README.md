# Ontology Policy

Store legally usable ICD and RxNorm snapshots under `ontologies/icd/` and `ontologies/rxnorm/` with source, version, license, checksum, and acquisition date.
Never emit a code absent from a pinned local snapshot.

For RxNorm, retain active and historical concepts plus replacement relationships when legally available.
Keep active status, term type, branded or generic level, combination or component behavior, and candidate-output policy configurable.
Never assume the newest replacement RXCUI is the evaluator target.
