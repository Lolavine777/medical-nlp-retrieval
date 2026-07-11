# Evidence-First Clinical NLP Baseline Design

## Scope

This milestone verifies the competition artifacts, records research evidence, creates the minimum repository structure, and produces an implementation plan for an end-to-end rule baseline.
It does not train, download, or scaffold a large model.

`input.zip` at the repository root remains the single canonical raw input artifact.
The `data/raw/` directory is reserved for future source artifacts and must not contain a duplicate of `input.zip`.

## Evidence flow

The saved official HTML and `input.zip` are immutable inputs.
A standard-library audit script will read both artifacts without extraction or mutation and emit reproducible statistics and checks.
The checks will cover ZIP membership, strict UTF-8 decoding, document lengths, physical line counts, section-header frequencies, drug-like and laboratory-like lines, assertion cues, official example schemas, duplicate mentions, and end-exclusive offsets.

Every recorded claim will distinguish verified source evidence, derived inference, and unresolved assumptions.
Research notes will record the URL, access date, evidence, confidence, uncertainty, and strategic impact for each finding.

## Repository structure

Only directories and files required by the current milestone will be created.
Empty Python packages, placeholder modules, `.gitkeep` files, and speculative configuration will not be added.
The planned baseline component boundaries will be documented now and materialized checkpoint by checkpoint when implementation begins.

The repository will use these top-level areas:

- `configs/` for reproducible experiment configuration once a configurable experiment exists.
- `data/raw/`, `data/external/`, `data/synthetic/`, and `data/processed/` for non-canonical derived or added data.
- `ontologies/icd/` and `ontologies/rxnorm/` for approved local ontology snapshots and provenance.
- `research/` for source notes and machine-readable source records.
- `docs/` for assumptions, annotation policy, experiments, specifications, and plans.
- `src/` for offset handling, section parsing, extraction, assertions, linking, postprocessing, evaluation, and submission code as those components are implemented.
- `tests/` for the smallest runnable checks that protect source interpretation and output correctness.
- `outputs/` for generated submissions and reports that are not raw inputs.

## Baseline architecture

The future baseline will process each document through an offset-safe loader, a section parser, rule-based drug and laboratory extraction, conservative assertion rules, approved local ontology matching, constraint postprocessing, a type-dependent serializer, an output validator, and a local evaluator.
The raw document string will remain immutable throughout the pipeline.
Any normalized view will carry an explicit mapping back to raw indices.

The serializer will preserve separate mentions at separate positions and reject any entity for which `raw_text[start:end] != entity["text"]`.
It will emit only fields allowed for the entity type by verified competition evidence.
The linker will return only identifiers present in an approved local ontology snapshot.

## Error handling and unknowns

Artifact validation failures will be fatal and identify the file and violated invariant.
Heuristic extraction ambiguity will remain observable through reproducible reports rather than being silently converted into invented labels or codes.

The exact ICD edition, RxNorm snapshot, complete type-dependent schema, mention-matching algorithm, role of `position` in scoring, and target RxNorm concept granularity remain unresolved until confirmed by an official artifact or controlled leaderboard evidence.
Policies for history-of-present-illness sections and family reporter versus family experiencer will remain documented assumptions until annotated evidence confirms them.

## Verification strategy

The source audit will be rerunnable with the repository virtual environment or `uv run` once project tooling is initialized.
The official example will become a byte-preserving fixture because HTML rendering collapses whitespace that affects offsets.
The fixture test will verify every official entity span using end-exclusive slicing and will verify that repeated surface forms remain separate mentions.

Each baseline checkpoint will add one focused failing test before implementation, then run focused tests, the relevant full suite, JSON validation, raw-offset validation, and a sample end-to-end output before completion is claimed.

## Deliverables for this milestone

This milestone will produce reproducible source-audit code, verified dataset statistics, `research/notes.md`, `docs/assumptions.md`, `docs/annotation_policy.md`, the minimal repository directories, and a checkpointed implementation plan.
The final report will separate verified findings, important unknowns, proposed architecture, implementation checkpoints, and high-information leaderboard experiments.
