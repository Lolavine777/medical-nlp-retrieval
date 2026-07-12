# First Five Meaningful Submissions Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Produce five validated, non-empty, ontology-backed submission ZIP files with reproducible configurations, checksums, semantic diffs, and manual-upload instructions.

**Architecture:** A standard-library RxNorm reader loads the pinned archive directly, a deterministic lexical linker gates existing drug spans, and one configurable prediction pipeline adds assertions and optional laboratory pairs.
Existing serializer and packager boundaries create the ZIP files, while a small build command and semantic diff generate experiment evidence.

**Tech Stack:** Python 3.11 standard library, `unittest`, NLM RxNorm RRF, JSON configuration, deterministic ZIP packaging.

## Global Constraints

- Work inline on `master` as authorized.
- Keep model parameters at `0 / 9B`.
- Preserve `input.zip` and all raw document text exactly.
- Emit no RXCUI absent from `RxNorm_full_prescribe_07062026.zip`.
- Keep the raw ontology archive untracked.
- Add no dependency, model, network call at runtime, ICD code, symptom guess, or diagnosis guess.
- Never upload `outputs/NON_SUBMITTABLE-empty-output.zip`.
- Run every implementation change through RED, GREEN, and full verification.

---

### Task 1: Pinned RxNorm acquisition and RRF reader

**Files:**

- Create untracked: `ontologies/rxnorm/RxNorm_full_prescribe_07062026.zip`
- Create: `ontologies/rxnorm/PROVENANCE.json`
- Modify: `.gitignore`
- Create: `src/medical_race/linking/__init__.py`
- Create: `src/medical_race/linking/rxnorm.py`
- Create: `tests/test_rxnorm.py`

**Interfaces:**

- Produces: `RxNormTerm(rxcui, text, term_type, source, preferred)`.
- Produces: `read_rxnorm_archive(path, expected_md5) -> tuple[RxNormTerm, ...]`.
- Produces: a committed provenance record with the archive identity and legal status.

- [ ] **Step 1: Download and verify the dated no-license archive**

Download `https://download.nlm.nih.gov/umls/kss/rxnorm/RxNorm_full_prescribe_07062026.zip` to the exact untracked path.
Verify published MD5 `767678e3b5b1d6fe358b61c21659f3ef`, compute SHA-256, list members, and inspect the included README before writing provenance.

- [ ] **Step 2: Write the failing RRF tests**

Build a tiny in-memory ZIP containing `rrf/RXNCONSO.RRF` rows with the 18 documented fields plus trailing delimiter.
Test that English, unsuppressed `RXNORM` and `MTHSPL` rows load; suppressed, non-English, and unsupported-source rows do not; malformed rows and MD5 mismatches raise `ValueError`.

- [ ] **Step 3: Run RED**

```powershell
$env:PYTHONPATH='src'
.\.venv\Scripts\python.exe -m unittest tests.test_rxnorm -v
```

Expected: import failure because `medical_race.linking.rxnorm` does not exist.

- [ ] **Step 4: Implement the minimal reader**

Use `hashlib.md5`, `zipfile.ZipFile`, strict UTF-8 decoding, a frozen slotted dataclass, and exact RRF column indices.
Reject missing or duplicate `RXNCONSO.RRF` members and archives whose MD5 differs from the explicit expected value.

```python
@dataclass(frozen=True, slots=True)
class RxNormTerm:
    rxcui: str
    text: str
    term_type: str
    source: str
    preferred: bool


def read_rxnorm_archive(path: Path, expected_md5: str) -> tuple[RxNormTerm, ...]: ...
```

- [ ] **Step 5: Run GREEN and commit**

Run the focused tests, then commit reader, test, provenance, and ignore changes with `feat: ingest pinned rxnorm content`.

---

### Task 2: Deterministic lexical drug linker

**Files:**

- Modify: `src/medical_race/linking/rxnorm.py`
- Modify: `tests/test_rxnorm.py`

**Interfaces:**

- Consumes: extracted raw drug span text and immutable RxNorm terms.
- Produces: `LinkResult(candidates, matched_text)` or `None`.
- Produces: `link_drug(text, terms, concept_level="all_retrievable", candidate_output="top1")`.

- [ ] **Step 1: Write failing ranking tests**

Cover generic `metoprolol`, brand `Seroquel`, regimen `aspirin 325mg daily`, duplicate RXCUI collapse, exact-match preference, deterministic tie order, ingredient-only filtering, top-one, top-two, and noisy unmatched treatment phrases.

- [ ] **Step 2: Run RED**

Run `tests.test_rxnorm` and confirm failure because `link_drug` is missing.

- [ ] **Step 3: Implement the minimum linker**

Normalize with case folding, punctuation-to-space conversion, and whitespace collapse.
Use token-bounded substring matches in either direction.
Rank exact normalized match, longer matched term, `RXNORM` source, preferred flag, then RXCUI numeric order.
Collapse to one result per RXCUI before applying term-type and candidate-count policy.

```python
@dataclass(frozen=True, slots=True)
class LinkResult:
    candidates: tuple[str, ...]
    matched_text: str


def link_drug(
    text: str,
    terms: tuple[RxNormTerm, ...],
    concept_level: str = "all_retrievable",
    candidate_output: str = "top1",
) -> LinkResult | None: ...
```

- [ ] **Step 4: Run GREEN and commit**

Run focused and full tests, then commit with `feat: add lexical rxnorm linker`.

---

### Task 3: Configurable prediction pipeline and five configs

**Files:**

- Create: `src/medical_race/pipeline.py`
- Create: `tests/test_pipeline.py`
- Create: `configs/submissions/01_drugs_top1.json`
- Create: `configs/submissions/02_add_labs.json`
- Create: `configs/submissions/03_core_spans.json`
- Create: `configs/submissions/04_ingredient_only.json`
- Create: `configs/submissions/05_top2.json`

**Interfaces:**

- Produces: frozen `SubmissionConfig` with `include_labs`, `span_policy`, `concept_level`, and `candidate_output`.
- Produces: `load_submission_config(path) -> SubmissionConfig`.
- Produces: `predict_document(raw_text, terms, config) -> list[dict[str, object]]`.

- [ ] **Step 1: Write failing pipeline tests**

Use tiny local RxNorm terms and raw documents.
Test linked drugs with assertions, rejection of unlinked noise, duplicate occurrence preservation, laboratory toggle, core offset recovery, regimen-inclusive spans, candidate policies, sorted positions, and strict serializer validation.

- [ ] **Step 2: Run RED**

Run `tests.test_pipeline` and confirm import failure.

- [ ] **Step 3: Implement the minimum pipeline**

Reuse `extract_drugs`, `extract_labs`, `classify_assertions`, `link_drug`, and `validate_entities`.
Recover core spans with a case-insensitive escaped raw-term search and require exactly one match inside the extracted span.
Do not add a second extraction path.

```python
@dataclass(frozen=True, slots=True)
class SubmissionConfig:
    include_labs: bool
    span_policy: str
    concept_level: str
    candidate_output: str


def load_submission_config(path: Path) -> SubmissionConfig: ...


def predict_document(
    raw_text: str,
    terms: tuple[RxNormTerm, ...],
    config: SubmissionConfig,
) -> list[dict[str, object]]: ...
```

- [ ] **Step 4: Add the five one-variable configurations**

Configuration 1 uses drugs only, regimen-inclusive spans, all retrievable concepts, and top one.
Configuration 2 changes only `include_labs` to true.
Configuration 3 derives from 2 and changes only `span_policy` to core.
Configuration 4 derives from 2 and changes only `concept_level` to ingredient.
Configuration 5 derives from 2 and changes only `candidate_output` to top two.

- [ ] **Step 5: Run GREEN and commit**

Run focused and full tests, then commit with `feat: build configurable clinical predictions`.

---

### Task 4: Reproducible builder and semantic diff

**Files:**

- Create: `tools/build_submission.py`
- Create: `src/medical_race/submission_diff.py`
- Create: `tools/diff_submissions.py`
- Create: `tests/test_build_submission.py`
- Create: `tests/test_submission_diff.py`

**Interfaces:**

- Produces: `build_submission(input_zip, rxnorm_zip, config_path, destination) -> dict`.
- Produces: `diff_submission_archives(parent, child) -> dict`.
- Produces: command-line JSON reports with deterministic sorting and UTF-8 output.

- [ ] **Step 1: Write failing build and diff tests**

Use temporary 100-document input ZIPs and tiny ontology ZIPs.
Test deterministic output checksum, ontology membership, non-empty entity counts, existing-destination refusal, report fields, added laboratory entities, changed core spans, changed candidates, and unchanged parent inputs.

- [ ] **Step 2: Run RED**

Run both focused test modules and confirm missing imports.

- [ ] **Step 3: Implement the builder**

Reuse `read_zip_documents`, `read_rxnorm_archive`, `predict_document`, and `build_output_zip`.
Include input, ontology, config, and output SHA-256 values plus entity, type, candidate, assertion, linked, dropped, and empty-document counts.

- [ ] **Step 4: Implement semantic diff**

Read both archives, identify entities by document plus exact type/text/position, and report additions, removals, and field changes deterministically.
Count changed entities, candidates, assertions, text, type, and position.

- [ ] **Step 5: Run GREEN and commit**

Run focused and full tests, then commit with `feat: build and diff submission artifacts`.

---

### Task 5: Generate and verify the upload queue

**Files:**

- Generate ignored: `outputs/submissions/01_drugs_top1.zip`
- Generate ignored: `outputs/submissions/02_add_labs.zip`
- Generate ignored: `outputs/submissions/03_core_spans.zip`
- Generate ignored: `outputs/submissions/04_ingredient_only.zip`
- Generate ignored: `outputs/submissions/05_top2.zip`
- Generate ignored: matching build and diff JSON reports
- Create: `docs/first_five_submission_queue_2026-07-12.md`
- Update after portal results: `docs/submissions.csv`

**Interfaces:**

- Produces: five artifacts ready for manual portal upload in numerical order.
- Produces: exact checksum, commit, config, parent, hypothesis, changed counts, and expected portal logging fields for each artifact.

- [ ] **Step 1: Generate all five artifacts**

Build each configuration from canonical `input.zip` and the pinned RxNorm archive.
Generate diffs from submission 1 to 2 and from submission 2 to 3, 4, and 5.

- [ ] **Step 2: Audit real corpus predictions**

Inspect every linked drug surface, RXCUI, term type, assertion, core-span change, laboratory pair, and top-two expansion.
Fix extraction or linking errors only through a failing regression test.

- [ ] **Step 3: Verify acceptance gates**

Require 100 JSON entries per ZIP, non-empty distinct predictions, zero invalid offsets, zero identifiers outside the archive, deterministic rebuild equality, and exactly one primary change per child config.

Run:

```powershell
$env:PYTHONPATH='src;.'
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -m compileall -q src tools tests
git diff --check
```

- [ ] **Step 4: Write and commit the upload queue**

Record filenames, SHA-256 values, configs, commits, parents, hypotheses, diffs, counts, upload order, and the warning against the empty artifact.
Commit with `docs: prepare first five submission queue`.

- [ ] **Step 5: Manual upload feedback loop**

The user checks portal quota, uploads artifact 1, and returns its submission ID and score.
Record the result before choosing or uploading artifact 2.
Repeat through five scored submissions, replacing a later variant only when an earlier grade makes a higher-information one-variable experiment preferable.
