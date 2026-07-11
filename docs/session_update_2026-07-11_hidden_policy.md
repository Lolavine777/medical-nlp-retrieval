# Session Update - Hidden Evaluator Policy

New organizer information supersedes the earlier expectation that ontology, schema, span, candidate, or position policies might later be clarified.
These are intentional hidden evaluator variables.

## Decision changes

- Ontology ingestion is no longer blocked while waiting for an organizer snapshot.
- Use legally available versioned ICD and RxNorm references with full provenance.
- Retain active and historical RxNorm concepts plus replacement relationships when legally available.
- Never assume a current replacement RXCUI is the evaluator target.
- Keep RxNorm status, term type, branded or generic level, combination or component output, span boundaries, candidate cardinality, and position strategy configurable.
- Resolve one hidden policy at a time through reproducible leaderboard experiments.
- Stop requesting clarification on policies the organizer has declared part of the challenge.

## Priority experiments

1. Active-only versus active-plus-historical RxNorm.
2. Ingredient versus clinical-drug versus branded-drug candidates.
3. Combination RXCUI versus component RXCUIs.
4. Core span versus modifier-inclusive span.
5. Exact raw offsets versus one alternative position strategy after non-position predictions stabilize.

The private-test generalization objective and prohibition on public-test hard-coding remain unchanged.
