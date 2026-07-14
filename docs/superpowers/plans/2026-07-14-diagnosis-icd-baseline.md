# Diagnosis and ICD Baseline Implementation Plan

> **Goal:** Add high-precision ontology-backed diagnosis extraction to the promoted Submission 6 pipeline and produce one validated integrated artifact.

**Architecture:** A standard-library acquisition tool pins the official Vietnamese ICD-10 hierarchy as canonical JSON.
An offline reader verifies its checksum and builds an unambiguous leaf-term index.
A structural recognizer matches normalized ontology terms only in diagnosis-bearing sections while retaining exact raw offsets.
The existing pipeline adds assertions and serializes the established diagnosis schema behind a backward-compatible configuration toggle.

**Tech stack:** Python 3.11 standard library, `unittest`, public Ministry ICD hierarchy, deterministic JSON and ZIP packaging.

---

## Constraints

- Never alter raw record text or derive offsets from a mutated copy without a boundary map.
- Never emit an ICD code absent from the pinned verified snapshot.
- Do not derive aliases or manual mappings from the public test records.
- Do not access the network at prediction time.
- Keep every Submission 6 entity, assertion, position, and candidate unchanged.
- Keep active model parameters at `0 / 9B`.
- Keep the raw ICD snapshot untracked and do not redistribute it.
- Change one primary leaderboard variable by adding diagnosis output only.

### Task 1: Deterministic ICD hierarchy acquisition

**Files:**

- Create: `tools/fetch_icd10_vn.py`
- Create: `tests/test_icd_acquisition.py`
- Update: `.gitignore`
- Create locally: `ontologies/icd/icd10_vn_2020.json`

**Steps:**

1. Write failing tests with a fake hierarchy client for recursive traversal, stable ordering, duplicate collapse, conflict rejection, cycle rejection, malformed response rejection, and canonical UTF-8 JSON output.
2. Run `\.\.venv\Scripts\python.exe -m unittest tests.test_icd_acquisition -v` and confirm failure because the acquisition module does not exist.
3. Implement the smallest standard-library fetcher that satisfies the tests.
4. Run the focused test again and confirm success.
5. Add the snapshot path to `.gitignore` before acquisition.
6. Fetch the base Vietnamese catalog from `https://ccs.whiteneuron.com/api/ICD10/` with `lang=vi`.
7. Record the node count and SHA-256 without modifying the fetched snapshot.

### Task 2: Verified offline ICD reader and index

**Files:**

- Create: `src/medical_race/linking/icd10.py`
- Update: `src/medical_race/linking/__init__.py`
- Create: `tests/test_icd10.py`

**Steps:**

1. Write failing tests for checksum enforcement, schema validation, immutable terms, duplicate codes, ambiguous normalized titles, leaf preference, and exact top-one lookup.
2. Run `\.\.venv\Scripts\python.exe -m unittest tests.test_icd10 -v` and confirm the expected failure.
3. Implement `ICD10Term`, `read_icd10_snapshot`, normalization, and an unambiguous offline term index using only the standard library.
4. Run the focused tests and confirm success.
5. Verify that every indexed candidate is copied exactly from the snapshot code field.

### Task 3: Exact-offset structural diagnosis recognition

**Files:**

- Create: `src/medical_race/extraction/diagnoses.py`
- Create: `tests/test_diagnosis_extraction.py`
- Update only if required: `src/medical_race/sections/__init__.py`

**Steps:**

1. Write failing tests for explicit diagnosis sections, treatment stop headings, assessment diagnosis sub-blocks, past history, imaging, context rejection, exact raw offsets, duplicate occurrences, ambiguous terms, and longest-overlap resolution.
2. Run `\.\.venv\Scripts\python.exe -m unittest tests.test_diagnosis_extraction -v` and confirm the expected failure.
3. Implement a mapped normalized view and structural context ranges.
4. Match only unambiguous specific ontology titles inside the approved ranges.
5. Resolve overlaps by longest span and preserve non-overlapping duplicate occurrences.
6. Run diagnosis, section, offset, and extraction regression tests.

### Task 4: Backward-compatible pipeline integration

**Files:**

- Update: `src/medical_race/pipeline.py`
- Update: `tests/test_pipeline.py`
- Update: `tools/build_submission.py`
- Update: `tests/test_build_submission.py`
- Create: `configs/submissions/07_add_diagnoses.json`

**Steps:**

1. Write failing tests for `include_diagnoses`, missing or malformed values, conditional ICD loading, strict diagnosis schema, assertion attachment, sorted output, and report counters.
2. Confirm legacy configuration tests still expect diagnoses to default off.
3. Run focused tests and confirm failure before implementation.
4. Add `include_diagnoses: bool = False` as an optional configuration field.
5. Pass verified ICD terms only when diagnosis output is enabled.
6. Emit `CHẨN_ĐOÁN` with exactly `text`, `type`, `candidates`, `assertions`, and `position`.
7. Extend the build report with ICD and diagnosis counters without changing legacy report values.
8. Run focused tests and confirm success.

### Task 5: Provenance and external-data compliance

**Files:**

- Create: `ontologies/icd/PROVENANCE.json`
- Update: `ontologies/README.md`
- Update: `data/DATA_SOURCES.md`
- Update: `research/notes.md`

**Steps:**

1. Record the official application page, API base, acquisition date, catalog branch, language, national decision, snapshot checksum, node count, and acquisition command.
2. Record that no explicit redistribution license was located and that the raw snapshot is untracked, not bundled, and restricted to internal competition use.
3. Record the mapping from snapshot codes to `CHẨN_ĐOÁN.candidates` and all known target-version uncertainty.
4. Run the source-audit tests and typography checks.

### Task 6: Full corpus audit and integrated artifact

**Files:**

- Generate ignored: `outputs/submissions/07_add_diagnoses.zip`
- Generate ignored: `outputs/submissions/07_add_diagnoses.report.json`
- Generate ignored: `outputs/submissions/06_add_symptoms_to_07_add_diagnoses.diff.json`
- Create: `docs/next_submission_queue_2026-07-14-diagnoses.md`

**Steps:**

1. Run the complete test suite.
2. Build Submission 7 from canonical `input.zip`, pinned RxNorm, pinned ICD, and `configs/submissions/07_add_diagnoses.json`.
3. Diff the artifact against `outputs/submissions/06_add_symptoms.zip`.
4. Require zero removed entities and zero changes to existing entities, candidates, assertions, text, types, or positions.
5. Require every added entity to have type `CHẨN_ĐOÁN` and a candidate found in the pinned ICD snapshot.
6. Print and manually inspect every diagnosis with document, text, candidate, assertion, and position.
7. Reject or generalize any false-positive structural class through tested rules.
8. Require useful cross-document coverage before consuming a guaranteed upload slot.
9. Build twice independently and require identical artifact SHA-256 values.
10. Record config, commit, checksums, parent `local-s006`, hypothesis, counts, diff path, model budget, and exact upload artifact.

### Task 7: Leaderboard result and next phase

**Files:**

- Update after manual upload: `docs/submissions.csv`
- Create after manual upload: `docs/submission_results_2026-07-XX.md`

**Steps:**

1. Have the user upload only the validated Submission 7 ZIP.
2. Record portal score, WER, assertion Jaccard, candidate Jaccard, and record counts.
3. Decompose the score delta against Submission 6.
4. Promote only if the gain is clean, interpretable, and plausibly private-test generalizable.
5. Use the diagnosis audit misses to scope the compact model-based recognition and reranking phase.
