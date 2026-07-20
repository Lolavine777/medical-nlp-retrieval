# Team Workstreams, 16 July 2026

This page is the active assignment board for the three-person team.
The current best Round 1 result is Submission 12 at `17.25890`.
Submission 8 remains its reproducible parent control at `16.13250`.

The organizer announcement supplied by the team lead says Round 1 remains active until Tuesday, 21 July 2026, when the upgraded problem and dataset are expected.
The deadline is expected to move to the end of 4 August 2026.
Treat those dates as scheduling information only until the team lead confirms and preserves the new official artifacts.

## Shared setup

Start every task from the current remote baseline:

```powershell
git switch master
git pull --ff-only origin master
py -m venv .venv
$env:PYTHONPATH = "src;."
$env:PYTHONIOENCODING = "utf-8"
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

The official `input.zip`, RxNorm archive, model proposals, generated reports, and checkpoints are not shared through Git.
Obtain required official artifacts from the team lead or the organizer, verify them against the repository provenance, and never stage them.
Never hard-code a Round 1 document, phrase, span, candidate, or answer.

Read `AGENTS.md`, `CODEX_HANDOFF.md`, `docs/submission_strategy.md`, and this page before editing code.

## Workstream A: Retrieval and reranking

Owner: Teammate A.

Branch:

```powershell
git switch -c team-a/linking-recall
```

Goal: improve ICD and RxNorm candidate recall and ranking evidence while preserving the current final top-one behavior by default.

Owned files:

- `src/medical_race/linking/`;
- `tools/audit_linking.py`;
- focused ICD, RxNorm, and linking-audit tests;
- `research/linking_error_inventory_round1.md`;
- `data/DATA_SOURCES.md` only when proposing a licensed external source.

First deliverable:

1. Reproduce or inspect the current audit of 171 queries: 111 linked, 39 ambiguous, and 21 unlinked.
2. Group the ambiguous and unlinked cases by reusable failure class in `research/linking_error_inventory_round1.md`.
3. Add deterministic lexical top-k ranking diagnostics with tests.
4. Prove that existing top-one linker outputs and default pipeline predictions remain unchanged.

Focused verification:

```powershell
$env:PYTHONPATH = "src;."
.\.venv\Scripts\python.exe -m unittest tests.test_audit_linking tests.test_icd10 tests.test_rxnorm_linker tests.test_rxnorm_precision -v
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Do not edit `src/medical_race/pipeline.py`, model prompts, submission configurations, packaging tools, or `docs/submissions.csv`.
Do not change output candidate cardinality in this branch.

Message to send:

> Bạn phụ trách retrieval/reranking ICD và RxNorm.
> Bắt đầu từ `master`, tạo branch `team-a/linking-recall`, rồi phân loại 21 query chưa link và 39 query ambiguous thành các nhóm lỗi tổng quát.
> Deliverable đầu tiên là error inventory và lexical top-k diagnostics có test, nhưng top-one output hiện tại phải giữ nguyên mặc định.
> Không sửa `pipeline.py`, config submission, packaging hoặc `docs/submissions.csv`.

## Workstream B: Extraction, type, and assertions

Owner: Teammate B.

Branch:

```powershell
git switch -c team-b/extraction-assertion
```

Goal: improve mention coverage, type precision, and assertion scope while preserving exact raw offsets and type-dependent schemas.

Owned files:

- `src/medical_race/extraction/`;
- `src/medical_race/assertions/`;
- `src/medical_race/sections/` and `src/medical_race/line_roles.py` when a tested structural fix requires them;
- focused extraction, section, assertion, and offset tests;
- `research/extraction_assertion_error_inventory_round1.md`.

First deliverable:

1. Compare stable predictions with available grounded Qwen proposal evidence.
2. Record reusable missing-span, wrong-type, assertion-scope, and structural false-positive classes in `research/extraction_assertion_error_inventory_round1.md`.
3. Select one general failure class.
4. Add a positive fixture, a negative fixture, and an exact-offset regression before implementing the smallest general fix.

Focused verification:

```powershell
$env:PYTHONPATH = "src;."
.\.venv\Scripts\python.exe -m unittest tests.test_assertions tests.test_assertion_regressions tests.test_extraction tests.test_extraction_regressions tests.test_symptom_extraction tests.test_diagnosis_extraction -v
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Do not edit linking candidate policy, ontology files, model prompts, submission configurations, packaging tools, or `docs/submissions.csv`.
Do not infer gold labels from model proposals.

Message to send:

> Bạn phụ trách extraction, type và assertion.
> Bắt đầu từ `master`, tạo branch `team-b/extraction-assertion`, rồi lập error inventory từ stable output và grounded Qwen proposals.
> Sau đó chọn đúng một nhóm lỗi tổng quát, viết positive test, negative test và exact-offset regression trước khi sửa rule.
> Không sửa linking policy, ontology, model prompt, config submission, packaging hoặc `docs/submissions.csv`.

## Workstream C: Model, integration, and experiments

Owner: Team lead.

Recommended branch prefix: `lead/` for lead-controlled implementation branches.

The team lead owns:

- model proposals, weak supervision, model configuration, and the combined `<= 9B` budget;
- `src/medical_race/pipeline.py` and cross-module integration;
- pull-request review and merge decisions;
- submission configurations, semantic diffs, packaging, portal experiments, and `docs/submissions.csv`;
- distribution of official or generated local artifacts outside Git.

Immediate deliverables are to keep the verified baseline reproducible, review the two bounded teammate pull requests, and prepare model work that can be rerun after the upgraded dataset arrives.

## Pull-request and merge gates

Each pull request must include:

- one sentence stating the hypothesis;
- the exact changed files;
- focused and full-suite test results;
- prediction diff counts when behavior changes;
- a statement saying whether the change is ready for integration only or for a controlled portal experiment.

Only the team lead merges cross-cutting changes, changes `pipeline.py`, creates numbered experiment configurations, builds final archives, submits to the portal, or records leaderboard results.
One pull request should test one primary hypothesis.

## Upgrade freeze

When the team lead confirms the upgraded artifacts are live:

1. stop new merges and portal experiments;
2. preserve and hash the official artifacts;
3. follow [Post-Update Bring-Up Checklist](post_update_bringup_checklist.md);
4. verify the contract and schemas before adapting code;
5. run the rule-only control and matching Qwen control;
6. compare drift, then re-prioritize all three workstreams.

Do not promote model training, prompt changes, ontology expansion, or threshold tuning after the update until both controls and the drift report exist.
