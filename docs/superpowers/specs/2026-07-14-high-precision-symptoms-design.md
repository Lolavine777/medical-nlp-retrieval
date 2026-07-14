# High-Precision Symptom Submission Design

## Goal

Add a conservative `TRIỆU_CHỨNG` extraction path to the stable Submission 2 baseline and produce one controlled upload artifact.
The artifact should improve missing text and assertion coverage without changing drugs, laboratory entities, RxNorm candidates, or drug spans.

## Evidence and decision

Submission 2 showed that exact structured entity coverage can materially improve the public score.
Submission 3 showed only a marginal mixed span gain.
Submission 4 showed that dropping drug coverage is harmful.
Submission 5 established that every linked drug should retain exactly one candidate.

The corpus audit found 1,238 non-empty lines inside `symptoms` and `admission_reason` sections, including 814 bulleted lines.
Many of those lines describe procedures, events, characteristic metadata, or narrative rather than symptom mentions.
Whole-line section output is therefore rejected as too imprecise.

Three approaches were considered.

1. Ingredient-preferred RxNorm linking with brand fallback would isolate candidate granularity but affect only ten known candidate choices and has limited expected upside.
2. Structural extraction from explicit current-symptom blocks targets a much larger missing entity class without requiring unpinned ontology codes.
3. Diagnosis extraction with ICD linking has the highest long-term ceiling but is blocked from safe implementation until a licensed, pinned, and documented ICD source exists.

The chosen approach is structural symptom extraction followed by ICD acquisition and diagnosis linking as a separate milestone.

## Scope

The extractor will use existing section and line-role output.
It will not use a lexicon derived from public test phrases.
It will not add a model, dependency, external runtime call, ontology identifier, or new output field.
It will not change existing drug, laboratory, assertion, serializer, or candidate behavior.

## Extraction policy

The extractor will consider only `symptoms` and `admission_reason` sections.
Within an admission-reason section, the first short inline chief complaint may be emitted when it is not a generic heading or metadata line.
Bulleted content becomes eligible only inside an explicit current-symptom block introduced by a heading such as `Triệu chứng hiện tại`, `Các triệu chứng hiện tại`, or `Triệu chứng chính`.
Eligibility ends at a symptom-characteristics, pre-admission-events, onset-time, examination, laboratory, imaging, diagnosis, or treatment subsection.

Only short symptom-shaped bullet values will be emitted.
Generic headings, `N/A` values, characteristic labels, time or frequency metadata, procedures, medications, tests, admissions, transfers, and clinician actions will be rejected.
The initial implementation will favor precision over recall and will not split complex coordinated clauses into multiple predictions.

The raw entity span will exclude list markers, Markdown emphasis, leading reporter phrases, and leading assertion cues while preserving an exact contiguous slice of the immutable source text.
Trailing delimiters and explanatory parentheticals may be excluded only by moving boundaries within the raw line.
Every result must satisfy `raw_text[start:end] == text`.
Duplicate mentions at different positions will remain separate.

## Assertions and schema

Each accepted span will be passed to the existing clause-scoped assertion classifier.
The serializer output will contain exactly `text`, `type`, `assertions`, and `position` for `TRIỆU_CHỨNG`.
No `candidates` field will be emitted for symptoms.

## Configuration and experiment isolation

`SubmissionConfig` will gain one strict boolean field named `include_symptoms`.
The loader will default an absent `include_symptoms` field to `false` so the five historical configuration files and their recorded hashes remain unchanged.
The new configuration will derive from `configs/submissions/02_add_labs.json` and change only `include_symptoms` to `true`.

The new artifact will be named `outputs/submissions/06_add_symptoms.zip`.
Its parent will be `local-s002`, not the marginal core-span variant.
The semantic diff must report only added symptom entities, with zero removed or changed existing entities and zero changed candidate sets.

## Components

`src/medical_race/extraction/symptoms.py` will contain the structural extractor and return existing `Span` values.
`src/medical_race/pipeline.py` will gate symptom serialization behind `include_symptoms` and reuse `classify_assertions` plus `validate_entities`.
`configs/submissions/06_add_symptoms.json` will define the one-variable experiment.
The existing build and diff commands will generate the artifact and its evidence reports without modification unless a tested report-count gap is discovered.

## Error handling and safety

Configuration loading will continue to reject missing required fields, extra fields, and a non-boolean `include_symptoms` value.
The extractor will return no prediction for ambiguous or structurally unsupported lines.
The existing validator will reject offset, field, assertion, and duplicate-candidate violations before packaging.
The model budget remains `0 / 9B`.

## Testing

Tests will first fail for the missing symptom extractor and configuration field.
Focused tests will cover inline chief complaints, active current-symptom bullets, negated symptoms, stop headings, metadata rejection, procedure rejection, duplicate occurrence preservation, exact offsets, and strict symptom schema.
Regression tests will verify that all five existing configurations rebuild identically and that enabling symptoms does not change existing entities.

Full verification will run the complete unit suite, bytecode compilation, strict artifact validation, semantic diff inspection, deterministic rebuild comparison, and `git diff --check`.

## Acceptance criteria

- The artifact contains exactly 100 JSON entries.
- Every symptom is an exact raw-text slice with the approved type-dependent schema.
- Every existing Submission 2 entity remains byte-for-byte unchanged.
- The semantic diff contains only added `TRIỆU_CHỨNG` entities.
- No candidate identifier, model parameter, dependency, or external runtime requirement is added.
- Independent rebuilds produce identical ZIP checksums.
- The artifact identity, checksum, config, parent, hypothesis, and diff counts are documented before upload.
