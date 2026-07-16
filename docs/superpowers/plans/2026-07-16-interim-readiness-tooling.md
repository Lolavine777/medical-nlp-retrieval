# Interim Readiness Tooling Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add final-ZIP preflight validation, observational linking diagnostics, reproducible rule and Qwen controls, and an inactive post-update bring-up checklist.

**Architecture:** Reuse the existing submission validator, ontology readers, extractors, linkers, builder, and semantic diff.
Expose small pure functions for archive validation and candidate ranking, then keep command-line wrappers thin.
Do not change prediction behavior or run model inference.

**Tech Stack:** Python 3.11 standard library, existing `medical_race` package, `unittest`, deterministic JSON and ZIP files.

## Global Constraints

- Preserve raw UTF-8 text, whitespace, line endings, duplicate mentions, and end-exclusive offsets.
- Keep the active model budget at `0` for the rule control and `4,000,000,000` for the Qwen control, both below `9,000,000,000`.
- Add no dependency, model, ontology data, portal automation, policy assumption, or ranking behavior change.
- Use existing files with exclusive creation and never overwrite raw inputs, proposal records, reports, or archives.
- Run every Python command through `.venv\Scripts\python.exe`.
- Keep the post-update checklist inactive until the user explicitly confirms that the update is live.

---

### Task 1: Final submission preflight

**Files:**
- Modify: `src/medical_race/submission/__init__.py`
- Create: `tools/validate_submission.py`
- Create: `tests/test_validate_submission.py`
- Modify: `tests/test_submission.py`

**Interfaces:**
- Consumes: `Mapping[str, str]` containing canonical `input/1.txt` through `input/100.txt`.
- Produces: `validate_output_zip(path: Path, documents: Mapping[str, str], schemas: Mapping[str, Sequence[str]] = DEFAULT_SCHEMAS) -> dict[str, object]`.
- Produces: A CLI with `--input PATH` and one positional submission ZIP path.

- [ ] **Step 1: Write the failing end-to-end regression for the Submission 9 transfer mistake**

Create a proposal-shaped archive with `qwen3-4b-s009/manifest.json` and `qwen3-4b-s009/documents/1.json`.
Invoke the command with the virtual-environment interpreter and assert a nonzero result containing `intermediate model-proposal archive`.

```python
environment = os.environ.copy()
environment["PYTHONPATH"] = os.pathsep.join(("src", "."))
result = subprocess.run(
    [
        sys.executable,
        "tools/validate_submission.py",
        "--input",
        str(input_zip),
        str(proposal_zip),
    ],
    cwd=Path(__file__).resolve().parents[1],
    env=environment,
    text=True,
    capture_output=True,
)
self.assertNotEqual(result.returncode, 0)
self.assertIn("intermediate model-proposal archive", result.stderr)
```

- [ ] **Step 2: Run the regression and observe RED**

Run:

```powershell
.\.venv\Scripts\python.exe -m unittest tests.test_validate_submission -v
```

Expected: FAIL because `tools/validate_submission.py` does not exist.

- [ ] **Step 3: Add focused archive-validation tests**

Use `build_output_zip()` to make a valid fixture and assert that `validate_output_zip()` returns exactly these stable report fields:

```python
{
    "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
    "entry_count": 100,
    "entity_count": 0,
    "candidate_count": 0,
    "assertion_count": 0,
    "entity_counts": {},
}
```

Add subtests for a single wrapper directory, malformed JSON, a missing record, an extra record, an invalid schema, and an invalid offset.
Assert that each raises `ValueError` with a direct reason.

- [ ] **Step 4: Implement the shared validator**

Replace the private read-back loop with a public function that validates a file without extracting it.
Keep `build_output_zip()` using the same validation path.

```python
def validate_output_zip(
    path: Path,
    documents: Mapping[str, str],
    schemas: Mapping[str, Sequence[str]] = DEFAULT_SCHEMAS,
) -> dict[str, object]:
    _validate_keys("document", documents)
    data = Path(path).read_bytes()
    with zipfile.ZipFile(BytesIO(data)) as archive:
        names = tuple(archive.namelist())
        if names != OUTPUT_NAMES:
            _raise_archive_shape_error(names)
        entities = []
        for input_name, output_name in zip(INPUT_NAMES, OUTPUT_NAMES, strict=True):
            try:
                values = json.loads(archive.read(output_name).decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError) as error:
                raise ValueError(f"invalid UTF-8 JSON in {output_name}") from error
            validate_entities(documents[input_name], values, schemas)
            entities.extend(values)
    counts = Counter(entity["type"] for entity in entities)
    return {
        "sha256": hashlib.sha256(data).hexdigest(),
        "entry_count": len(OUTPUT_NAMES),
        "entity_count": len(entities),
        "candidate_count": sum(len(entity.get("candidates", [])) for entity in entities),
        "assertion_count": sum(len(entity.get("assertions", [])) for entity in entities),
        "entity_counts": dict(sorted(counts.items())),
    }
```

Implement `_raise_archive_shape_error(names)` with three cases only:

```python
if any(name.endswith("/manifest.json") or "/documents/" in name for name in names):
    raise ValueError("intermediate model-proposal archive, not a leaderboard submission")
prefixes = {name.split("/", 1)[0] for name in names if "/" in name}
if len(prefixes) == 1 and next(iter(prefixes)) != "output":
    raise ValueError("submission is nested under a wrapper directory")
raise ValueError("submission must contain exactly output/1.json through output/100.json")
```

Implement the record loop in private `_validate_output_bytes(data, documents, schemas) -> dict[str, object]`.
Have `validate_output_zip()` read the file bytes and delegate to `_validate_output_bytes()`.
Have `build_output_zip()` validate its in-memory bytes with `_validate_output_bytes()` before creating the destination file.
Do not write an invalid archive to disk and do not duplicate the record loop.

- [ ] **Step 5: Implement the thin command**

```python
def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("archive", type=Path)
    parser.add_argument("--input", type=Path, default=Path("input.zip"))
    args = parser.parse_args()
    documents = read_zip_documents(args.input)
    validate_document_names(list(documents))
    print(json.dumps(validate_output_zip(args.archive, documents), sort_keys=True))
```

Let uncaught `ValueError` produce a nonzero exit status and visible reason.

- [ ] **Step 6: Run GREEN and regression tests**

Run:

```powershell
.\.venv\Scripts\python.exe -m unittest tests.test_validate_submission tests.test_submission -v
```

Expected: PASS.

- [ ] **Step 7: Commit the preflight**

```powershell
git add src/medical_race/submission/__init__.py tools/validate_submission.py tests/test_validate_submission.py tests/test_submission.py
git commit -m "feat: add final submission preflight"
```

---

### Task 2: Observable candidate ranking and linking audit

**Files:**
- Modify: `src/medical_race/linking/rxnorm.py`
- Modify: `src/medical_race/linking/icd10.py`
- Create: `tools/audit_linking.py`
- Modify: `tests/test_rxnorm_linker.py`
- Modify: `tests/test_icd10.py`
- Create: `tests/test_audit_linking.py`

**Interfaces:**
- Produces: `rank_drug_candidates(text: str, terms: tuple[RxNormTerm, ...], concept_level: str = "all_retrievable") -> tuple[RxNormTerm, ...]`.
- Produces: `exact_icd_candidates(text: str, terms: tuple[ICD10Term, ...]) -> tuple[ICD10Term, ...]`.
- Produces: `audit_linking(documents, rxnorm_terms, icd_terms, model_proposals=None) -> dict[str, object]`.
- Preserves: `link_drug()` and `link_diagnosis()` outputs for every existing test.

- [ ] **Step 1: Write ranking-preservation tests**

Add assertions that the fixture query `aspirin` produces RxCUIs `("3", "6", "5")` from `rank_drug_candidates()` while `link_drug(..., candidate_output="top2")` remains `("3", "6")`.
Add ICD fixture terms with two leaf codes sharing one normalized title and assert that `exact_icd_candidates()` returns both codes in deterministic order while `build_term_index()` continues dropping the ambiguous title.

- [ ] **Step 2: Run ranking tests and observe RED**

Run:

```powershell
.\.venv\Scripts\python.exe -m unittest tests.test_rxnorm_linker tests.test_icd10 -v
```

Expected: FAIL because both ranking functions are missing.

- [ ] **Step 3: Extract the existing RxNorm ordering without changing it**

Move the current matching and sorting body from `link_drug()` into `rank_drug_candidates()`.
Return the deduplicated `RxNormTerm` tuple before the top-one or top-two limit.
Keep policy validation in both public functions through one shared `_validate_concept_level()` helper or one inline membership check.

```python
ranked = rank_drug_candidates(text, terms, concept_level)
if not ranked:
    return None
limit = 1 if candidate_output == "top1" else 2
return LinkResult(tuple(term.rxcui for term in ranked[:limit]), ranked[0].text)
```

- [ ] **Step 4: Add exact ICD candidate inspection**

```python
def exact_icd_candidates(
    text: str,
    terms: tuple[ICD10Term, ...],
) -> tuple[ICD10Term, ...]:
    normalized = normalize_icd_text(text)
    by_code = {
        term.code: term
        for term in terms
        if term.is_leaf and normalize_icd_text(term.name) == normalized
    }
    return tuple(by_code[code] for code in sorted(by_code))
```

- [ ] **Step 5: Write the failing audit test**

Build two in-memory documents containing one linked drug, one unlinked drug proposal, one linked diagnosis proposal, and one ambiguous diagnosis proposal.
Pass validated `ModelProposal` mappings directly to `audit_linking()`.
Assert deterministic records with `document`, `text`, `type`, `source`, `normalized_query`, `status`, and ranked candidate metadata.
Assert summary counts for `queries`, `linked`, `ambiguous`, and `unlinked`.

- [ ] **Step 6: Run the audit test and observe RED**

Run:

```powershell
.\.venv\Scripts\python.exe -m unittest tests.test_audit_linking -v
```

Expected: FAIL because `tools.audit_linking` does not exist.

- [ ] **Step 7: Implement the read-only audit**

Collect drug queries from `extract_drugs()` and diagnosis queries from `extract_diagnoses()`.
When `model_proposals` is supplied, ground only `THUá»C` and `CHáº¨N_ÄOÃN` proposals with `ground_proposals()` and add them with source `qwen`.
Deduplicate only identical `(document, start, end, type, source)` records so duplicate raw occurrences remain distinct.

For each drug query, call `rank_drug_candidates()` and serialize each returned term as:

```python
{
    "id": term.rxcui,
    "text": term.text,
    "term_type": term.term_type,
    "source": term.source,
    "preferred": term.preferred,
}
```

For each diagnosis query, call `exact_icd_candidates()` and serialize `code`, `name`, `model`, and `is_leaf`.
Set status to `unlinked` for zero candidates, `ambiguous` for multiple distinct IDs, and `linked` for one distinct ID.
Sort records by document number, raw start, raw end, type, and source.

The CLI will accept `--input`, `--rxnorm`, `--icd`, optional `--model-proposals`, `--output`, `--expected-md5`, and `--expected-icd-sha256`.
Reuse the pinned defaults from `tools.build_submission` and write JSON with `ensure_ascii=False`, `indent=2`, `sort_keys=True`, and exclusive creation.

- [ ] **Step 8: Run GREEN and linker regression tests**

Run:

```powershell
.\.venv\Scripts\python.exe -m unittest tests.test_audit_linking tests.test_rxnorm_linker tests.test_rxnorm_precision tests.test_rxnorm_linker_performance tests.test_icd10 tests.test_diagnosis_pipeline tests.test_model_pipeline -v
```

Expected: PASS with unchanged production linking assertions.

- [ ] **Step 9: Commit linking diagnostics**

```powershell
git add src/medical_race/linking/rxnorm.py src/medical_race/linking/icd10.py tools/audit_linking.py tests/test_rxnorm_linker.py tests/test_icd10.py tests/test_audit_linking.py
git commit -m "feat: add linking diagnostics"
```

---

### Task 3: One-command rule and Qwen controls

**Files:**
- Create: `tools/build_controls.py`
- Create: `tests/test_build_controls.py`

**Interfaces:**
- Produces: `build_controls(input_zip, rxnorm_zip, icd_path, proposal_root, destination, expected_md5, expected_icd_sha256, rule_config=Path("configs/submissions/07_add_diagnoses.json"), qwen_config=Path("configs/submissions/08_qwen_grounded.json")) -> dict[str, object]`.
- Consumes: `build_submission()`, `validate_output_zip()`, and `diff_submission_archives()`.

- [ ] **Step 1: Write the failing fixture control test**

Create canonical input, minimal RxNorm and ICD fixtures, one model-off config, one model-on config, and a valid proposal directory through `generate_proposal_directory()`.
Call `build_controls()` once.
Assert the existence and preflight success of:

```text
rule-control.zip
rule-control.report.json
qwen-control.zip
qwen-control.report.json
rule-to-qwen.diff.json
controls.summary.json
```

Assert rule `model_parameters == 0`, Qwen `model_parameters == 4_000_000_000`, both archive checksums equal their preflight checksums, and the diff adds the fixture Qwen entity without changing stable entities.

- [ ] **Step 2: Run the control test and observe RED**

Run:

```powershell
.\.venv\Scripts\python.exe -m unittest tests.test_build_controls -v
```

Expected: FAIL because `tools.build_controls` does not exist.

- [ ] **Step 3: Implement the minimal orchestrator**

Require `destination.is_dir()` and reject any pre-existing target file before either build starts.
Read and validate the canonical documents once.
Call `build_submission()` for the rule config without proposals and the Qwen config with `proposal_root`.
Preflight each ZIP with `validate_output_zip()`.
Call `diff_submission_archives()` and write the reports and diff with a small exclusive JSON helper:

```python
def _write_json(path: Path, value: object) -> None:
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, sort_keys=True)
        stream.write("\n")
```

Reject an unexpectedly empty rule entity set or zero candidate count with `ValueError("rule control produced no entities or candidates")`.
Reject an unexpectedly empty Qwen entity set or zero candidate count with the corresponding Qwen message.
Do not require Qwen to add an entity because S9 proved that zero accepted additions is possible.

The returned and written summary will contain only report paths, archive paths, both preflight reports, and diff counts excluding detailed rows.

- [ ] **Step 4: Add the command-line interface**

Accept `--input`, `--rxnorm`, `--icd`, `--model-proposals`, `--output-dir`, both expected ontology digests, and optional config overrides.
Use the same pinned defaults as `tools/build_submission.py`.
Print the summary as sorted JSON.
Never import Transformers or invoke `tools/run_kaggle_s009.py`.

- [ ] **Step 5: Run GREEN and build regressions**

Run:

```powershell
.\.venv\Scripts\python.exe -m unittest tests.test_build_controls tests.test_build_submission tests.test_model_build tests.test_submission_diff tests.test_validate_submission -v
```

Expected: PASS.

- [ ] **Step 6: Commit the control builder**

```powershell
git add tools/build_controls.py tests/test_build_controls.py
git commit -m "feat: build reproducible controls"
```

---

### Task 4: Post-update operational checklist and final verification

**Files:**
- Create: `docs/post_update_bringup_checklist.md`
- Modify: `docs/TEAM_ONBOARDING.md`

**Interfaces:**
- Documents: The exact inactive sequence for receiving, auditing, controlling, and deciding on the updated dataset.
- References: `tools/audit_sources.py`, `tools/validate_submission.py`, `tools/build_controls.py`, `tools/audit_linking.py`, and `tools/diff_submissions.py`.

- [ ] **Step 1: Write the checklist**

Start with this gate:

```markdown
Do not execute this checklist until the user explicitly confirms that the organizer update is live and supplies the new official artifacts.
```

Include checkboxes and exact virtual-environment commands for:

1. Copying the supplied artifact to a new immutable path without replacing the legacy `input.zip`.
2. Recording SHA-256, strict UTF-8 status, exact document names, lengths, line counts, and section-header distributions.
3. Comparing the published schema and policy with `research/competition_policy.md` without assuming a change.
4. Running the rule-only build first and preflighting it.
5. Validating proposal records against the new raw hashes before the Qwen control.
6. Running both controls and their semantic diff.
7. Running the linking audit and separating linked, ambiguous, and unlinked buckets.
8. Classifying observed drift as input, contract, extraction, assertion, or linking drift.
9. Selecting one primary variable for the first portal submission and recording it in `docs/submissions.csv`.
10. Deferring training until both controls and the drift report exist.

- [ ] **Step 2: Update onboarding without claiming the update is live**

Replace the stale statement that Submission 9 is still running with its corrected score and conclusion.
Link the new checklist as the only start point after explicit update confirmation.
Keep Submission 8 and corrected Submission 9 tied at `16.13250` as the current stable evidence.

- [ ] **Step 3: Verify documentation and syntax**

Run:

```powershell
rg -n "Do not execute|validate_submission.py|build_controls.py|audit_linking.py|16.13250" docs/post_update_bringup_checklist.md docs/TEAM_ONBOARDING.md
.\.venv\Scripts\python.exe -m compileall -q src tools tests
git diff --check
```

Expected: Every required phrase is present, compilation exits `0`, and `git diff --check` prints nothing.

- [ ] **Step 4: Run the full test suite**

Run:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Expected: All tests pass with no errors or failures.

- [ ] **Step 5: Run real local preflight and observational audit**

Run the preflight against the corrected Submission 9 archive:

```powershell
$env:PYTHONPATH='src;.'
.\.venv\Scripts\python.exe tools\validate_submission.py --input input.zip outputs\submissions\09_qwen_grounded.zip
```

Expected: `entry_count` is `100`, `entity_count` is `521`, `candidate_count` is `150`, `assertion_count` is `139`, and SHA-256 is `90921e43e204909cfe0c0c5c47c350d9b53634b427f5a3fff5f29ead9df4e142`.

Run the linking audit into a new ignored output path and inspect summary counts:

```powershell
.\.venv\Scripts\python.exe tools\audit_linking.py --input input.zip --model-proposals outputs\model_proposals\qwen3-4b-s009 --output outputs\reports\linking-audit-s009.json
```

Expected: The command exits `0`, produces deterministic sorted JSON, and reports nonzero linked and unlinked query buckets without changing any submission archive.

- [ ] **Step 6: Commit documentation and verification evidence**

```powershell
git add docs/post_update_bringup_checklist.md docs/TEAM_ONBOARDING.md
git commit -m "docs: add post-update bring-up checklist"
```

Do not commit ignored reports or rebuilt archives.

---

## Final acceptance review

- [ ] Confirm that the proposal archive is rejected before upload and the corrected S9 archive passes.
- [ ] Confirm that production top-one and top-two outputs are unchanged by ranking observability.
- [ ] Confirm that no new package, model, ontology, or output field was added.
- [ ] Confirm that both control configurations retain their pinned model budgets.
- [ ] Confirm that the checklist explicitly remains inactive pending user confirmation.
- [ ] Review every committed diff against `docs/superpowers/specs/2026-07-16-interim-readiness-tooling-design.md`.
