# AGENTS.md - Medical AI Race 2026

## Mission

Build a reproducible offline clinical NLP system that generalizes to private test data.

## Required context

Read `CODEX_HANDOFF.md`, `research/competition_policy.md`, and `docs/submission_strategy.md` before changing the system.
Treat raw inputs, official artifacts, organizer statements, ontology files, and submission results as source evidence.

## Non-negotiable rules

- Never mutate raw text; preserve UTF-8, whitespace, line endings, and duplicate mentions.
- Generate local offsets satisfying `raw_text[start:end] == text`; keep normalized text separately mapped.
- Treat ontology, span, candidate, and position policies as hidden variables resolved by controlled experiments, not clarification requests.
- Do not invent codes or output fields.
- Keep combined active model parameters `<= 9B`; declare the model subset and budget report before use.
- Do not bundle unused checkpoints into the final solution.
- Use external data only after license, provenance, redistribution, and label mapping are recorded in `data/DATA_SOURCES.md`.
- Maintain one stable configurable pipeline, not diverging codebases.
- Identify every submission by commit, config, checksum, parent, and hypothesis in `docs/submissions.csv`.
- Plan around five guaranteed daily submissions; treat legitimate team-member capacity as optional exploration only.
- Promote experiments only when gains are reproducible, interpretable, and plausibly private-test generalizable.
- Never hard-code public-test data.
- Run tests and validators before claiming completion.

## Workflow and priorities

1. Inspect first and test critical behavior before implementation.
2. Complete the rule baseline before model training.
3. Prioritize linking, assertion and type precision, then spans and laboratory coverage.
4. Change one primary variable per probing submission where possible.
5. Probe position only after every non-position prediction stabilizes.

Prefer primary sources, separate facts from inference, and keep experiments reproducible from config and commit.
