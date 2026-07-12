# First Five Meaningful Submissions Design

## Goal

Produce five reproducible, non-empty, ontology-backed submission ZIP files for manual upload to the Viettel competition portal.
Each submission will change one primary variable, preserve exact raw offsets, and record enough metadata to interpret the returned score.
The user will upload each artifact and provide the portal score for the repository ledger.

This checkpoint will not train a model, use an external API at evaluation time, invent ontology identifiers, submit the existing empty artifact, or claim that a public leaderboard gain generalizes automatically.
The active model parameter budget remains `0 / 9B`.

## External ontology source

Use NLM Current Prescribable Content release `RxNorm_full_prescribe_07062026.zip`, published July 6, 2026.
The official archive is marked no-license-required and has published MD5 checksum `767678e3b5b1d6fe358b61c21659f3ef`.
The downloaded archive will also receive a locally computed SHA-256 checksum.

The archive contains active prescribable content in `RXNCONSO.RRF`, `RXNREL.RRF`, and `RXNSAT.RRF`.
The ingestion checkpoint will use `RXNCONSO.RRF` only for the first lexical index because the first five hypotheses require identifiers, strings, sources, and term types but not relationship traversal.
Only English rows with a non-empty RXCUI and term will enter the index.
RxNorm normalized rows from `SAB=RXNORM` are preferred over other source rows.
Suppressed rows are excluded.

The raw archive will remain untracked under `ontologies/rxnorm/`.
A committed provenance manifest will record URL, release date, access date, published MD5, computed SHA-256, license status, redistribution status, included files, filters, and NLM attribution.
No identifier absent from the pinned local archive may be emitted.

The Current Prescribable Content subset excludes obsolete and historical concepts.
Active-plus-historical retrieval therefore remains a later licensed experiment rather than being simulated or approximated.

## Components

### RxNorm ingestion

Add a standard-library RRF reader that consumes a local archive path and returns immutable concept terms.
Each term contains RXCUI, text, term type, source, preferred flag, and suppression flag.
The reader will validate the expected archive member, UTF-8 decoding, RRF column count, numeric RXCUI, supported source, and published MD5 before producing terms.

The first implementation will read the ZIP directly without extracting its contents to the workspace.
This keeps acquisition reproducible and avoids duplicate ontology payloads.

### Lexical drug linking

Normalize ontology strings and extracted drug spans with Unicode case folding, punctuation-to-space conversion, and whitespace collapse.
Keep the raw span unchanged for output.
Do not remove diacritics from the raw text or output.

Rank a concept when its normalized ontology term occurs as a token-bounded substring of the normalized span or when the span occurs as a token-bounded substring of the ontology term.
Prefer a longer matched term, an exact normalized match, `SAB=RXNORM`, preferred rows, and deterministic RXCUI order.
Collapse duplicate terms to one ranked candidate per RXCUI.

The precision-first gate will emit a drug only when at least one ontology-backed candidate exists.
Generic treatment phrases and noisy extracted lines without a candidate will be dropped rather than assigned an invented code.

Candidate policy will support top one, top two, and ingredient-only filtering.
Ingredient-only includes RxNorm term types `IN`, `PIN`, and `MIN`.
All-retrievable includes the term types present in the approved archive.

### Entity generation

Build one prediction function that consumes raw text, the RxNorm index, and a submission configuration.
It will run the existing drug and laboratory extractors and the existing assertion engine.

Linked drugs become `THUỐC` entities with `text`, `type`, `candidates`, `assertions`, and `position`.
Laboratory names become `TÊN_XÉT_NGHIỆM` entities with `text`, `type`, and `position`.
Laboratory values become `KẾT_QUẢ_XÉT_NGHIỆM` entities with `text`, `type`, and `position`.
The laboratory schema remains provisional and configurable.

Regimen-inclusive drug spans use the existing extractor output.
Core drug spans use the exact raw subspan corresponding to the selected ontology term when that term occurs inside the regimen span.
If a unique exact raw core cannot be recovered, the core-span variant drops that drug rather than fabricating an offset.

Entity order follows raw start position and preserves separate occurrences.
Every entity must pass the strict serializer and raw-slice validator before packaging.

### One-command build and semantic diff

Add a command that reads `input.zip`, the pinned RxNorm archive, and one JSON configuration, then creates a deterministic ZIP and a JSON build report.
The report will include commit, config, ontology checksum, artifact checksum, entity counts by type, linked and dropped drug counts, empty document count, candidate count, assertion count, and model budget.

Add a semantic prediction diff that compares two generated ZIP files by document and reports added, removed, and changed entities plus changed candidates, assertions, text, type, and position.
Every non-baseline submission must have exactly one documented primary policy change from its parent.

Generated ZIP files and reports remain ignored build artifacts.
Committed configuration and ledger files retain their identities and checksums.

## First five submissions

### Submission 1: Precision drug baseline

Emit linked regimen-inclusive drug entities only.
Use all retrievable term types and top-one candidates.
The hypothesis is that conservative ontology-backed drug predictions produce a measurable non-zero score without speculative types or codes.

### Submission 2: Add laboratory pairs

Use Submission 1 unchanged and add laboratory-name and laboratory-result entities.
The hypothesis is that existing exact-offset laboratory rules add text credit with acceptable precision under the provisional laboratory schema.

### Submission 3: Core drug spans

Use Submission 2 unchanged and replace regimen-inclusive drug spans with recoverable core drug-name spans.
The hypothesis is that the evaluator may prefer normalized medication names over full regimen spans despite the official example showing modifier-inclusive spans.

### Submission 4: Ingredient-only candidates

Use Submission 2 unchanged and restrict drug candidates to `IN`, `PIN`, and `MIN` term types.
The hypothesis is that organizer targets may emphasize ingredients rather than clinical or branded drug concepts.

### Submission 5: Top-two candidates

Use Submission 2 unchanged and emit the two highest-ranked distinct RXCUIs when available.
The hypothesis is that candidate recall may outweigh the Jaccard penalty for one additional plausible code.

The artifacts will be uploaded in numerical order unless an earlier portal result makes a later hypothesis invalid or redundant.
In that case, the later slot may be replaced by a documented one-variable experiment with higher expected information value.

## Ledger and manual portal workflow

Before upload, each artifact will have a committed configuration, commit hash, SHA-256 checksum, parent submission, hypothesis, semantic prediction diff, and changed counts.
The user will upload the named artifact manually and return its submission identifier, score, and any component scores shown by the portal.
The repository will then record the result in `docs/submissions.csv` before the next upload.

The portal quota must be checked before the first upload.
The all-empty `outputs/NON_SUBMITTABLE-empty-output.zip` must never be uploaded.

## Validation and testing

TDD tests will cover RRF parsing from a tiny in-memory ZIP, checksum rejection, suppression filtering, ranking determinism, brand and generic matching, noisy-span rejection, term-type filtering, top-one and top-two output, exact core offset recovery, laboratory toggling, assertion attachment, complete schema validation, deterministic ZIP generation, and semantic diffs.

An end-to-end dry run will process all 100 documents from the canonical `input.zip`.
Acceptance requires at least one ontology-backed drug entity, zero invented candidates, zero raw-offset mismatches, 100 valid JSON entries, deterministic rebuild checksums, distinct non-empty variants, and complete build reports.

The full unittest suite and Python compilation will pass before any artifact is offered for upload.

## Known limits and next iteration

The first five submissions intentionally omit diagnosis and symptom extraction because neither has a reliable extractor and diagnosis output requires an ICD ontology.
This omission limits recall but does not prevent a meaningful measured baseline.

After scores return, prioritize the highest-information improvement among ICD-backed diagnosis extraction, symptom extraction, licensed historical RxNorm, better brand aliases, and precision fixes found in the generated audit.
Promotion to the stable baseline requires reproducible score improvement, an interpretable prediction diff, and plausible private-test generalization.
