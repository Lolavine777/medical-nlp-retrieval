# Submission 10 Targeted Qwen Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a backward-compatible prompt version 2 for symptom and laboratory proposals, retain failed-response diagnostics, and provide a minimal manual Kaggle smoke and dual-GPU runbook.

**Architecture:** Keep the existing Qwen model, strict parser, proposal schema, grounding gates, and Submission 8 pipeline.
Register prompt versions 1 and 2 in the existing proposal module, add optional diagnostic sidecars to the existing generator, and parameterize the existing dual-GPU runner instead of creating another notebook or runner.

**Tech Stack:** Python 3.11+, standard library, PyTorch, Transformers, Kaggle 2x T4, JSON, and `unittest`.

## Global Constraints

The only active model is `Qwen/Qwen3-4B-Instruct-2507` at revision `1b4199c4f36b0cef378bfb12390c18780c18af4c`.
The active parameter count remains `4,000,000,000 / 9,000,000,000`.
Prompt version 1 artifacts remain readable without migration.
Prompt version 2 permits only `TRIỆU_CHỨNG`, `TÊN_XÉT_NGHIỆM`, and `KẾT_QUẢ_XÉT_NGHIỆM`.
The parser remains strict JSON and model proposals remain add-only.
Raw diagnostics remain ignored, are excluded from the final submission archive, and never become prediction input.
The user runs all Kaggle cells manually after local implementation and verification finish.
No full inference run starts until the deterministic ten-document smoke gate passes.

---

### Task 1: Register prompt version 2 without breaking version 1 artifacts

**Files:**

- Modify: `src/medical_race/model_proposals.py`
- Modify: `tests/test_model_proposals.py`
- Modify: `tests/test_generate_model_proposals.py`

**Interfaces:**

- Produces: `PROMPT_HEADERS: dict[int, str]`.
- Produces: `PROMPT_ALLOWED_TYPES: dict[int, frozenset[str]]`.
- Produces: `prompt_sha256(prompt_version: int = PROMPT_VERSION) -> str`.
- Extends: `parse_model_response(value: str, allowed_types: frozenset[str] = ALLOWED_TYPES)`.
- Extends: `prompt_chunks(raw_text: str, max_chars: int = 6000, prompt_version: int = PROMPT_VERSION)`.
- Preserves: version 1 manifest and proposal-directory validation.

- [ ] **Step 1: Add failing prompt-profile tests**

Add tests that require version 1 and version 2 to have different hashes, require version 2 prompts to name only the three targeted types, and reject a version 2 drug proposal while accepting the same proposal under version 1.

```python
from medical_race.model_proposals import (
    PROMPT_ALLOWED_TYPES,
    PROMPT_HEADERS,
    prompt_sha256,
)

def test_prompt_profiles_preserve_v1_and_target_v2(self):
    self.assertEqual(set(PROMPT_HEADERS), {1, 2})
    self.assertNotEqual(prompt_sha256(1), prompt_sha256(2))
    self.assertEqual(
        PROMPT_ALLOWED_TYPES[2],
        frozenset({"TRIỆU_CHỨNG", "TÊN_XÉT_NGHIỆM", "KẾT_QUẢ_XÉT_NGHIỆM"}),
    )
    prompt = prompt_chunks("Triệu chứng hiện tại\nHo\n", prompt_version=2)[0].prompt
    self.assertNotIn("CHẨN_ĐOÁN", prompt)
    self.assertNotIn("THUỐC", prompt)

def test_version_two_manifest_rejects_non_targeted_type(self):
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        value = manifest(prompt_version=2)
        write_json(root / "manifest.json", value)
        write_json(
            root / "documents" / "1.json",
            {
                "name": "input/1.txt",
                "raw_sha256": hashlib.sha256(RAW.encode("utf-8")).hexdigest(),
                "chunk_count": 1,
                "parse_error_count": 0,
                "proposals": [{"line_index": 3, "text": "Viêm phổi", "type": "CHẨN_ĐOÁN"}],
            },
        )
        with self.assertRaisesRegex(ValueError, "unknown type"):
            read_proposal_directory(root, {"input/1.txt": RAW})
```

Update the test helper to use `PROMPT_HEADERS[prompt_version]` and accept `prompt_version: int = 1`.

```python
def manifest(prompt_version: int = 1):
    return {
        "format_version": 1,
        "model_id": MODEL_ID,
        "model_revision": MODEL_REVISION,
        "model_parameters": MODEL_PARAMETERS,
        "prompt_version": prompt_version,
        "prompt_sha256": hashlib.sha256(
            PROMPT_HEADERS[prompt_version].encode("utf-8")
        ).hexdigest(),
        "generation": {"do_sample": False, "max_new_tokens": 2048},
    }
```

- [ ] **Step 2: Run the focused tests and confirm failure**

Run:

```powershell
$env:PYTHONPATH = "src;."
.\.venv\Scripts\python.exe -m unittest tests.test_model_proposals tests.test_generate_model_proposals -v
```

Expected: failure because prompt profiles and version-aware validation do not exist.

- [ ] **Step 3: Implement the two prompt profiles and strict version-aware validation**

Keep the existing header as `PROMPT_HEADERS[1]` and add this concise version 2 header:

```python
PROMPT_VERSION = 2
TARGETED_TYPES = frozenset(
    {"TRIỆU_CHỨNG", "TÊN_XÉT_NGHIỆM", "KẾT_QUẢ_XÉT_NGHIỆM"}
)
PROMPT_V1_HEADER = """Extract clinical mentions from the supplied raw lines.
Return only a JSON array.
Each object must contain exactly line_index, text, and type.
Copy text verbatim from one supplied line.
Use only these types: CHẨN_ĐOÁN, KẾT_QUẢ_XÉT_NGHIỆM, THUỐC, TRIỆU_CHỨNG, TÊN_XÉT_NGHIỆM.
Include every genuine mention occurrence and no headings or metadata.
Lines are formatted as line_index, section, role, and raw text separated by tabs.
"""
PROMPT_HEADERS = {
    1: PROMPT_V1_HEADER,
    2: """Extract atomic symptom and laboratory mentions from the supplied raw lines.
Return only one strict JSON array with no Markdown or explanation.
Each object must contain exactly line_index, text, and type.
Copy text verbatim from one supplied line.
Use only these types: KẾT_QUẢ_XÉT_NGHIỆM, TRIỆU_CHỨNG, TÊN_XÉT_NGHIỆM.
Never return a heading, metadata, procedure, date, standalone unit, treatment action, normal-state description, whole bullet, or whole sentence.
For laboratory content, return the test name and its numeric or qualitative result as separate objects.
For symptom content, exclude bullets and assertion cues from the copied symptom text.
Example input:
10\tlaboratory\tlab\tNatri: 138 mmol/L; CRP âm tính
11\tsymptoms\tbullet\t- Không khó nuốt nhưng đau vai khi vận động
Example output:
[{"line_index":10,"text":"Natri","type":"TÊN_XÉT_NGHIỆM"},{"line_index":10,"text":"138 mmol/L","type":"KẾT_QUẢ_XÉT_NGHIỆM"},{"line_index":10,"text":"CRP","type":"TÊN_XÉT_NGHIỆM"},{"line_index":10,"text":"âm tính","type":"KẾT_QUẢ_XÉT_NGHIỆM"},{"line_index":11,"text":"khó nuốt","type":"TRIỆU_CHỨNG"},{"line_index":11,"text":"đau vai khi vận động","type":"TRIỆU_CHỨNG"}]
Lines are formatted as line_index, section, role, and raw text separated by tabs.
""",
}
PROMPT_ALLOWED_TYPES = {1: ALLOWED_TYPES, 2: TARGETED_TYPES}
PROMPT_HEADER = PROMPT_HEADERS[PROMPT_VERSION]
```

Validate prompt versions through `PROMPT_HEADERS`, calculate the hash for the manifest version, and pass the corresponding allowed type set into `parse_model_response` when reading records.

- [ ] **Step 4: Run focused tests and commit**

Run:

```powershell
$env:PYTHONPATH = "src;."
.\.venv\Scripts\python.exe -m unittest tests.test_model_proposals tests.test_generate_model_proposals -v
git add src\medical_race\model_proposals.py tests\test_model_proposals.py tests\test_generate_model_proposals.py
git commit -m "feat: add targeted Qwen prompt profile"
```

Expected: focused tests pass and historical version 1 manifest tests remain green.

### Task 2: Retain failed responses outside proposal records

**Files:**

- Modify: `tools/generate_model_proposals.py`
- Modify: `tests/test_generate_model_proposals.py`

**Interfaces:**

- Extends: `generate_document(..., prompt_version: int = PROMPT_VERSION, failures: list[dict[str, object]] | None = None, document_name: str = "")`.
- Extends: `generate_proposal_directory(..., prompt_version: int = PROMPT_VERSION, diagnostics_output: Path | None = None) -> dict[str, object]`.
- Adds CLI: `--prompt-version` with choices from `PROMPT_HEADERS` and default `2`.
- Adds CLI: `--diagnostics-output` as an optional directory.
- Produces: a deterministic printed summary with documents, chunks, parse errors, proposals, and type counts.

- [ ] **Step 1: Add failing diagnostics and summary tests**

Require an invalid JSON response to remain absent from proposal records while its raw response is written into a separate diagnostics file.

```python
def test_writes_failed_raw_response_only_to_diagnostics(self):
    documents = {"input/1.txt": RAW}
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        summary = generate_proposal_directory(
            documents,
            root / "proposals",
            lambda prompt: "```json\n[]\n```",
            prompt_version=2,
            diagnostics_output=root / "diagnostics",
        )
        record = json.loads((root / "proposals/documents/1.json").read_text(encoding="utf-8"))
        diagnostic = json.loads((root / "diagnostics/1.json").read_text(encoding="utf-8"))
        self.assertEqual(record["proposals"], [])
        self.assertEqual(record["parse_error_count"], 1)
        self.assertEqual(diagnostic["failures"][0]["raw_response"], "```json\n[]\n```")
        self.assertEqual(diagnostic["failures"][0]["category"], "parse")
        self.assertEqual(summary["parse_errors"], 1)
        self.assertEqual(summary["type_counts"], {})
```

Also require an outside-chunk or non-verbatim response to use category `grounding`.
Delete a diagnostic file after a completed run and require resume to regenerate that document when its proposal record reports a parse error.

```python
def test_records_grounding_failures_and_regenerates_missing_diagnostics(self):
    documents = {"input/1.txt": RAW}
    calls = []

    def generate(prompt):
        calls.append(prompt)
        return '[{"line_index":99,"text":"missing","type":"TRIỆU_CHỨNG"}]'

    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        proposal_root = root / "proposals"
        diagnostics_root = root / "diagnostics"
        generate_proposal_directory(
            documents,
            proposal_root,
            generate,
            prompt_version=2,
            diagnostics_output=diagnostics_root,
        )
        diagnostic_path = diagnostics_root / "1.json"
        diagnostic = json.loads(diagnostic_path.read_text(encoding="utf-8"))
        self.assertEqual(diagnostic["failures"][0]["category"], "grounding")
        first_calls = len(calls)
        diagnostic_path.unlink()
        generate_proposal_directory(
            documents,
            proposal_root,
            generate,
            prompt_version=2,
            diagnostics_output=diagnostics_root,
        )
        self.assertGreater(len(calls), first_calls)
        self.assertTrue(diagnostic_path.is_file())
```

- [ ] **Step 2: Run the diagnostics test and confirm failure**

Run:

```powershell
$env:PYTHONPATH = "src;."
.\.venv\Scripts\python.exe -m unittest tests.test_generate_model_proposals -v
```

Expected: failure because diagnostics arguments and the summary return value do not exist.

- [ ] **Step 3: Implement minimal diagnostic sidecars and summary output**

Generate the raw response before parsing.
Use one try block for strict response parsing and another for chunk membership plus exact grounding so failures receive category `parse` or `grounding`.
Append records with exactly `document`, `chunk_index`, `prompt_version`, `category`, and `raw_response`.
Write one atomic diagnostics JSON file per document only when failures exist.
When diagnostics are enabled, write the diagnostic record before the proposal record and treat a proposal record with parse errors as incomplete if its diagnostic record is missing or invalid.

Pass `prompt_version` into `_manifest`, `prompt_chunks`, `_is_complete`, and `parse_model_response`.
Return and print this summary shape:

```python
{
    "documents": len(proposals_by_document),
    "chunks": sum(record["chunk_count"] for record in records),
    "parse_errors": sum(record["parse_error_count"] for record in records),
    "proposals": sum(len(values) for values in proposals_by_document.values()),
    "type_counts": dict(sorted(type_counts.items())),
}
```

- [ ] **Step 4: Run focused tests and commit**

Run:

```powershell
$env:PYTHONPATH = "src;."
.\.venv\Scripts\python.exe -m unittest tests.test_generate_model_proposals tests.test_model_proposals -v
git add tools\generate_model_proposals.py tests\test_generate_model_proposals.py
git commit -m "feat: retain Qwen failure diagnostics"
```

Expected: focused tests pass, strict Markdown-fence rejection remains tested, and proposal document schemas remain unchanged.

### Task 3: Parameterize the existing dual-GPU runner for Submission 10

**Files:**

- Modify: `tools/run_kaggle_s009.py`
- Modify: `tests/test_run_kaggle_s009.py`

**Interfaces:**

- Adds CLI: `--run-name` with default `qwen3-4b-s009`.
- Adds CLI: `--prompt-version` with default `1` for historical S9 compatibility.
- Passes: `--prompt-version` and per-shard `--diagnostics-output` to the generator.
- Produces: `<run-name>.zip` and `<run-name>-diagnostics.zip` under the selected work root.
- Preserves: existing input discovery, two-GPU sharding, resumability, logs, validation, and SHA-256 reporting.

- [ ] **Step 1: Add failing runner tests**

Update valid shard generation to pass prompt version 1 explicitly.
Add a test proving merge validation uses the prompt version stored in the manifest rather than the current default.
Add a test for safe run names:

```python
from tools.run_kaggle_s009 import validate_run_name

def test_accepts_safe_run_name_and_rejects_paths(self):
    self.assertEqual(validate_run_name("qwen3-4b-s010"), "qwen3-4b-s010")
    for value in ("../escape", "nested/name", "", "."):
        with self.subTest(value=value), self.assertRaisesRegex(ValueError, "run name"):
            validate_run_name(value)

def test_merge_uses_manifest_prompt_version(self):
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        source = write_documents(root)
        documents = {
            f"input/{index}.txt": (source / f"{index}.txt").read_text(encoding="utf-8")
            for index in range(1, 101)
        }
        shards = []
        for shard_index in range(2):
            shard = root / f"v1-shard-{shard_index}"
            generate_proposal_directory(
                select_document_shard(documents, shard_index, 2),
                shard,
                lambda prompt: "[]",
                2500,
                prompt_version=1,
            )
            shards.append(shard)
        summary = merge_shards(shards, root / "final", documents, 2500)
        self.assertEqual(summary["documents"], 100)
```
```

- [ ] **Step 2: Run runner tests and confirm failure**

Run:

```powershell
$env:PYTHONPATH = "src;."
.\.venv\Scripts\python.exe -m unittest tests.test_run_kaggle_s009 -v
```

Expected: failure because configurable run names and prompt versions do not exist.

- [ ] **Step 3: Implement safe parameterized paths and diagnostics packaging**

Validate run names with this exact policy:

```python
RUN_NAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*")

def validate_run_name(value: str) -> str:
    if not isinstance(value, str) or RUN_NAME.fullmatch(value) is None:
        raise ValueError("run name must contain only letters, numbers, dot, underscore, and hyphen")
    return value
```

Build shard, log, merged-output, and archive paths from the validated run name.
Pass the selected prompt version to each generator worker.
Read the merged manifest prompt version when recomputing chunk counts.
Copy per-document diagnostic JSON files from both disjoint shards into `<run-name>-diagnostics` and package that directory separately.
Include `prompt_version`, `diagnostics_archive`, and its SHA-256 in the printed result.

- [ ] **Step 4: Run focused tests and commit**

Run:

```powershell
$env:PYTHONPATH = "src;."
.\.venv\Scripts\python.exe -m unittest tests.test_run_kaggle_s009 tests.test_generate_model_proposals -v
git add tools\run_kaggle_s009.py tests\test_run_kaggle_s009.py
git commit -m "feat: parameterize dual-GPU Qwen runner"
```

Expected: runner tests pass and the historical default still produces `qwen3-4b-s009.zip` with prompt version 1.

### Task 4: Add the Submission 10 config and manual Kaggle runbook

**Files:**

- Create: `configs/submissions/10_qwen_targeted.json`
- Create: `docs/qwen_s010_runbook.md`
- Create: `docs/next_submission_queue_2026-07-17-qwen-targeted.md`

**Interfaces:**

- Produces: one unchanged stable-pipeline configuration identified for S10.
- Produces: exact manual Kaggle smoke and full-run cells.
- Produces: exact local build, diff, preflight, and promotion commands for use after the user returns the proposal archive.

- [ ] **Step 1: Add the S10 submission configuration**

Create this exact JSON:

```json
{
  "include_labs": true,
  "span_policy": "regimen",
  "concept_level": "all_retrievable",
  "candidate_output": "top1",
  "include_symptoms": true,
  "include_diagnoses": true,
  "include_model_proposals": true
}
```

- [ ] **Step 2: Write the minimal manual Kaggle runbook**

The runbook must have four cells only:

1. clone or update the GitHub repository and print `git rev-parse HEAD`;
2. install `requirements-model.txt` and prepare `/kaggle/working/input.zip` through `prepare_input_zip`;
3. run the deterministic ten-document smoke shard on GPU 0 with prompt version 2 and diagnostics enabled;
4. after team-lead approval of the printed smoke summary, run the existing dual-GPU runner with `--run-name qwen3-4b-s010 --prompt-version 2`.

Cell 1 is:

```python
from pathlib import Path
import subprocess

repo = Path("/kaggle/working/medical-nlp-retrieval")
url = "https://github.com/Lolavine777/medical-nlp-retrieval.git"
if not repo.exists():
    subprocess.run(["git", "clone", url, str(repo)], check=True)
subprocess.run(["git", "-C", str(repo), "switch", "master"], check=True)
subprocess.run(["git", "-C", str(repo), "pull", "--ff-only", "origin", "master"], check=True)
subprocess.run(["git", "-C", str(repo), "rev-parse", "HEAD"], check=True)
```

Cell 2 is:

```python
import os
import subprocess
import sys
from pathlib import Path

repo = Path("/kaggle/working/medical-nlp-retrieval")
subprocess.run(
    [sys.executable, "-m", "pip", "install", "-r", str(repo / "requirements-model.txt")],
    check=True,
)
os.chdir(repo)
sys.path[:0] = [str(repo), str(repo / "src")]
from tools.run_kaggle_s009 import prepare_input_zip

input_zip = prepare_input_zip(Path("/kaggle/input"), Path("/kaggle/working/input.zip"))
print("Code:", repo)
print("Input ZIP:", input_zip)
```

The smoke command is:

```bash
CUDA_VISIBLE_DEVICES=0 PYTHONPATH=.:src python tools/generate_model_proposals.py \
  --input /kaggle/working/input.zip \
  --output /kaggle/working/qwen3-4b-s010-smoke \
  --diagnostics-output /kaggle/working/qwen3-4b-s010-smoke-diagnostics \
  --prompt-version 2 \
  --max-chars 2500 \
  --shard-index 0 \
  --shard-count 10
```

The full command is:

```bash
PYTHONPATH=.:src python tools/run_kaggle_s009.py \
  --input-root /kaggle/input \
  --work-root /kaggle/working \
  --run-name qwen3-4b-s010 \
  --prompt-version 2
```

The runbook must explicitly tell the user to stop after the smoke summary and send it to the team lead.
It must explicitly say never upload either proposal ZIP to the competition portal.

- [ ] **Step 3: Document the S10 gate and local return path**

Create the S10 queue document with parent `local-s008`, expected unchanged candidates, and the local gates from the design spec.
Use these exact facts in the queue document:

```markdown
# Next Submission Queue, Targeted Qwen

## Hypothesis

Prompt version 2 recovers atomic symptom and laboratory mentions missed by Submission 8 while preserving every stable entity and all 150 candidates.

## Parent and controlled variable

The semantic parent is `local-s008` at score `16.13250`.
The only primary behavior change is the task-focused prompt profile.
The model, revision, strict parser, 2,500-character chunking, grounding, linkers, rules, assertions, and candidate policy remain fixed.

## Local gate

The run must cover 100 documents, keep parse errors below 20 percent of chunks, add at least 25 entities across at least 10 documents, preserve all 150 candidates, and produce zero removals or changes to stable fields.
Every accepted addition receives manual structural review before a portal ZIP is created.

## Portal decision

Promote only above `16.13250` with component movement consistent with improved mention coverage and unchanged candidate Jaccard.
```
Document these local commands for after the returned proposal archive is extracted:

```powershell
$env:PYTHONPATH = "src;."
$env:PYTHONIOENCODING = "utf-8"
.\.venv\Scripts\python.exe tools\build_submission.py --input input.zip --config configs\submissions\10_qwen_targeted.json --model-proposals outputs\model_proposals\qwen3-4b-s010 --output outputs\submissions\10_qwen_targeted.zip --report outputs\submissions\10_qwen_targeted.report.json
.\.venv\Scripts\python.exe tools\diff_submissions.py outputs\submissions\08_qwen_grounded.zip outputs\submissions\10_qwen_targeted.zip --output outputs\submissions\08_qwen_grounded_to_10_qwen_targeted.diff.json
.\.venv\Scripts\python.exe tools\validate_submission.py --input input.zip outputs\submissions\10_qwen_targeted.zip
```

- [ ] **Step 4: Run final verification**

Run:

```powershell
$env:PYTHONPATH = "src;."
$env:PYTHONIOENCODING = "utf-8"
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -m compileall -q src tools tests
.\.venv\Scripts\python.exe -m json.tool configs\submissions\10_qwen_targeted.json > $null
git diff --check
```

Expected: all tests pass, compilation and JSON validation exit zero, and there are no whitespace errors.

- [ ] **Step 5: Commit and publish the Kaggle-ready code**

Run:

```powershell
git add configs\submissions\10_qwen_targeted.json docs\qwen_s010_runbook.md docs\next_submission_queue_2026-07-17-qwen-targeted.md docs\superpowers\plans\2026-07-17-submission-10-targeted-qwen.md
git commit -m "docs: add Submission 10 Kaggle runbook"
git push origin master
```

Expected: the verified implementation is available from GitHub for the user's manual Kaggle cells, while raw inputs, diagnostics, proposals, model weights, and generated archives remain untracked.
