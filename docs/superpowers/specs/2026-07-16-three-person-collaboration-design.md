# Three-Person Collaboration Design

## Objective

Divide the current Round 1 work among three people so each person can make useful progress without creating conflicting pipelines or blocking the other two.
Prepare the repository and team to stop, audit, and redirect work when the organizer publishes the upgraded problem and dataset.

## Timeline evidence and operating assumption

The user supplied an organizer announcement stating that the upgraded Round 2 version is temporarily delayed because of a technical issue.
The existing Round 1 problem and leaderboard remain active until Tuesday, 21 July 2026.
The upgraded version is expected on 21 July 2026, and the competition deadline is expected to move to the end of 4 August 2026.

This announcement changes scheduling, not the current technical contract.
Until the upgraded artifacts are actually published and supplied, all work must use the existing confirmed rules and must remain generalizable beyond the public Round 1 documents.
No teammate may hard-code a Round 1 document, phrase, span, candidate, or answer.

## Considered collaboration structures

### Experiment ownership

Each teammate could own one leaderboard hypothesis from implementation through submission.
This is fast for isolated experiments but would cause frequent conflicts in pipeline, configuration, packaging, and submission-ledger files.

### Pipeline-layer ownership

The team could split data preparation, prediction, and evaluation into three sequential layers.
This creates clean conceptual boundaries but makes progress dependent on upstream handoffs.

### Module ownership with lead integration

This is the selected structure.
Each teammate owns a stable technical area and its tests, while the lead stream owns shared pipeline integration, experiment configuration, packaging, and portal decisions.
It supports independent progress and keeps one configurable production pipeline.

## Workstream A: Retrieval and reranking

Teammate A owns candidate-generation and ranking evidence for RxNorm and ICD.
The primary objective is to improve candidate recall and ranking quality without changing final output cardinality until a controlled experiment is approved.

Owned areas are:

- `src/medical_race/linking/`;
- focused ICD and RxNorm tests;
- `tools/audit_linking.py`;
- ontology provenance updates in `data/DATA_SOURCES.md` when new sources are proposed.

The first deliverable is an analysis of the current real audit containing 159 unlinked and 56 ambiguous queries.
The first implementation candidate is deterministic lexical top-k retrieval with traceable ranking features and tests proving the existing top-one output remains unchanged by default.

Teammate A must not independently edit `src/medical_race/pipeline.py`, submission configurations, the submission ledger, model prompts, or final packaging tools.

## Workstream B: Extraction, type, and assertions

Teammate B owns rule-based mention recognition, section context, type precision, and assertion scope.
The primary objective is to improve text coverage and assertion quality without weakening exact offsets or type-dependent schemas.

Owned areas are:

- `src/medical_race/extraction/`;
- `src/medical_race/assertions/`;
- `src/medical_race/sections/` and `src/medical_race/line_roles.py` when a tested structural fix requires them;
- focused extraction, section, assertion, and offset tests.

The first deliverable is a compact structural error inventory comparing stable predictions with grounded Qwen proposal evidence.
The first implementation must fix one general failure class through a failing positive fixture, a failing negative fixture, and an exact-offset regression.

Teammate B must not independently edit candidate policy, ontology files, model prompts, submission configurations, the submission ledger, or final packaging tools.

## Workstream C: Model, integration, and experiments

The team lead owns model preparation, shared integration, experiment design, PR review, reproducible controls, final packaging, and result logging.
The primary objective is to turn accepted work from all streams into one stable product while preparing model work that can be rerun after the upgrade.

Owned areas are:

- `src/medical_race/model_proposals.py` and model-generation tools;
- `src/medical_race/pipeline.py` and cross-module integration tests;
- model budget and model configuration files;
- submission configurations, reports, diffs, and `docs/submissions.csv`;
- final archive preflight, control builds, and manual portal handoff.

The first deliverables are to publish the current verified baseline, create the two human handoff tasks, review incoming PRs, and prepare model or weak-supervision work that does not depend on unreleased Round 2 data.

## GitHub workflow

The current verified `master` must be pushed before either teammate creates a branch.
Every task branch starts from that exact remote baseline and remains short-lived.

Recommended branch prefixes are `team-a/`, `team-b/`, and `lead/`.
Each branch should contain one testable hypothesis rather than an entire workstream backlog.

Every pull request must report:

- one sentence describing the hypothesis;
- the exact files changed;
- the focused test command and result;
- the full-suite command and result;
- prediction diff counts when output behavior changes;
- whether the change is ready only for integration or also for a controlled portal experiment.

Only the integration owner merges cross-cutting changes, creates numbered submission configurations, builds final archives, records portal experiments, or changes the stable baseline.
Generated outputs, downloaded ontologies, model checkpoints, and raw artifacts remain uncommitted.

## Upgrade boundary on 21 July

Before the upgraded version arrives, all three streams may develop and test improvements against the existing data.
Round 1 leaderboard submissions remain controlled experiments and are not evidence that a change will generalize to Round 2.

When the user confirms that the upgraded artifacts are live, the team will:

1. pause new merges and portal experiments;
2. preserve and hash the new official artifacts;
3. follow `docs/post_update_bringup_checklist.md`;
4. verify the output contract before adapting code;
5. run the rule-only control, regenerate matching Qwen proposals, run the Qwen control, and compare drift;
6. re-prioritize all three workstreams from the observed extraction, assertion, and linking gaps.

No model training, prompt change, ontology expansion, or threshold tuning may be promoted after the upgrade until both controls and the drift report exist.

## Vietnamese team announcement

The following message is intended for the two teammates:

> Chào mọi người, BTC vừa thông báo bản nâng cấp Đề 2 tạm hoãn đến thứ Ba 21/7; Round 1 vẫn giữ nguyên trong thời gian này và hạn thi dự kiến được gia hạn đến hết 4/8.
> Nhóm mình sẽ chia ba luồng làm việc trên cùng một pipeline: bạn A phụ trách retrieval/reranking ICD và RxNorm; bạn B phụ trách extraction, type và assertion; mình phụ trách model, tích hợp, review PR, đóng gói và quản lý submission.
> Trước khi bắt đầu, mọi người pull `master`, chạy toàn bộ test rồi tạo branch ngắn theo prefix `team-a/` hoặc `team-b/`.
> Mỗi PR cần ghi rõ giả thuyết, test đã chạy và prediction diff nếu có.
> Không sửa riêng `pipeline.py`, config submission hay `docs/submissions.csv`, không hard-code dữ liệu Round 1 và chưa tự nộp bài nếu chưa thống nhất experiment.
> Khi bản nâng cấp được công bố, cả nhóm sẽ tạm dừng merge, audit dữ liệu mới và chạy lại hai control trước khi đổi chiến lược.

## Acceptance criteria

- Each teammate receives one owned module boundary, one first deliverable, and one prohibited shared boundary.
- The integration owner remains the only path for final prediction behavior and portal artifacts.
- The Vietnamese announcement communicates the work split, branch rules, pull-request evidence, and 21 July freeze.
- The collaboration structure does not assume that the upgraded technical contract is already live.
- The repository retains one configurable pipeline and one stable `master` baseline.
