# Session Report - 2026-07-11

## Expected outcome

This session was expected to connect the local repository to GitHub, incorporate the latest organizer constraints, continue the reproducible rule baseline, and leave a concise explanation of the problem, decisions, findings, unknowns, and next work.

## Delivered

- Configured `origin` as `https://github.com/Lolavine777/medical-nlp-retrieval.git` without fetching, pushing, or changing remote state.
- Committed competition policy, model-budget rules, external-data manifest, submission ledger, assumptions, and annotation policy in commit `862152c`.
- Implemented the immutable strict UTF-8 loader and casefold view with normalized-to-raw boundary mapping in commit `4dc1c44`.
- Implemented a deterministic section parser that preserves raw spans, supports numbered and inline headers, and retains unknown content as `unsectioned` in commit `4dc1c44`.
- Added nine loader and section tests, bringing the full suite to 18 passing tests.

## Problem being solved

The system must extract mention-level clinical entities from noisy Vietnamese and mixed-language records, classify their types, assign assertion flags, and link diagnoses and drugs to organizer-approved ontology identifiers.
The final score emphasizes candidate linking, while wrong types and speculative candidates can be expensive.
The private evaluator does not disclose mention matching or exact position behavior, so the system must generalize rather than fit public examples.

## Organizer-confirmed constraints

- The combined parameter count of every model in the solution must be at most 9B.
- Public Vietnamese medical NER and other external training data are allowed when licenses, provenance, reproducibility, redistribution, and label mappings are documented.
- Position is intended to help locate genuine concepts, but detailed matching behavior will not be disclosed.
- Final inference must remain offline and must not use external APIs.

## Main decisions

- Keep raw UTF-8 text, whitespace, and line endings immutable.
- Generate clean local offsets satisfying `raw_text[start:end] == text` without claiming exact evaluator semantics.
- Keep normalized text separate and map its boundaries back to raw indices.
- Do not convert LF offsets to simulated CRLF offsets except in a controlled one-variable submission after other predictions stabilize.
- Start with rules, lexical retrieval, ontology indices, and deterministic postprocessing.
- Add no model until a measured error category justifies it and the parameter ledger is updated.
- Treat external labels as source-specific and require explicit mappings into the five competition entity types.
- Use leaderboard submissions as hypothesis tests and record prediction diffs, score deltas, conclusions, confidence, and generalization risk.

## Verified implementation findings

- All 100 ZIP documents load with strict UTF-8 while preserving their original line endings.
- The mapped casefold view maps its full normalized span back to the full raw span, including expanding casefold characters.
- Section output covers every raw document continuously without dropping or overlapping characters.
- Known section families were detected in 99 of 100 documents.
- The parser produced 516 sections across the corpus.
- Unsectioned spans contain 2,985 of 132,336 characters, or 2.26 percent.
- The most frequent section kinds are past history at 155, current illness at 87, admission reason at 78, assessment at 74, and symptoms at 55.
- Only one explicit laboratory section was detected, which indicates that laboratory extraction must also inspect assessment and free-form lines rather than depend on section headers.

## Important unknowns

- The official ICD namespace, release, aliases, and code list remain unavailable.
- The official RxNorm release, subset, and target term type remain unavailable.
- Complete schemas for diagnosis and both laboratory entity types remain unverified.
- Mention matching and the exact role of position remain undisclosed.
- Auxiliary-model accounting for synthetic generation, distillation, ontology embeddings, and LoRA remains unclear.
- Submission quota scope remains unconfirmed.
- External dataset licenses and redistribution rights have not yet been verified or downloaded.

## What was intentionally not done

- No model was downloaded, trained, or added, so the parameter budget remains 0 of 9B.
- No external dataset was downloaded before license review.
- No ICD or RxNorm code was generated without an approved ontology snapshot.
- No leaderboard submission was made.
- No code or commit was pushed to the remote repository.

## Next checkpoints

1. Add deterministic line roles using the section spans and corpus audit.
2. Implement drug-regimen and laboratory name/result parsers with exact raw spans.
3. Implement clause-scoped negation, history, and family rules.
4. Resolve the full type-dependent output schema before full serializer validation.
5. Acquire organizer-approved ICD and RxNorm snapshots before candidate linking.
6. Implement a provisional evaluator with matching assumptions isolated in configuration.
7. Generate an end-to-end validated sample output before any model work.

## Session evidence

- Full test command: `.\.venv\Scripts\python.exe -m unittest discover -s tests -v`.
- Result before the implementation commit: 18 tests passed with zero failures.
- Knowledge commit: `862152c`.
- Loader and section commit: `4dc1c44`.
- Remote: `origin` points to `https://github.com/Lolavine777/medical-nlp-retrieval.git`.
