# Medical AI Race 2026

This repository is an evidence-first, offline clinical NLP pipeline for the Viettel AI Race 2026 medical task.
The current milestone audits the official artifacts, fixes annotation invariants, and defines the end-to-end rule baseline before model training.

## Canonical artifacts

- `input.zip` is the single canonical raw input artifact and must remain at the repository root.
- `AI Race 2026 - Cuộc đua AI cho kỹ sư Việt Nam.html` is the saved authenticated official phase page.
- Do not copy `input.zip` into `data/raw/` or normalize raw text in place.

Current SHA-256 values:

- `input.zip`: `46fe4a578b2c4478faa7c570b218218f539c0bbf1ea409168ae67a14ad86ca35`.
- Saved official HTML: `a7cbac16fa2ec0c994c1ca7c6052b7f1d6035ebecd69b55a0f4c0402ed0b3879`.

## Verified findings

- The ZIP contains exactly `input/1.txt` through `input/100.txt` and all files decode as strict UTF-8.
- The corpus contains 170,948 UTF-8 bytes, 132,336 Python characters, and 2,964 physical lines.
- Document character counts range from 136 to 4,428 with a median of 1,222.5.
- Drug-like rules match 126 lines in 49 documents and laboratory-like rules match 130 lines in 40 documents under the documented audit regexes.
- Negation cues occur 393 times in 86 documents, family cues 16 times in 12 documents, and history cues 482 times in 94 documents under the documented audit regexes.
- The most frequent detected section headers are `Đánh giá tại bệnh viện` at 74, `Tiền sử bệnh hiện tại` at 52, `Tiền sử bệnh` at 48, `Tiền sử bệnh nội khoa` at 39, and `Triệu chứng hiện tại` at 33.
- The official HTML example contains 19 entities and preserves two occurrences each of `táo bón` and `lo âu`.
- All 19 example spans satisfy end-exclusive slicing after reconstructing the offset-significant CRLF and leading-space layout.
- The observed `THUỐC` schema has candidates and assertions, while the observed `TRIỆU_CHỨNG` schema has assertions but no candidates.
- The official page states WER for text, Jaccard for assertions and candidates, weights of 0.3, 0.3, and 0.4, self-hosting, and a 9B limit.
- Organizer clarification confirms that 9B is the combined parameter budget across all models, not a per-model limit.

The counts above describe regex evidence, not ground-truth entity counts.
The example contains `prn`, `qhs`, `qid`, and `xl`, but those tokens have zero occurrences in the 100 input documents under exact token matching.

## Important unknowns

- The official ICD namespace, release, and code list are not present in the saved phase HTML or ZIP.
- The official RxNorm release, subset, and target term type are not present in the saved phase HTML or ZIP.
- Complete schemas for diagnosis, laboratory name, and laboratory result entities are not demonstrated.
- The mention-matching algorithm and whether `position` participates in scoring are not published.
- Multi-code ground-truth frequency is unknown.
- Historical and family policies outside the one official example remain provisional.
- The observation that submission quotas may apply per team member is unconfirmed and is not an architectural assumption.

## Proposed architecture

The baseline uses an immutable loader, raw-index mappings, section parsing, rule extraction, scoped assertions, approved local ontology retrieval, deterministic constraints, a type-dependent serializer, validation, and a provisional local evaluator.
No large model is implemented in this milestone.
The parameter ledger is [configs/model_budget.json](configs/model_budget.json) and currently records zero model parameters.

## Reproduce the audit

Create the local virtual environment once:

```powershell
py -m venv .venv
```

Run verification and regenerate the ignored audit report:

```powershell
$env:PYTHONPATH = "src;."
$env:PYTHONIOENCODING = "utf-8"
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe tools\audit_sources.py
```

The generated report is `outputs/source_audit.json`.

## Repository map

- `configs/` stores reproducible configuration and the model-budget ledger.
- `data/` separates external, synthetic, and processed data from the canonical root artifact.
- `ontologies/` will hold pinned organizer-approved ICD and RxNorm snapshots.
- `research/` stores sourced findings and machine-readable provenance.
- `docs/` stores assumptions, annotation policy, experiments, specifications, and plans.
- `src/medical_race/` holds implemented pipeline components only when their checkpoint begins.
- `tests/` protects source interpretation and output invariants.
- `outputs/` contains rebuildable reports and generated submissions.

## Project documents

- [Research notes](research/notes.md).
- [Assumption register](docs/assumptions.md).
- [Annotation policy](docs/annotation_policy.md).
- [Baseline checkpoint plan](docs/baseline_plan.md).
- [Leaderboard experiment ledger](docs/experiments.md).
- [Evidence-first design](docs/superpowers/specs/2026-07-11-evidence-first-baseline-design.md).
- [Organizer clarifications](docs/superpowers/specs/2026-07-11-organizer-clarifications.md).
