# Submission 10 Item-Level Salvage Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Preserve independently valid Qwen proposals from otherwise imperfect chunks and replay the completed Submission 10 diagnostics without another GPU run.

**Architecture:** Add one strict item-level validator beside the existing model proposal parser.
Use it in live generation so one bad item no longer discards valid siblings.
Add a small offline replay command that reads the existing proposal and diagnostics ZIPs and writes the normal proposal directory consumed by `build_submission.py`.

**Tech Stack:** Python 3.12 standard library, existing `unittest` suite, existing proposal and submission validators.

## Global Constraints

- Preserve raw UTF-8 text, whitespace, line endings, and duplicate mentions.
- Accept only exact verbatim spans where `raw_text[start:end] == text`.
- Do not normalize, fuzzy-match, invent, or repair proposal text or types.
- Keep prompt-version allowed types and model manifest unchanged.
- Keep the combined model parameter budget at or below 9B.
- Do not upload the original or replayed proposal archive directly to the portal.
- Do not modify the untracked organizer HTML, handoff, input ZIP, or notebook files in the main checkout.

---

### Task 1: Add the strict item-level validator

**Files:**
- Modify: `src/medical_race/model_proposals.py`
- Test: `tests/test_model_proposals.py`

**Interface:**
- Add `salvage_model_response(raw_text: str, response: str, line_indices: frozenset[int], allowed_types: frozenset[str]) -> tuple[tuple[ModelProposal, ...], str | None]`.
- Return accepted proposals and one diagnostic category, where the category is `None`, `parse`, or `grounding`.

- [ ] **Step 1: Write the failing tests**

Add tests that pass one response containing one valid proposal and one non-verbatim proposal, and assert that the valid proposal survives with category `grounding`.
Add a test containing one valid targeted type and one unknown type, and assert that the valid proposal survives with category `parse`.
Add a test for a non-array response and assert that it returns no proposals with category `parse`.
Add a test for an empty JSON array and assert that it returns no proposals with category `None`.

- [ ] **Step 2: Run the focused tests and verify the expected failure**

Run:

```powershell
$env:PYTHONPATH = "src;."
.\.venv\Scripts\python.exe -m unittest discover -s tests -p test_model_proposals.py
```

Expected result: the new tests fail because `salvage_model_response` does not exist.

- [ ] **Step 3: Implement the minimum validator**

Parse the outer response with `json.loads` and require a list.
Validate each object independently by serializing a one-item list and calling the existing `parse_model_response` with the supplied allowed types.
For a valid object, reject it as `grounding` when its line index is absent from `line_indices` or `ground_proposals(raw_text, (proposal,))` raises `ValueError`.
Keep accepted proposals even when sibling items are rejected.
Use `parse` precedence when any object fails schema or type validation.

- [ ] **Step 4: Run the focused tests and verify they pass**

Run the same focused command.
Expected result: all existing and new model proposal tests pass.

- [ ] **Step 5: Commit the helper and tests**

```powershell
git add src/medical_race/model_proposals.py tests/test_model_proposals.py
git commit -m "feat: salvage valid model proposal items"
```

### Task 2: Use item-level salvage during live generation

**Files:**
- Modify: `tools/generate_model_proposals.py`
- Test: `tests/test_generate_model_proposals.py`

**Interface:**
- Keep `generate_document` and the proposal record schema unchanged.
- Keep `parse_error_count` as the number of chunks with one or more rejected items.
- Keep one diagnostic record per imperfect chunk with the existing `parse` or `grounding` category.

- [ ] **Step 1: Write the failing regression test**

Add a `generate_document` test whose response contains one valid targeted proposal and one invalid grounding proposal in the same chunk.
Assert that the valid proposal is returned and `parse_error_count` is one.
Add a test whose response contains one valid targeted proposal and one unknown type.
Assert that the valid proposal is returned and `parse_error_count` is one.

- [ ] **Step 2: Run the focused generator tests and verify the expected failure**

Run:

```powershell
$env:PYTHONPATH = "src;."
.\.venv\Scripts\python.exe -m unittest discover -s tests -p test_generate_model_proposals.py
```

Expected result: the new tests fail because `generate_document` still discards the whole chunk.

- [ ] **Step 3: Implement the smallest integration change**

Replace the chunk-wide `parse_model_response` and `ground_proposals` rejection block with one call to `salvage_model_response`.
Extend the document proposals with the returned accepted items.
Increment `parse_error_count` and write one diagnostic when the returned category is not `None`.
Leave manifest validation, resume behavior, sorting, and record fields unchanged.

- [ ] **Step 4: Run focused tests and the complete suite**

Run the focused generator command, then:

```powershell
$env:PYTHONPATH = "src;."
.\.venv\Scripts\python.exe -m unittest discover -s tests
.\.venv\Scripts\python.exe -m compileall -q src tools tests
```

Expected result: all tests pass and compilation exits zero.

- [ ] **Step 5: Commit the live generator change**

```powershell
git add tools/generate_model_proposals.py tests/test_generate_model_proposals.py
git commit -m "fix: keep valid siblings in imperfect Qwen chunks"
```

### Task 3: Replay the completed Submission 10 diagnostics offline

**Files:**
- Create: `tools/replay_model_diagnostics.py`
- Test: `tests/test_replay_model_diagnostics.py`
- Modify: `docs/qwen_s010_runbook.md`

**Interface:**
- Add `replay_proposals(input_zip: Path, proposal_zip: Path, diagnostics_zip: Path, output: Path) -> dict[str, object]`.
- Add CLI arguments `--input`, `--proposals`, `--diagnostics`, and `--output`.
- Write the original manifest, one record per canonical document, and no diagnostics files to the output directory.
- Report original proposals, recovered proposals, rejected items, final proposals, and type counts.

- [ ] **Step 1: Write the failing replay test**

Create a temporary canonical input ZIP, a valid proposal ZIP containing one accepted item, and a diagnostics ZIP containing one failed response with one valid sibling and one invalid sibling.
Call `replay_proposals` and assert that the output directory passes `read_proposal_directory` and contains both the original item and the recovered valid sibling.
Assert that the invalid sibling is absent and the original chunk error count is preserved.

- [ ] **Step 2: Run the replay test and verify the expected failure**

Run:

```powershell
$env:PYTHONPATH = "src;."
.\.venv\Scripts\python.exe -m unittest tests.test_replay_model_diagnostics
```

Expected result: the test fails because the replay module does not exist.

- [ ] **Step 3: Implement the replay command**

Read and validate the canonical documents with `read_zip_documents` and `validate_document_names`.
Read the proposal manifest and document records directly from the proposal ZIP.
Read diagnostic failures directly from the diagnostics ZIP.
For each failed response, call `salvage_model_response` with the corresponding document and prompt chunk line indices.
Merge accepted recovered proposals with the original record proposals using `ModelProposal` values and deterministic sorting.
Write JSON with the existing record schema and preserve `raw_sha256`, `chunk_count`, and original `parse_error_count`.
Validate the written directory with `read_proposal_directory` before returning the report.

- [ ] **Step 4: Run replay tests and local artifact checks**

Run the replay test, the complete test suite, and compilation.
Replay the real artifacts:

```powershell
$env:PYTHONPATH = "src;."
.\.venv\Scripts\python.exe tools\replay_model_diagnostics.py `
  --input input.zip `
  --proposals outputs\kaggle\qwen3-4b-s010.zip `
  --diagnostics outputs\kaggle\qwen3-4b-s010-diagnostics.zip `
  --output outputs\model_proposals\qwen3-4b-s010-salvaged
```

Expected result: output validation passes and the report shows the recovered count from item-level replay.

- [ ] **Step 5: Add the offline replay command to the runbook**

Document that the original proposal and diagnostics archives are evidence only.
Document the replay command and require its output to pass the existing build, diff, and submission validators before any portal upload.

- [ ] **Step 6: Commit the replay command, tests, and runbook**

```powershell
git add tools/replay_model_diagnostics.py tests/test_replay_model_diagnostics.py docs/qwen_s010_runbook.md
git commit -m "feat: replay valid proposals from Qwen diagnostics"
```

### Task 4: Evaluate the salvaged proposals before promotion

**Files:**
- Create: `outputs/submissions/10_qwen_targeted_salvaged.report.json`
- Create: `outputs/submissions/08_qwen_grounded_to_10_qwen_targeted_salvaged.diff.json`
- Create: `outputs/submissions/10_qwen_targeted_salvaged.zip`

- [ ] **Step 1: Build the normal competition archive**

```powershell
$env:PYTHONPATH = "src;."
$env:PYTHONIOENCODING = "utf-8"
.\.venv\Scripts\python.exe tools\build_submission.py `
  --input input.zip `
  --config configs\submissions\10_qwen_targeted.json `
  --model-proposals outputs\model_proposals\qwen3-4b-s010-salvaged `
  --output outputs\submissions\10_qwen_targeted_salvaged.zip `
  --report outputs\submissions\10_qwen_targeted_salvaged.report.json
```

- [ ] **Step 2: Diff against Submission 8 and validate**

```powershell
.\.venv\Scripts\python.exe tools\diff_submissions.py `
  outputs\submissions\08_qwen_grounded.zip `
  outputs\submissions\10_qwen_targeted_salvaged.zip `
  --output outputs\submissions\08_qwen_grounded_to_10_qwen_targeted_salvaged.diff.json
.\.venv\Scripts\python.exe tools\validate_submission.py `
  --input input.zip outputs\submissions\10_qwen_targeted_salvaged.zip
```

- [ ] **Step 3: Apply the promotion gate**

Promote only if the archive validates, stable entities have zero removals or changes, candidate count remains 150, and every accepted addition is structurally reviewed.
Otherwise retain the salvaged archive as a diagnostic artifact and do not submit it.

