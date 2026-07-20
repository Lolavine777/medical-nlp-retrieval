# Team Onboarding

This repository is an offline clinical NLP system for the Viettel AI Race 2026 task.
The current best Round 1 evidence is Submission 12 at score `17.25890`.
When the organizer confirms the update is live, start with the [post-update bring-up checklist](post_update_bringup_checklist.md).

The active three-person assignments, file boundaries, and Git workflow are in [Team Workstreams, 16 July 2026](TEAM_WORKSTREAMS_2026-07-16.md).
Read that page before choosing a task from the general list below.

## Start here

Read these files in order:

1. [`AGENTS.md`](../AGENTS.md) for non-negotiable repository and competition rules.
2. [`CODEX_HANDOFF.md`](../CODEX_HANDOFF.md) for annotation findings and the long-term roadmap.
3. [`docs/submission_strategy.md`](submission_strategy.md) for experiment and promotion rules.
4. [`docs/submissions.csv`](submissions.csv) for the actual leaderboard history.
5. [`docs/qwen_free_gpu_runbook.md`](qwen_free_gpu_runbook.md) only if working on the Qwen proposal run.

Do not begin by reading every plan in `docs/superpowers/`.
Those plans are historical evidence and are useful only when the task points to one.

## Local setup

Use Python 3.11 or newer.
Run Python through the repository virtual environment.

```powershell
py -m venv .venv
$env:PYTHONPATH = "src;."
$env:PYTHONIOENCODING = "utf-8"
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

The full suite is the first required check before and after a change.
The current baseline is verified by the full suite command above; the exact count is intentionally not hard-coded in onboarding.

## System map

| Area | Location | Responsibility |
|---|---|---|
| Raw loading and offsets | `src/medical_race/loader.py`, `offsets.py` | Preserve exact UTF-8 text and end-exclusive positions. |
| Sections and line roles | `src/medical_race/sections/`, `line_roles.py` | Identify clinical context without mutating source text. |
| Entity extraction | `src/medical_race/extraction/` | Extract drugs, laboratories, symptoms, and diagnoses. |
| Assertions | `src/medical_race/assertions/` | Derive negation, family, and historical labels. |
| Linking | `src/medical_race/linking/` | Link diagnoses to pinned ICD and drugs to pinned RxNorm. |
| Pipeline and schema | `src/medical_race/pipeline.py`, `output.py` | Merge predictions and enforce type-dependent output fields. |
| Model proposals | `src/medical_race/model_proposals.py`, `tools/generate_model_proposals.py` | Ground Qwen suggestions through deterministic gates. |
| Builds and diffs | `tools/build_submission.py`, `tools/diff_submissions.py` | Create reproducible archives and explain prediction changes. |
| Tests | `tests/` | Protect offsets, extraction, assertions, linking, schemas, and builds. |

## Current state

Submission 12 is the current candidate at score `17.25890`.
Its components were WER `82.6481`, assertion Jaccard `18.6554`, and candidate Jaccard `16.1416`.
It preserves every Submission 8 entity and adds 91 precision-filtered Qwen entities.
Submission 8 remains the reproducible parent control at score `16.13250`.
Do not start post-update work until the user explicitly confirms that the organizer update is live.

The main strategic gap is recall and candidate linking, not packaging.
Small rule tweaks are lower priority than interpretable coverage or linking improvements.

## Pick one bounded task

### A. Post-update intake

Use this only after the team lead confirms that the organizer update is live and preserves the new official artifacts.

Definition of done:

- Follow `docs/post_update_bringup_checklist.md` in order.
- Hash and preserve the new input and official problem statement before running code.
- Build unchanged rule and Qwen controls before changing extraction, linking, assertions, or prompts.
- Classify contract and distribution drift before selecting one experiment variable.

Primary files:

- `docs/post_update_bringup_checklist.md`
- `research/competition_policy.md`
- `tools/audit_sources.py`
- `tools/build_controls.py`

### B. Candidate-linking recall

Inspect missed or unlinked diagnosis and drug mentions against the pinned ontology snapshots.

Definition of done:

- Add a failing fixture for each proposed normalization or alias behavior.
- Keep one top-one candidate for drugs unless an experiment explicitly changes that policy.
- Record ontology provenance and license information for any added source.
- Measure candidate changes separately from span and assertion changes.

Primary files:

- `src/medical_race/linking/`
- `ontologies/`
- `tests/test_icd10*.py`
- `tests/test_rxnorm*.py`
- `data/DATA_SOURCES.md`

### C. Assertion scope QA

Find false negation, family, or historical labels in synthetic fixtures and generalize the rule only when the scope is clear.

Definition of done:

- Add a minimal regression test before changing a rule.
- Test clause boundaries, contrast words, section priors, and family reporter versus family experiencer.
- Run assertion tests and the full suite.

Primary files:

- `src/medical_race/assertions/`
- `tests/test_assertions.py`
- `tests/test_assertion_regressions.py`

### D. Span recall

Identify a missing class of symptoms, laboratory mentions, or diagnoses and improve only that extractor.

Definition of done:

- Use general section or line-role evidence rather than document-number rules.
- Preserve exact raw offsets and duplicate occurrences.
- Add positive and negative fixtures.
- Build a local semantic diff before considering a portal submission.

Primary files:

- `src/medical_race/extraction/`
- `src/medical_race/line_roles.py`
- `tests/test_*extraction*.py`

### E. Model-training preparation

Prepare synthetic or weakly supervised training data without claiming it is gold annotation.

Definition of done:

- Store generated data under `data/synthetic/` or `data/processed/`.
- Record source, license, generation configuration, and label mapping.
- Keep the model subset within the combined 9B parameter budget.
- Add a document-level holdout and report where labels came from.

Primary files:

- `data/DATA_SOURCES.md`
- `configs/model_budget.json`
- `configs/model_configurations.json`
- `docs/assumptions.md`

## Rules for changes

- Change one primary variable per experiment.
- Never mutate `input.zip` or raw document text.
- Never hard-code a public document number, span, code, or answer.
- Never invent output fields or candidates.
- Keep model suggestions behind deterministic grounding and validation.
- Record every submission with commit, config, checksum, parent, hypothesis, and result in `docs/submissions.csv`.
- Prefer a failing test and the smallest general rule that fixes it.

## Handoff format

Before starting, post one sentence with the task letter and hypothesis.
When finished, report changed files, test command and result, semantic diff counts, and whether the change is ready for a portal experiment.

If a task touches the Qwen run, do not start another full inference job until the existing archive has been validated or the runbook explicitly calls for a new one.
