# Grounded Qwen Proposals Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add reproducible Qwen3-4B mention proposals to Submission 7 while allowing only deterministically grounded, linked, schema-valid additions into the final output.

**Architecture:** A model-only CLI runs the pinned Qwen checkpoint on bounded raw-line chunks and writes strict per-document proposal files.
The existing submission builder validates those files against input checksums, grounds exact text to raw offsets, applies section and overlap gates, links required ICD or RxNorm candidates, derives assertions, and merges accepted additions over unchanged Submission 7 entities.
The core package remains importable without model dependencies because Transformers and PyTorch are loaded only by the generation CLI.

**Tech Stack:** Python 3.11 standard library, existing `unittest` suite, PyTorch supplied by Kaggle or Colab, `transformers==4.51.0`, pinned Qwen3-4B BF16 safetensors, existing ICD-10 and RxNorm linkers.

## Global Constraints

- Never mutate raw text, whitespace, line endings, or duplicate mentions.
- Require `raw_text[start:end] == text` for every entity.
- Keep Submission 7 byte-identical when model proposals are disabled.
- Model proposals may add entities but may never remove or modify a Submission 7 entity.
- Use only `Qwen/Qwen3-4B-Instruct-2507` revision `1b4199c4f36b0cef378bfb12390c18780c18af4c`.
- Report active parameters as exactly `4,000,000,000 / 9,000,000,000`.
- Do not load or call a second model.
- Do not call a hosted inference API.
- Reject diagnosis and drug proposals that do not receive a pinned top-one candidate.
- Do not add document-specific rules, prompt examples, corrections, or cached answers as program logic.
- Keep model output files, weights, raw ontologies, and generated submissions untracked.
- Run every Python command through `.venv` locally or the notebook environment on Kaggle or Colab.

---

### Task 1: Pin model provenance and the parameter budget

**Files:**

- Create: `requirements-model.txt`
- Create: `tests/test_model_budget.py`
- Modify: `configs/model_budget.json`
- Modify: `configs/model_configurations.json`
- Modify: `data/DATA_SOURCES.md`
- Modify: `.gitignore`

**Interfaces:**

- Consumes: The organizer-confirmed `9,000,000,000` combined parameter limit.
- Produces: Model identifier `qwen3_4b_instruct_2507`, exact revision, `4,000,000,000` parameters, Apache-2.0 provenance, and ignored model-output paths.

- [ ] **Step 1: Write the failing budget test**

Create `tests/test_model_budget.py` with checks equivalent to:

```python
import json
import unittest
from pathlib import Path


class ModelBudgetTest(unittest.TestCase):
    def test_qwen_configuration_is_pinned_and_compliant(self):
        budget = json.loads(Path("configs/model_budget.json").read_text(encoding="utf-8"))
        configurations = json.loads(
            Path("configs/model_configurations.json").read_text(encoding="utf-8")
        )
        model = next(value for value in budget["models"] if value["id"] == "qwen3_4b_instruct_2507")
        self.assertEqual(model["revision"], "1b4199c4f36b0cef378bfb12390c18780c18af4c")
        self.assertEqual(model["parameters"], 4_000_000_000)
        self.assertEqual(model["license"], "Apache-2.0")
        active = next(
            value
            for value in configurations["configurations"]
            if value["id"] == "qwen_grounded_proposals"
        )
        self.assertEqual(active["active_model_ids"], [model["id"]])
        self.assertEqual(active["combined_parameters"], model["parameters"])
        self.assertLessEqual(active["combined_parameters"], configurations["budget_limit_parameters"])
        self.assertFalse(active["unused_checkpoints_included"])


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the focused test and verify RED**

Run:

```powershell
$env:PYTHONPATH='src'; .\.venv\Scripts\python.exe -m unittest tests.test_model_budget -v
```

Expected: FAIL because the Qwen model and configuration entries do not exist.

- [ ] **Step 3: Add the minimal provenance and budget records**

Add one model object to `configs/model_budget.json`:

```json
{
  "id": "qwen3_4b_instruct_2507",
  "source": "Qwen/Qwen3-4B-Instruct-2507",
  "revision": "1b4199c4f36b0cef378bfb12390c18780c18af4c",
  "parameters": 4000000000,
  "license": "Apache-2.0",
  "purpose": "Clinical mention proposals before deterministic grounding"
}
```

Add one experimental configuration to `configs/model_configurations.json` with `active_model_ids` containing only `qwen3_4b_instruct_2507`, `combined_parameters` equal to `4000000000`, `compliant` true, and `unused_checkpoints_included` false.

Create `requirements-model.txt` containing only:

```text
transformers==4.51.0
accelerate==1.6.0
safetensors==0.5.3
```

Record the model source, revision, parameter count, Apache-2.0 license, acquisition through `from_pretrained(..., revision=...)`, no-redistribution default, label mapping, and proposal-only use in `data/DATA_SOURCES.md`.

Ignore:

```gitignore
models/
outputs/model_proposals/
outputs/kaggle/
```

- [ ] **Step 4: Run GREEN and commit**

Run the focused test and `git diff --check`.

Commit:

```powershell
git add requirements-model.txt tests/test_model_budget.py configs/model_budget.json configs/model_configurations.json data/DATA_SOURCES.md .gitignore
git commit -m "chore: pin qwen proposal model"
```

---

### Task 2: Parse, chunk, and exactly ground model proposals

**Files:**

- Create: `src/medical_race/model_proposals.py`
- Create: `tests/test_model_proposals.py`

**Interfaces:**

- Produces: `ModelProposal(line_index: int, text: str, entity_type: str)`.
- Produces: `PromptChunk(line_indices: tuple[int, ...], prompt: str)`.
- Produces: `GroundedProposal(span: Span, entity_type: str, section: str, role: str)`.
- Produces: `parse_model_response(value: str) -> tuple[ModelProposal, ...]`.
- Produces: `prompt_chunks(raw_text: str, max_chars: int = 6000) -> tuple[PromptChunk, ...]`.
- Produces: `ground_proposals(raw_text: str, proposals: tuple[ModelProposal, ...]) -> tuple[GroundedProposal, ...]`.

- [ ] **Step 1: Write strict parsing and grounding tests**

Create tests that cover:

```python
def test_parses_only_exact_three_field_objects(self):
    value = '[{"line_index":1,"text":"đau ngực","type":"TRIỆU_CHỨNG"}]'
    self.assertEqual(
        parse_model_response(value),
        (ModelProposal(1, "đau ngực", "TRIỆU_CHỨNG"),),
    )

def test_rejects_markdown_unknown_fields_bad_indices_and_unknown_types(self):
    invalid = [
        '```json\n[]\n```',
        '[{"line_index":0,"text":"ho","type":"TRIỆU_CHỨNG","score":1}]',
        '[{"line_index":true,"text":"ho","type":"TRIỆU_CHỨNG"}]',
        '[{"line_index":0,"text":"ho","type":"OTHER"}]',
    ]
    for value in invalid:
        with self.subTest(value=value), self.assertRaises(ValueError):
            parse_model_response(value)

def test_grounds_every_exact_duplicate_and_rejects_normalized_text(self):
    raw = "Triệu chứng hiện tại\n- đau ngực, đau ngực\n"
    grounded = ground_proposals(
        raw,
        (ModelProposal(1, "đau ngực", "TRIỆU_CHỨNG"),),
    )
    self.assertEqual([value.span.text for value in grounded], ["đau ngực", "đau ngực"])
    for value in grounded:
        self.assertEqual(raw[value.span.start:value.span.end], value.span.text)
    with self.assertRaisesRegex(ValueError, "not found verbatim"):
        ground_proposals(raw, (ModelProposal(1, "dau nguc", "TRIỆU_CHỨNG"),))
```

Add chunk tests requiring global line indices, no split line, no blank-only chunk, deterministic prompts, and every nonblank line appearing exactly once.

- [ ] **Step 2: Run the focused test and verify RED**

Run:

```powershell
$env:PYTHONPATH='src'; .\.venv\Scripts\python.exe -m unittest tests.test_model_proposals -v
```

Expected: FAIL because `medical_race.model_proposals` does not exist.

- [ ] **Step 3: Implement the strict standard-library core**

Use frozen slot dataclasses and the existing `Span` and `parse_line_roles` interfaces.
Define exactly these allowed types:

```python
ALLOWED_TYPES = {
    "TRIỆU_CHỨNG",
    "TÊN_XÉT_NGHIỆM",
    "KẾT_QUẢ_XÉT_NGHIỆM",
    "CHẨN_ĐOÁN",
    "THUỐC",
}
MODEL_ID = "Qwen/Qwen3-4B-Instruct-2507"
MODEL_REVISION = "1b4199c4f36b0cef378bfb12390c18780c18af4c"
MODEL_PARAMETERS = 4_000_000_000
PROMPT_VERSION = 1
```

`parse_model_response` must accept a JSON array only, require exactly `line_index`, `text`, and `type`, reject booleans as indices, reject empty text, and preserve returned order.

`prompt_chunks` must use `parse_line_roles`, retain global line indices, stop before adding a line that would exceed `max_chars`, and render one generic instruction plus lines formatted as `<index>\t<raw line>`.

`ground_proposals` must validate the line index, locate every non-overlapping verbatim occurrence inside the selected line, convert line-relative positions to raw offsets, attach the existing section and role, and return deterministic `(start, end, type)` order.

- [ ] **Step 4: Run GREEN and commit**

Run the focused tests plus `tests.test_line_roles`, then commit:

```powershell
git add src/medical_race/model_proposals.py tests/test_model_proposals.py
git commit -m "feat: ground strict model proposals"
```

---

### Task 3: Accept linked additions without changing the stable baseline

**Files:**

- Modify: `src/medical_race/linking/icd10.py`
- Modify: `src/medical_race/extraction/diagnoses.py`
- Modify: `src/medical_race/pipeline.py`
- Create: `tests/test_model_pipeline.py`
- Modify: `tests/test_diagnosis_code_policy.py`

**Interfaces:**

- Consumes: `GroundedProposal`, existing RxNorm terms, verified ICD index, and stable entities.
- Produces: `is_diagnosis_code(code: str) -> bool` as the shared ICD policy.
- Produces: `ModelMergeResult(entities: tuple[dict[str, object], ...], rejected: dict[str, int])`.
- Produces: `accept_model_proposals(...) -> ModelMergeResult` in `model_proposals.py`.
- Extends: `SubmissionConfig.include_model_proposals: bool = False`.
- Extends: `predict_document(..., model_proposals=(), model_report=None)` without changing existing callers.

- [ ] **Step 1: Write failing acceptance and regression tests**

Tests must prove:

```python
def test_accepts_grounded_symptom_and_derives_assertion(self):
    raw = "Triệu chứng hiện tại\n- không đau ngực\n"
    proposals = (ModelProposal(1, "đau ngực", "TRIỆU_CHỨNG"),)
    entities = predict_document(
        raw,
        (),
        config(include_symptoms=False, include_model_proposals=True),
        model_proposals=proposals,
    )
    self.assertEqual(entities[0]["assertions"], ["isNegated"])
    self.assertEqual(raw[slice(*entities[0]["position"])], "đau ngực")

def test_rejects_unlinked_diagnosis_and_drug(self):
    raw = "Chẩn đoán\nBệnh không có trong ontology\nThuốc: thuốc lạ\n"
    proposals = (
        ModelProposal(1, "Bệnh không có trong ontology", "CHẨN_ĐOÁN"),
        ModelProposal(2, "thuốc lạ", "THUỐC"),
    )
    report = Counter()
    entities = predict_document(
        raw,
        (),
        config(include_model_proposals=True),
        icd_index={},
        model_proposals=proposals,
        model_report=report,
    )
    self.assertEqual(entities, [])
    self.assertEqual(report["unlinked_candidate"], 2)
```

Add tests for type-compatible sections, header and blank rejection, stable-overlap precedence, ambiguous same-span type rejection, model-model longest non-overlap selection, exact ICD and RxNorm top-one linking, R and U82-U85 ICD rejection, and zero stable changes.

Add a regression test that rebuilding every existing config with no proposals returns the same predictions as before this task.

- [ ] **Step 2: Run focused tests and verify RED**

Run:

```powershell
$env:PYTHONPATH='src'; .\.venv\Scripts\python.exe -m unittest tests.test_model_pipeline tests.test_diagnosis_code_policy tests.test_pipeline tests.test_diagnosis_pipeline -v
```

Expected: FAIL because the model toggle, acceptance function, and shared code policy do not exist.

- [ ] **Step 3: Centralize the diagnosis-code gate**

Move the existing R and U82-U85 exclusion into public `is_diagnosis_code` in `linking/icd10.py`.
Update `extraction/diagnoses.py` to call that shared function without changing its output.

- [ ] **Step 4: Implement deterministic acceptance**

Use these section sets:

```python
TYPE_SECTIONS = {
    "TRIỆU_CHỨNG": {"unsectioned", "current_illness", "symptoms", "admission_reason", "course", "exam", "assessment"},
    "TÊN_XÉT_NGHIỆM": {"laboratory", "assessment"},
    "KẾT_QUẢ_XÉT_NGHIỆM": {"laboratory", "assessment"},
    "CHẨN_ĐOÁN": {"past_history", "diagnosis", "imaging", "assessment"},
    "THUỐC": {"medications", "course", "assessment"},
}
```

Reject header and blank line roles.
Drop any proposal overlapping a stable entity.
Deduplicate identical grounded proposals.
Reject all same-span proposals when more than one type remains.
Select remaining model proposals by longest span, then earliest start, then type, while preventing model-model overlap.

Build entities with the existing linkers, assertion classifier, type-specific fields, and validator.
Update the optional report counter with `invalid_section`, `stable_overlap`, `ambiguous_type`, `model_overlap`, `unlinked_candidate`, and `accepted`.

- [ ] **Step 5: Add the backward-compatible toggle**

Add `include_model_proposals` to `OPTIONAL_CONFIG_FIELDS` and `SubmissionConfig` with default false and strict boolean validation.
When enabled, ground and accept supplied proposals after all existing rule entities have been built.
When disabled, ignore any supplied proposal argument and preserve existing output exactly.

- [ ] **Step 6: Run GREEN and commit**

Run focused tests and the full suite, then commit:

```powershell
git add src/medical_race/linking/icd10.py src/medical_race/extraction/diagnoses.py src/medical_race/pipeline.py src/medical_race/model_proposals.py tests/test_model_pipeline.py tests/test_diagnosis_code_policy.py
git commit -m "feat: merge grounded model additions"
```

---

### Task 4: Generate resumable proposal files on free GPU compute

**Files:**

- Create: `tools/generate_model_proposals.py`
- Create: `tests/test_generate_model_proposals.py`

**Interfaces:**

- Consumes: Canonical input ZIP and the pinned local or downloadable model snapshot.
- Produces: `<output>/manifest.json` and `<output>/documents/<number>.json`.
- Produces: `generate_document(raw_text: str, generate: Callable[[str], str]) -> dict[str, object]` for dependency-free tests.
- Produces: `read_proposal_directory(root: Path, documents: Mapping[str, str]) -> dict[str, tuple[ModelProposal, ...]]` in `model_proposals.py`.

- [ ] **Step 1: Write failing storage, resume, and fake-generation tests**

Use a fake `generate` callable and temporary directories to require:

```python
def test_generate_document_parses_chunks_and_counts_fail_closed_errors(self):
    responses = iter([
        '[{"line_index":1,"text":"đau ngực","type":"TRIỆU_CHỨNG"}]',
        "not json",
    ])
    result = generate_document(RAW_WITH_TWO_CHUNKS, lambda prompt: next(responses))
    self.assertEqual(result["parse_error_count"], 1)
    self.assertEqual(len(result["proposals"]), 1)

def test_reader_rejects_wrong_input_hash_or_model_revision(self):
    with self.assertRaisesRegex(ValueError, "input SHA-256"):
        read_proposal_directory(root, {"input/1.txt": "changed"})
```

Also test strict manifest keys, exact model ID and revision, `do_sample` false, prompt version, per-document names, atomic replacement, skip of valid completed files, regeneration of invalid partial files, and deterministic proposal ordering.

- [ ] **Step 2: Run focused tests and verify RED**

Run:

```powershell
$env:PYTHONPATH='src'; .\.venv\Scripts\python.exe -m unittest tests.test_generate_model_proposals -v
```

Expected: FAIL because the generator and directory reader do not exist.

- [ ] **Step 3: Implement the strict proposal directory reader**

Require this manifest shape:

```json
{
  "format_version": 1,
  "model_id": "Qwen/Qwen3-4B-Instruct-2507",
  "model_revision": "1b4199c4f36b0cef378bfb12390c18780c18af4c",
  "model_parameters": 4000000000,
  "prompt_version": 1,
  "prompt_sha256": "64 lowercase hexadecimal characters",
  "generation": {"do_sample": false, "max_new_tokens": 2048}
}
```

Require each document file to contain exactly `name`, `raw_sha256`, `chunk_count`, `parse_error_count`, and `proposals`.
Validate all 100 expected names and each raw-text checksum before returning proposals.

- [ ] **Step 4: Implement the model-only CLI**

The top-level module must not import PyTorch or Transformers.
Import them only inside `_load_generator` so all core tests remain dependency-free.

Load exactly:

```python
tokenizer = AutoTokenizer.from_pretrained(MODEL_ID, revision=MODEL_REVISION)
model = AutoModelForCausalLM.from_pretrained(
    MODEL_ID,
    revision=MODEL_REVISION,
    torch_dtype=torch.float16,
    device_map="cuda",
)
```

Generate with `do_sample=False` and `max_new_tokens=2048`.
Decode only newly generated tokens.
Write canonical UTF-8 JSON to a sibling temporary file and commit it with `os.replace`.
Skip a completed document only after fully validating its name and input checksum.

Expose:

```text
--input input.zip
--output outputs/model_proposals/qwen3-4b-s008
--model-path optional/local/snapshot
--max-chars 6000
```

When `--model-path` is supplied, use `local_files_only=True` and do not access the network.

- [ ] **Step 5: Run GREEN and commit**

Run the focused tests, all proposal tests, and compilation, then commit:

```powershell
git add tools/generate_model_proposals.py tests/test_generate_model_proposals.py src/medical_race/model_proposals.py
git commit -m "feat: generate resumable qwen proposals"
```

---

### Task 5: Integrate proposal evidence into deterministic submission builds

**Files:**

- Modify: `tools/build_submission.py`
- Create: `tests/test_model_build.py`
- Create: `configs/submissions/08_qwen_grounded.json`
- Create: `docs/qwen_free_gpu_runbook.md`

**Interfaces:**

- Extends: `build_submission(..., model_proposals_path: Path | None = None)`.
- Extends CLI: `--model-proposals PATH`.
- Produces report fields `model_id`, `model_revision`, `model_parameters`, `prompt_sha256`, `model_proposal_count`, `model_added_entity_count`, `model_parse_error_count`, and `model_rejections`.

- [ ] **Step 1: Write failing builder tests**

Require one 100-document fixture proposal directory and prove:

```python
report = build_submission(
    input_zip,
    rxnorm_zip,
    config,
    output_zip,
    rxnorm_md5,
    icd_path=icd,
    expected_icd_sha256=icd_sha256,
    model_proposals_path=proposal_root,
)
self.assertEqual(report["model_id"], "Qwen/Qwen3-4B-Instruct-2507")
self.assertEqual(report["model_parameters"], 4_000_000_000)
self.assertGreater(report["model_added_entity_count"], 0)
```

Also require a missing proposal directory to fail when enabled, an unexpected directory to remain unread when disabled, wrong input checksums to fail, all model-off legacy reports to retain `model_parameters == 0`, and two builds from identical proposals to have identical ZIP hashes.

- [ ] **Step 2: Run the focused test and verify RED**

Run:

```powershell
$env:PYTHONPATH='src'; .\.venv\Scripts\python.exe -m unittest tests.test_model_build -v
```

Expected: FAIL because the builder has no model proposal integration.

- [ ] **Step 3: Add conditional proposal loading and reporting**

Read the proposal directory only when `include_model_proposals` is true.
Pass each document's proposals and one shared `Counter` into `predict_document`.
Count accepted additions independently from stable entity totals.
Copy verified manifest values into the build report.
Keep all existing report fields and legacy values unchanged when the feature is off.

- [ ] **Step 4: Add the experimental configuration**

Create `configs/submissions/08_qwen_grounded.json` by copying Submission 7 and adding:

```json
"include_model_proposals": true
```

Do not change any other configuration value.

- [ ] **Step 5: Write the free-GPU runbook**

Document these Kaggle commands, with Colab path substitutions noted:

```bash
pip install -r requirements-model.txt
export PYTHONPATH=src
python tools/generate_model_proposals.py \
  --input input.zip \
  --output /kaggle/working/qwen3-4b-s008
cd /kaggle/working && zip -qr qwen3-4b-s008.zip qwen3-4b-s008
```

Require GPU acceleration, internet only for the pinned model download, the printed model revision, proposal manifest inspection, output ZIP download, and runtime shutdown after completion.
Document that no leaderboard artifact is produced on Kaggle and no external inference API is used.

- [ ] **Step 6: Run GREEN and commit**

Run model-build tests, all neighboring build and pipeline tests, and the full suite.

Commit:

```powershell
git add tools/build_submission.py tests/test_model_build.py configs/submissions/08_qwen_grounded.json docs/qwen_free_gpu_runbook.md
git commit -m "feat: build grounded qwen submissions"
```

---

### Task 6: Run free-GPU inference and package Submission 8

**Files:**

- Generate ignored: `outputs/kaggle/qwen_grounded_code.zip`
- Receive ignored: `outputs/model_proposals/qwen3-4b-s008/`
- Generate ignored: `outputs/submissions/08_qwen_grounded.zip`
- Generate ignored: `outputs/submissions/08_qwen_grounded.report.json`
- Generate ignored: `outputs/submissions/07_add_diagnoses_to_08_qwen_grounded.diff.json`
- Create: `docs/next_submission_queue_2026-07-14-qwen.md`

**Interfaces:**

- Consumes: Committed code archive, canonical `input.zip`, returned proposal directory, pinned RxNorm, pinned ICD, and Submission 7.
- Produces: One validated Submission 8 artifact and complete evidence report.

- [ ] **Step 1: Run fresh local verification**

Run:

```powershell
$env:PYTHONPATH='src'
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -m compileall -q src tools tests
git diff --check
```

Expected: all tests pass, compilation exits zero, and the diff check is clean.

- [ ] **Step 2: Package committed code for Kaggle**

Run:

```powershell
New-Item -ItemType Directory -Force outputs\kaggle | Out-Null
git archive --format=zip --output=outputs\kaggle\qwen_grounded_code.zip HEAD
```

Record the archive SHA-256.

- [ ] **Step 3: Run Qwen inference on Kaggle or Colab**

Upload the code archive and canonical `input.zip`.
Run the documented generator on a GPU runtime.
Require a manifest with the pinned revision, `4,000,000,000` parameters, prompt version `1`, `do_sample=false`, and 100 valid document files.
Download `qwen3-4b-s008.zip` and shut down the runtime.

- [ ] **Step 4: Validate returned proposals before building**

Extract the returned archive under `outputs/model_proposals/qwen3-4b-s008`.
Use `read_proposal_directory` against canonical input before any submission build.
Reject the entire run for a wrong revision, missing document, checksum mismatch, schema error, or unknown type.

- [ ] **Step 5: Build and semantically diff Submission 8**

Run the existing builder with:

```powershell
$env:PYTHONPATH='src'
.\.venv\Scripts\python.exe tools\build_submission.py `
  --input input.zip `
  --config configs\submissions\08_qwen_grounded.json `
  --model-proposals outputs\model_proposals\qwen3-4b-s008 `
  --output outputs\submissions\08_qwen_grounded.zip
```

Run the existing semantic diff tool against `outputs/submissions/07_add_diagnoses.zip`.

- [ ] **Step 6: Enforce artifact gates**

Require:

- 100 output entries and 100 scored-input proposal records.
- Zero removed Submission 7 entities.
- Zero changes to Submission 7 text, type, position, candidates, or assertions.
- Every addition has an exact raw offset and valid type-specific schema.
- Every diagnosis and drug addition has exactly one pinned candidate.
- No unknown candidate, output field, assertion, or type.
- Model budget exactly `4,000,000,000 / 9,000,000,000`.
- A rejection report broken down by deterministic gate.
- Two independent local builds from the same proposal directory have identical artifact SHA-256 values.

- [ ] **Step 7: Audit additions and record the upload queue**

Print every added entity with document, raw text, type, candidate, assertion, position, section, and acceptance source.
Group additions and rejections by type and section.
Fix only general structural errors through failing regression tests.
Do not add document identifiers or unique public-test phrases to code or prompts.

Record commit, config, input and ontology checksums, proposal manifest and checksum, model revision, prompt version, model budget, artifact checksum, parent `local-s007`, full semantic diff, hypothesis, and exact upload path.

- [ ] **Step 8: Hand the validated ZIP to the user**

The user uploads only `outputs/submissions/08_qwen_grounded.zip`.
After the portal result returns, append it to `docs/submissions.csv`, decompose all score components against Submission 7, and promote only if the gain is clean and plausibly private-test generalizable.

---

## Plan self-review checklist

- Every design requirement maps to an implementation task.
- The only active model is the pinned 4.0B Qwen checkpoint.
- Model dependencies are isolated from the standard-library core and local tests.
- Submission 7 remains the unchanged fallback and comparison parent.
- Raw grounding, section gates, link gates, assertion derivation, overlap precedence, schema validation, and reporting have explicit tests.
- Free-GPU interruption and transfer are handled by validated per-document files.
- No placeholder, external inference API, public-test hard-coding, or second model is included.
