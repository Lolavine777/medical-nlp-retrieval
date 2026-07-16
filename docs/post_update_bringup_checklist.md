# Post-Update Bring-Up Checklist

Do not execute this checklist until the user explicitly confirms that the organizer update is live and supplies the new official artifacts.

This checklist gathers evidence before changing extraction, linking, assertions, model prompts, or training data.
It does not authorize a portal upload.

## 1. Preserve the supplied artifacts

- [ ] Keep the legacy root `input.zip` unchanged.
- [ ] Save the new organizer input as `data/raw/post_update/input.zip`.
- [ ] Save the new official problem page as `data/raw/post_update/official.html`.
- [ ] Record both hashes before running the pipeline.

```powershell
$NewInput = 'data\raw\post_update\input.zip'
$NewHtml = 'data\raw\post_update\official.html'
Get-FileHash -Algorithm SHA256 -LiteralPath $NewInput
Get-FileHash -Algorithm SHA256 -LiteralPath $NewHtml
```

## 2. Audit the raw contract and corpus

- [ ] Set the repository environment without changing the raw files.
- [ ] Run strict UTF-8 decoding, document-name validation, length statistics, line counts, section headers, and cue distributions.
- [ ] Compare the new report with the legacy source audit.

```powershell
$env:PYTHONPATH = 'src;.'
$env:PYTHONIOENCODING = 'utf-8'
.\.venv\Scripts\python.exe tools\audit_sources.py --zip $NewInput --html $NewHtml --output outputs\post_update\source_audit.json
```

- [ ] Stop if document names, document count, encoding, required output fields, allowed entity types, offset semantics, metric weights, or model limits changed.
- [ ] Record confirmed changes in `research/competition_policy.md` and design the smallest contract update before running controls.
- [ ] Do not infer a policy change solely from corpus distribution drift.

## 3. Verify the legacy final archive boundary

- [ ] Confirm that the corrected Submission 9 artifact still passes final-ZIP preflight against the legacy input.

```powershell
.\.venv\Scripts\python.exe tools\validate_submission.py --input input.zip outputs\submissions\09_qwen_grounded.zip
```

- [ ] Never upload a ZIP containing `manifest.json`, `documents/*.json`, or a wrapper directory.

## 4. Build the rule-only control first

- [ ] Create a new empty control directory.
- [ ] Build the full stable rule pipeline represented by Submission 7 against the new input.
- [ ] Preflight the result.

```powershell
New-Item -ItemType Directory -Path outputs\post_update\rule -ErrorAction Stop
.\.venv\Scripts\python.exe tools\build_submission.py --input $NewInput --config configs\submissions\07_add_diagnoses.json --output outputs\post_update\rule\rule-control.zip --report outputs\post_update\rule\rule-control.report.json
.\.venv\Scripts\python.exe tools\validate_submission.py --input $NewInput outputs\post_update\rule\rule-control.zip
```

- [ ] Treat zero entities or zero candidates as an intake or contract failure, not a model-quality score.

## 5. Validate or regenerate Qwen proposal evidence

- [ ] Do not reuse proposal records whose raw SHA-256 values do not match the new input.
- [ ] Validate the proposal directory through the normal build path.
- [ ] If validation fails on raw hashes, generate a fresh proposal directory with the same pinned `Qwen/Qwen3-4B-Instruct-2507` revision and the existing free-GPU runbook.
- [ ] Do not train or change the prompt before the unchanged pinned model has produced the control evidence.

Set `$NewProposals` only after all proposal records validate against `$NewInput`:

```powershell
$NewProposals = 'outputs\model_proposals\post_update-qwen-control'
```

## 6. Build and compare both controls

- [ ] Create a new empty paired-control directory.
- [ ] Build, preflight, report, and diff both controls with one command.

```powershell
New-Item -ItemType Directory -Path outputs\post_update\controls -ErrorAction Stop
.\.venv\Scripts\python.exe tools\build_controls.py --input $NewInput --model-proposals $NewProposals --output-dir outputs\post_update\controls
```

- [ ] Confirm the rule control reports `0` model parameters.
- [ ] Confirm the Qwen control reports `4,000,000,000` model parameters.
- [ ] Inspect `outputs/post_update/controls/rule-to-qwen.diff.json` before considering any portal experiment.

## 7. Audit candidate retrieval and ranking evidence

- [ ] Produce deterministic linked, ambiguous, and unlinked drug and diagnosis query buckets.

```powershell
.\.venv\Scripts\python.exe tools\audit_linking.py --input $NewInput --model-proposals $NewProposals --output outputs\post_update\linking-audit.json
```

- [ ] Separate missing mention detection from missing ontology retrieval.
- [ ] Separate ambiguous exact titles from unlinked queries.
- [ ] Do not interpret coverage counts as accuracy without gold labels.

## 8. Classify drift and select one next variable

- [ ] Classify every observed change as input drift, contract drift, extraction drift, assertion drift, or linking drift.
- [ ] Prioritize linking, assertion and type precision, then spans and laboratory coverage.
- [ ] Select one primary variable for the first post-update portal submission.
- [ ] Record its commit, config, checksum, parent, hypothesis, and generalization class in `docs/submissions.csv` before upload.
- [ ] Defer training until the rule control, Qwen control, semantic diff, and linking audit exist.

The first portal artifact must pass `tools/validate_submission.py` immediately before manual upload.
