# Interim Readiness Tooling Design

## Goal

Use the waiting period before the organizer update to remove packaging risk, expose candidate-linking weaknesses, and make the first post-update comparison reproducible.
This work must not assume that any competition policy or dataset change is already live.
It must not train a model, change prediction behavior, or consume a portal submission.

## Selected approach

Extend the existing pipeline with small observational tools and documentation.
Reuse the current submission builder, entity validator, ontology readers, linkers, and semantic diff implementation.
Do not add an experiment framework, metrics service, dependency, or second pipeline.

## Submission preflight

Expose the current final-archive verification as a reusable function and a standalone command.
The command will receive a candidate ZIP and the canonical input ZIP.
It will require exactly `output/1.json` through `output/100.json` at the archive root.
It will decode every record as strict UTF-8 JSON and reuse the existing type-dependent entity, candidate, assertion, and raw-offset validation.
It will print a compact report containing the archive checksum, record count, entity count, candidate count, assertion count, and counts by entity type.

Errors will distinguish an evaluator-ready archive from common transfer mistakes.
A proposal archive containing `manifest.json` or `documents/*.json` will be identified as intermediate model evidence.
A ZIP with a single wrapper directory will be identified as nested instead of being silently flattened.
Malformed JSON, missing records, extra records, schema violations, and offset violations will fail before upload.

The final builder will continue validating its own output through the same shared function.

## Linking diagnostics

Add a read-only audit command for the current extracted drug and diagnosis mentions.
The audit will use the pinned local ontology snapshots and the existing normalization and ranking policies.
It will not modify a prediction or introduce a new candidate source.

For drugs, the report will include the raw mention, normalized query, ranked candidate identifiers, matched ontology text, term type, source, preferred status, and whether the mention was unlinked.
The existing top-one and top-two behavior will call the same ranking function so that diagnostics cannot drift from production ranking.

For diagnoses, the report will include the raw mention, normalized query, selected exact code, ambiguous exact-title codes, and unlinked status.
No fuzzy or neural retrieval will be added in this milestone.
The diagnostic output will expose the recall and ambiguity buckets needed to design lexical, dense, or cross-encoder retrieval after the new data is available.

The command will write deterministic JSON that can be compared across input versions.
Without gold labels, its metrics are coverage and ambiguity evidence, not accuracy claims.

## Reproducible controls

Add one command that builds two controls from one input ZIP and one output directory.
The rule-only control will use the full stable rule pipeline represented by Submission 7.
The Qwen control will use the same deterministic pipeline with the validated proposal directory represented by Submission 8.

The command will call the existing submission builder twice, preflight both archives, write both build reports, and create the existing semantic diff.
It will fail before starting if required ontology files, the Qwen proposal directory, or destination parents are missing.
It will never run Qwen inference or download a model.

The controls will retain their input, ontology, configuration, commit, model budget, and output checksums.
The generated filenames will identify them as controls rather than numbered portal submissions.

## Post-update bring-up checklist

Add an operational checklist that remains inactive until the user explicitly confirms that the update is live.
The checklist will require preserving the new raw artifact, recording its checksum, checking strict UTF-8 and document names, comparing corpus structure with the legacy input, and verifying the published output contract.
It will then run the final-archive preflight, both controls, the semantic diff, and the linking audit.

No model training or ranking change will begin until these results distinguish input drift, contract drift, extraction drift, and linking drift.
The checklist will identify the first controlled portal experiment but will not upload anything.

## Error handling

Every command will fail with a nonzero exit code and a direct path-specific message.
Existing files will not be overwritten.
Raw inputs and proposal records will remain read-only.
An unexpectedly empty entity or candidate result will be reported as a control failure rather than accepted as a quality result.

## Tests and acceptance criteria

Implementation will follow test-driven development.
The first end-to-end regression will reproduce the Submission 9 mistake by presenting an intermediate proposal ZIP to the preflight command and observing rejection.

Acceptance requires:

- A valid fixture submission passes preflight and produces deterministic counts and checksum.
- Proposal, nested, malformed, incomplete, extra-entry, invalid-schema, and invalid-offset archives fail clearly.
- Drug ranking diagnostics preserve every existing top-one and top-two result.
- Diagnosis diagnostics separate linked, ambiguous, and unlinked exact queries.
- One control command produces two preflighted archives, two reports, and one semantic diff from fixtures.
- The Qwen control reports the pinned 4B model while the rule control reports zero model parameters.
- The focused tests and the full existing test suite pass using the repository virtual environment.

## Excluded scope

This milestone does not add fuzzy retrieval, dense retrieval, a cross-encoder, training data, model training, new ontology data, portal automation, or assumptions about the unreleased update.
Those changes require evidence from the updated problem statement and dataset.
