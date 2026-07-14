# Diagnosis and ICD Baseline Design

## Goal

Add a reproducible offline diagnosis capability to the promoted Submission 6 baseline.
The capability must recognize high-precision Vietnamese diagnosis mentions, link every emitted mention to a pinned ICD-10 code, preserve exact raw offsets, and leave all existing predictions unchanged.

## Competitive context

Submission 6 scored `9.86290`, while the reported leading score is approximately `53`.
The remaining gap is too large for another candidate-cardinality or span-only probe.
Diagnosis coverage is the next integrated product capability because it can improve text, assertion, and candidate components together.

Only four of the 100 public records contain a top-level diagnosis section.
Seventy-four records contain an assessment section, 89 contain past-history content, and 41 contain imaging content.
A diagnosis-section-only rule would therefore be structurally precise but too narrow.

## Evidence and hidden variables

The serializer already recognizes `CHẨN_ĐOÁN` with exactly `text`, `type`, `candidates`, `assertions`, and `position`.
The competition does not identify the ICD namespace, release, alias set, candidate granularity, or matching policy.
These remain hidden variables and must stay configurable.

The Ministry of Health clinical-coding site exposes a Vietnamese ICD-10 hierarchy through the public application at `https://icd.kcb.vn/ICD-10-VN`.
The application reads the catalog from `https://ccs.whiteneuron.com/api/ICD10/`.
The base catalog corresponds to the national ICD-10 catalog associated with Decision 4469/QĐ-BYT dated 2020-10-28.
The same application exposes a separate `ICD10_TT06` branch for the June 2026 update.

The base 2020 catalog is the initial pinned source because it is the established national reference and avoids silently mixing releases.
The June 2026 branch remains a future controlled ontology experiment.
This source choice is an evidence-backed inference, not a claim about the organizer's hidden target.

## Considered approaches

### Approach A: Diagnosis-section-only rules

This approach would split the four explicit diagnosis sections and manually map their terms.
It has low engineering risk but poor coverage and creates pressure to encode public-record phrases.
It is rejected because it cannot plausibly close the competitive gap and risks public-test overfitting.

### Approach B: Pinned ontology plus structural exact matching

This approach pins the national Vietnamese ICD-10 hierarchy, builds an offline term index, and matches ontology titles in diagnosis-bearing clinical contexts.
It uses exact normalized matching for precision while mapping every match back to an exact raw-text span.
It covers explicit diagnosis sections, diagnosis sub-blocks inside assessments, past history, and imaging findings.
It is selected as the final rule-baseline milestone because it is reproducible, interpretable, generalizable, and immediately improves all three scored components when matches are correct.

### Approach C: Model-based clinical NER and neural reranking

This approach offers the largest eventual recall but introduces model provenance, parameter-budget, offline-packaging, training-data, and calibration work.
It is not rejected.
It follows Approach B because project policy requires the rule baseline to be completed before model training and because the pinned ontology and output interface are prerequisites for a model linker.

## Ontology acquisition and provenance

A standard-library acquisition tool will traverse the public hierarchy beginning at `GET /api/ICD10/root?lang=vi`.
It will request children by the returned `model` and `id` values until every leaf is reached.
It will reject cycles, duplicate node identities with conflicting data, malformed codes, missing names, and unsuccessful responses.

The tool will write a canonical UTF-8 JSON snapshot with sorted keys and deterministic node ordering.
Acquisition time, source page, API base, national decision, language, checksum, license status, and redistribution policy will be recorded separately in provenance.
The raw snapshot will remain untracked and will not be redistributed.
No runtime network access is allowed.

No explicit redistribution license has yet been located for the application dataset.
The data will therefore be recorded as public official reference data for internal competition use only, with raw redistribution prohibited unless a license is established.
The tracked acquisition code and checksum will make the local snapshot reproducible without bundling it.

## Offline representation

The reader will expose immutable ICD terms containing `code`, `name`, `model`, and `is_leaf`.
It will verify the snapshot SHA-256 before parsing.
Only codes present in the verified local snapshot may become output candidates.

The first candidate policy will use one code per mention.
Leaf terms are preferred over broader parent terms when identical normalized titles collide.
Ambiguous normalized titles with different leaf codes will be rejected rather than guessed.

## Recognition policy

Recognition will operate only in diagnosis-bearing contexts:

- top-level diagnosis sections, stopping at treatment or procedure sub-headings;
- sub-blocks explicitly headed as other diagnostic findings inside assessment sections;
- past-history sections;
- imaging sections and imaging-finding sub-blocks.

The recognizer will match complete ontology terms after Unicode normalization, case folding, and conservative separator and whitespace normalization.
Normalization will preserve a boundary map back to the original raw text.
Every accepted span must satisfy `raw_text[start:end] == text`.

Short generic titles, chapter titles, section-range titles, and ambiguous normalized aliases will not be emitted.
Overlapping matches will resolve to the longest specific span.
Distinct duplicate occurrences will be preserved.
The recognizer will not create a corpus-derived diagnosis lexicon or manually map public-record phrases.

Explicit diagnosis text that cannot be linked to a unique pinned term will be omitted from this first capability.
That precision-first decision protects candidate Jaccard and becomes a measurable retrieval-error bucket for the model phase.

## Pipeline integration

Submission configuration will gain an optional `include_diagnoses` boolean that defaults to `false`.
All existing configurations must rebuild byte-identically when the field is absent.

When enabled, the build path will load and verify the ICD snapshot, run diagnosis recognition, attach the existing assertion labels, and emit the existing strict diagnosis schema.
The output candidate will be the exact code string from the snapshot.

The build report will record the ICD checksum, diagnosis count, linked diagnosis count, candidate count by entity type, and the unchanged model budget.
The active model parameter budget remains `0 / 9B`.

## Validation and promotion gate

Tests will begin with failing cases for snapshot traversal, checksum validation, exact-offset recognition, ambiguous terms, context gating, duplicate mentions, overlap resolution, assertion attachment, and backward-compatible configuration loading.

The corpus audit will inspect every generated diagnosis before packaging.
The Submission 6 to diagnosis-enabled semantic diff must contain only added `CHẨN_ĐOÁN` entities.
All emitted codes must occur in the pinned snapshot.
Independent builds must produce byte-identical ZIP files.

The integrated artifact will not be promoted merely because it is non-empty.
It must have useful cross-document coverage, no obvious false-positive class in the full audit, and a clean isolated leaderboard gain over Submission 6.

## Follow-on model milestone

After this rule baseline is complete, the next product phase will add broader Vietnamese clinical mention recognition and ontology retrieval behind the same extractor-linker interface.
The likely design is a compact multilingual encoder or clinical NER model plus lexical candidate generation and calibrated top-one reranking.
The pinned ontology, exact offset mapping, candidate validator, and evaluation buckets from this milestone will remain unchanged.
