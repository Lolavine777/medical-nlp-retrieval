# Parent-Preserving Model Augmentation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a deterministic augmentation command that preserves every validated parent prediction and adds only grounded model proposals that pass the existing precision gates.

**Architecture:** A new tool reads the canonical input, validates and loads a parent submission, validates the existing proposal directory, and calls `accept_model_proposals` with the parent entities as stable evidence. It builds the child archive in a temporary directory, validates and diffs it against the parent, then atomically publishes it only when the parent-preservation gate passes.

**Tech Stack:** Python 3.12 standard library, existing `medical_race` extraction/linking/submission modules, `unittest`, pinned local ICD-10 and RxNorm snapshots.

## Global Constraints

- Never mutate raw text, whitespace, line endings, duplicate mentions, ontology files, or parent entity values.
- Every new span must satisfy `raw_text[start:end] == text`.
- Only existing pinned ICD-10 and RxNorm linkers may create candidate identifiers.
- Active model parameters remain exactly `4_000_000_000`, below the `9B` limit.
- The first artifact uses `outputs/submissions/08_qwen_grounded.zip` and the original non-salvaged `outputs/model_proposals/qwen3-4b-s010-original/qwen3-4b-s010` directory.
- The first artifact must retain exactly 150 candidates and have zero removed or changed parent entities.
- Do not add dependencies or modify rule extractors, prompts, candidate cardinality, or raw data.

---

## File Structure

- Create `tools/augment_submission.py` for parent loading, proposal augmentation, promotion gating, reporting, and CLI handling.
- Create `tests/test_augment_submission.py` for the end-to-end preservation contract and trust-boundary failures.
- Create `docs/next_submission_queue_2026-07-18-s011.md` only if the real local artifact passes every promotion gate.
- Produce ignored artifacts under `outputs/submissions/` without committing them.

### Task 1: Preserve parent entities while accepting new proposals

**Files:**
- Create: `tests/test_augment_submission.py`
- Create: `tools/augment_submission.py`

**Interfaces:**
- Consumes: `read_zip_documents`, `validate_document_names`, `validate_output_zip`, `read_proposal_directory`, `read_proposal_manifest`, `accept_model_proposals`, `build_output_zip`, and the pinned ontology readers.
- Produces: `augment_submission(input_zip: Path, parent_zip: Path, proposal_root: Path, rxnorm_zip: Path, config_path: Path, destination: Path, icd_path: Path = DEFAULT_ICD10_PATH, expected_md5: str = PUBLISHED_RXNORM_MD5, expected_icd_sha256: str = PINNED_ICD10_SHA256) -> dict[str, object]`.

- [ ] **Step 1: Write the failing end-to-end preservation test**

Create `tests/test_augment_submission.py` with helpers that write 100 canonical UTF-8 documents, a minimal RxNorm archive, a model-enabled configuration, a valid parent archive, and a prompt-version-2 proposal directory.
The first document must contain `đau cũ` and `đau mới` on separate symptom lines.
The parent must contain only `đau cũ`.
The proposal response must contain both spans so one item is rejected for parent overlap and one is accepted.

The central assertion must be equivalent to:

```python
report = augment_submission(
    input_zip,
    parent_zip,
    proposals,
    rxnorm_zip,
    config,
    child_zip,
    expected_md5=rxnorm_md5,
)

with zipfile.ZipFile(parent_zip) as parent, zipfile.ZipFile(child_zip) as child:
    parent_entities = json.loads(parent.read("output/1.json"))
    child_entities = json.loads(child.read("output/1.json"))

self.assertEqual(child_entities[0], parent_entities[0])
self.assertEqual([entity["text"] for entity in child_entities], ["đau cũ", "đau mới"])
self.assertEqual(report["model_added_entity_count"], 1)
self.assertEqual(report["model_rejections"]["stable_overlap"], 1)
self.assertEqual(report["diff"]["added_entities"], 1)
self.assertEqual(report["diff"]["removed_entities"], 0)
self.assertEqual(report["diff"]["changed_entities"], 0)
validate_output_zip(child_zip, documents)
```

- [ ] **Step 2: Run the focused test and verify the expected failure**

Run:

```powershell
$env:PYTHONPATH = "src;."
& "C:\Users\DELL\Documents\medical2-race-viettel\.venv\Scripts\python.exe" -m unittest tests.test_augment_submission -v
```

Expected result: `ModuleNotFoundError` for `tools.augment_submission`.

- [ ] **Step 3: Implement the minimum parent reader and augmentation function**

Implement a private `_read_parent_predictions(path, documents)` that first calls `validate_output_zip` and then maps `input/1.txt` through `input/100.txt` to the decoded JSON lists from `output/1.json` through `output/100.json`.
Use `zipfile.ZipFile`, `INPUT_NAMES`, and `OUTPUT_NAMES` from the standard library and existing submission module.

Implement `augment_submission` with this flow:

```python
documents = read_zip_documents(input_zip)
validate_document_names(list(documents))
parent_predictions = _read_parent_predictions(parent_zip, documents)
config = load_submission_config(config_path)
if not config.include_model_proposals:
    raise ValueError("augmentation config must enable model proposals")
proposals = read_proposal_directory(proposal_root, documents)
manifest = read_proposal_manifest(proposal_root)
terms = read_rxnorm_archive(rxnorm_zip, expected_md5)
icd_index = (
    build_term_index(read_icd10_snapshot(icd_path, expected_icd_sha256))
    if config.include_diagnoses
    else {}
)

model_report = Counter()
predictions = {}
for name, raw_text in documents.items():
    parent_entities = parent_predictions[name]
    result = accept_model_proposals(
        raw_text,
        proposals[name],
        parent_entities,
        terms,
        icd_index,
        config.concept_level,
        config.candidate_output,
    )
    model_report.update(result.rejected)
    predictions[name] = sorted(
        [*parent_entities, *result.entities],
        key=lambda entity: (
            entity["position"][0],
            entity["position"][1],
            entity["type"],
        ),
    )
```

Build and validate the child archive in a `TemporaryDirectory` under the destination parent.
Call `diff_submission_archives(parent_zip, temporary_zip)` before publishing.
Reject the build when any removed or changed counter is nonzero, the candidate count differs from the parent, or no entity was added.
Move the temporary archive to `destination` only after those checks pass.

- [ ] **Step 4: Run the focused test and verify it passes**

Run the focused command from Step 2.

Expected result: one passing test with the parent entity unchanged and one accepted addition.

- [ ] **Step 5: Commit the parent-preserving core**

```powershell
git add tools/augment_submission.py tests/test_augment_submission.py
git commit -m "feat: preserve parent predictions during model augmentation"
```

### Task 2: Enforce trust boundaries and produce a reproducible report

**Files:**
- Modify: `tests/test_augment_submission.py`
- Modify: `tools/augment_submission.py`

**Interfaces:**
- Consumes: `augment_submission` from Task 1.
- Produces: a report with hashes, model identity, counts, rejection buckets, semantic diff summary, and promotion eligibility, plus a command-line interface with equivalent path arguments.

- [ ] **Step 1: Add failing trust-boundary and reporting tests**

Add tests that:

1. Corrupt a parent entity offset and assert `augment_submission` raises `ValueError` before creating the destination.
2. Change one proposal document's `raw_sha256` and assert the function raises an input hash mismatch before creating the destination.
3. Verify the successful report contains `parent_sha256`, `input_sha256`, `config_sha256`, `ontology_sha256`, `output_sha256`, `model_id`, `model_revision`, `model_parameters`, `model_proposal_count`, `model_added_entity_count`, `model_rejections`, `candidate_count`, `assertion_count`, `entity_counts`, `diff`, and `promotion_eligible`.
4. Verify `promotion_eligible` is true only when all preservation counters are zero, candidate count is unchanged, and at least one entity is added.

- [ ] **Step 2: Run the focused tests and verify they fail**

Run:

```powershell
$env:PYTHONPATH = "src;."
& "C:\Users\DELL\Documents\medical2-race-viettel\.venv\Scripts\python.exe" -m unittest tests.test_augment_submission -v
```

Expected result: failures for missing report fields or missing CLI behavior while the Task 1 preservation test remains green.

- [ ] **Step 3: Add the report and CLI without duplicating build logic**

Use existing `sha256`, manifest, package, preflight, and semantic diff values to create one report dictionary.
Exclude `details` from the nested `diff` report so the summary stays compact.
Set `promotion_eligible` from the same predicate used before publishing the destination.

Add CLI arguments:

```text
--input
--parent
--model-proposals
--rxnorm
--config
--icd
--output
--report
--expected-md5
--expected-icd-sha256
```

Write the JSON report with UTF-8, indentation, deterministic key ordering, and exclusive creation.
Print the report with `ensure_ascii=True` for stable Windows and Kaggle consoles.

- [ ] **Step 4: Run focused and full verification**

Run:

```powershell
$env:PYTHONPATH = "src;."
& "C:\Users\DELL\Documents\medical2-race-viettel\.venv\Scripts\python.exe" -m unittest tests.test_augment_submission -v
& "C:\Users\DELL\Documents\medical2-race-viettel\.venv\Scripts\python.exe" -m unittest discover -s tests -q
& "C:\Users\DELL\Documents\medical2-race-viettel\.venv\Scripts\python.exe" -m compileall -q src tools tests
git diff --check
```

Expected result: all focused tests pass, the full suite reports zero failures, compilation exits zero, and `git diff --check` emits no errors.

- [ ] **Step 5: Commit the validated CLI and report**

```powershell
git add tools/augment_submission.py tests/test_augment_submission.py
git commit -m "feat: gate and report parent-preserving augmentation"
```

### Task 3: Build and audit the real Submission 11 candidate

**Files:**
- Create when eligible: `docs/next_submission_queue_2026-07-18-s011.md`
- Create ignored: `outputs/submissions/11_parent_preserving_qwen.zip`
- Create ignored: `outputs/submissions/11_parent_preserving_qwen.report.json`
- Create ignored: `outputs/submissions/08_qwen_grounded_to_11_parent_preserving_qwen.diff.json`

**Interfaces:**
- Consumes: `tools/augment_submission.py`, Submission 8, the original Submission 10 proposal directory, the canonical input, pinned ontologies, and `configs/submissions/10_qwen_targeted.json`.
- Produces: one locally validated parent-preserving archive and an evidence-backed upload recommendation or rejection.

- [ ] **Step 1: Build the real augmentation artifact**

Run:

```powershell
$env:PYTHONPATH = "src;."
$env:PYTHONIOENCODING = "utf-8"
& "C:\Users\DELL\Documents\medical2-race-viettel\.venv\Scripts\python.exe" tools\augment_submission.py `
  --input input.zip `
  --parent outputs\submissions\08_qwen_grounded.zip `
  --model-proposals outputs\model_proposals\qwen3-4b-s010-original\qwen3-4b-s010 `
  --config configs\submissions\10_qwen_targeted.json `
  --output outputs\submissions\11_parent_preserving_qwen.zip `
  --report outputs\submissions\11_parent_preserving_qwen.report.json
```

Expected result: the report records 4B active parameters, exactly 150 candidates, at least one accepted addition, zero removed entities, and zero changed entities.

- [ ] **Step 2: Independently validate and diff the archive**

Run:

```powershell
& "C:\Users\DELL\Documents\medical2-race-viettel\.venv\Scripts\python.exe" tools\validate_submission.py `
  --input input.zip outputs\submissions\11_parent_preserving_qwen.zip
& "C:\Users\DELL\Documents\medical2-race-viettel\.venv\Scripts\python.exe" tools\diff_submissions.py `
  outputs\submissions\08_qwen_grounded.zip `
  outputs\submissions\11_parent_preserving_qwen.zip `
  --output outputs\submissions\08_qwen_grounded_to_11_parent_preserving_qwen.diff.json
```

Expected result: validation passes and the independent diff matches the nested report summary.

- [ ] **Step 3: Audit accepted additions and decide whether to queue**

Inspect every `added` detail in the independent diff.
Reject the artifact if any addition is a heading, metadata, procedure, treatment action, normal-state description, whole sentence, or structurally implausible type assignment.
Do not weaken the gate to make the artifact pass.

- [ ] **Step 4: Document an eligible artifact**

Only when every gate passes, create `docs/next_submission_queue_2026-07-18-s011.md` containing the parent, commit, config, input and output checksums, proposal manifest identity, entity and candidate counts, diff summary, hypothesis, and explicit statement that portal scoring is still required before promotion.
If review fails, do not create a queue document and retain the archive only as a diagnostic artifact.

- [ ] **Step 5: Run final verification and commit the queue decision**

Run the focused tests, full test suite, compilation, validator, and diff commands again after any documentation change.
If a queue document was created, commit it with:

```powershell
git add docs/next_submission_queue_2026-07-18-s011.md
git commit -m "docs: queue parent-preserving Qwen probe"
```

If no queue document was created, make no documentation commit and report the failed review evidence.
