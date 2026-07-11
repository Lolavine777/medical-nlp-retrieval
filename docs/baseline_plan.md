# End-to-End Rule Baseline Checkpoint Plan

## Goal and gate

Build a reproducible offline baseline that generates valid output for all 100 documents before any large-model work begins.
No checkpoint may normalize raw text in place, deduplicate mention occurrences, invent codes, or add unapproved output fields.

The combined parameter count of all models is capped at 9B by confirmed organizer clarification.
The current ledger in `configs/model_budget.json` is 0 parameters.
Any future model proposal must record its unique parameter count, shared weights, and new running total before implementation.

## Architecture

```text
immutable raw document
  -> offset-safe loader and optional mapped normalized view
  -> section parser and line roles
  -> rule drug, laboratory, symptom, and diagnosis extraction
  -> clause and section scoped assertions
  -> approved local ontology retrieval
  -> deterministic constraints and overlap handling
  -> type-dependent serializer and validator
  -> provisional local evaluator
  -> output/1.json through output/100.json and output.zip
```

Rules, lexical retrieval, ontology indices, and deterministic postprocessing are the default.
Shared compact backbones are considered only after baseline error analysis demonstrates a specific gap.

## Checkpoint 0: Freeze evidence

- Inputs: `input.zip`, saved official HTML, `outputs/source_audit.json`, research notes, assumptions, annotation policy, and the official fixture.
- Outputs: Recorded SHA-256 hashes, current source-audit report, and a reviewed list of blockers.
- Acceptance command: Run `tools/audit_sources.py`, all tests, and JSON parsing from the repository README.
- Expected evidence: The two source hashes remain unchanged, 100 documents are present, and all 19 official offsets validate.
- Stop condition: Stop if either canonical artifact hash changes or any official fixture span fails.

## Checkpoint 1: Offset-safe loader

- Inputs: One ZIP entry as strict UTF-8 bytes.
- Outputs: Immutable raw text plus an optional normalized view carrying normalized-index to raw-index mappings.
- Acceptance command: Run focused loader tests covering LF, CRLF, combining characters, repeated text, and malformed UTF-8.
- Expected evidence: Every recovered span satisfies `raw_text[start:end] == text`.
- Stop condition: Stop if normalization cannot map every emitted character boundary back to raw text.

## Checkpoint 2: Section parser and line roles

- Inputs: Raw text and the observed header-frequency inventory from the source audit.
- Outputs: Ordered section spans and line roles without modifying raw offsets.
- Acceptance command: Run tests covering numbered headers, whitespace variants, malformed headers, and section boundaries.
- Expected evidence: Common headers such as `Đánh giá tại bệnh viện`, current illness, past history, symptoms, medications, and tests have stable raw spans.
- Stop condition: Stop model expansion if unknown-header analysis has not been recorded on all 100 files.

## Checkpoint 3: Drug and laboratory extraction

- Inputs: Raw lines, sections, and line roles.
- Outputs: Drug-regimen mention spans and paired laboratory name/result spans.
- Acceptance command: Run focused parsers against raw fixtures with strengths, ranges, routes, frequencies, PRN markers, decimal commas, units, and multiple results per line.
- Expected evidence: Drug spans exclude following indications when separable and laboratory outputs retain exact source text.
- Stop condition: Stop if a parser constructs output text instead of slicing it from raw input.

## Checkpoint 4: Symptom, diagnosis, and assertion rules

- Inputs: Candidate spans, clause boundaries, section labels, and versioned cue lists.
- Outputs: Conservative entity types plus `isNegated`, `isHistorical`, and `isFamily` where supported.
- Acceptance command: Run tests for contrast clauses, pseudo-negation, current illness versus past history, family reporter, and family experiencer.
- Expected evidence: `Không buồn nôn nhưng đau bụng tăng` negates only the first clause, and reporter versus experiencer stays distinct internally.
- Stop condition: Stop if a section prior overrides an explicit local cue without a documented rule.

## Checkpoint 5: Approved ontology ingestion and lexical retrieval

- Inputs: Organizer-confirmed ICD and RxNorm files with version, license, checksum, and acquisition date.
- Outputs: Deterministic local alias tables, character or token retrieval indices, and candidate provenance.
- Acceptance command: Validate every indexed code against the pinned snapshot and measure retrieval recall at depths 1, 2, 4, 8, 16, and 32 on any labeled examples.
- Expected evidence: No candidate exists outside the approved ontology and exact or normalized aliases are reproducible.
- Stop condition: This checkpoint is blocked until the ontology snapshots and target namespaces are verified.

## Checkpoint 6: Type-dependent serializer and validator

- Inputs: Raw text and internal entity records.
- Outputs: JSON containing only fields approved for each type.
- Acceptance command: Validate JSON type, required and forbidden fields, offset equality, candidate provenance, duplicate preservation, filename sequence, and UTF-8 encoding.
- Expected evidence: The official `THUỐC` and `TRIỆU_CHỨNG` examples serialize exactly under the observed schemas.
- Stop condition: Full submission generation remains blocked until schemas for diagnosis and both laboratory types are confirmed.

## Checkpoint 7: Provisional local evaluator

- Inputs: Labeled fixtures and prediction JSON.
- Outputs: Text, assertion, candidate, and weighted total metrics plus per-mention diagnostics.
- Acceptance command: Test empty sets, wrong types, duplicate mentions, candidate weighting, and known hand-calculated examples.
- Expected evidence: WER and Jaccard formulas reproduce official published examples where defined.
- Stop condition: Keep mention matching and the role of position behind explicit provisional configuration until evaluator code or organizer clarification exists.

## Checkpoint 8: One-command end-to-end baseline

- Inputs: `input.zip`, pinned configuration, and approved ontology snapshots.
- Outputs: `output/1.json` through `output/100.json`, validation report, semantic prediction summary, and `output.zip`.
- Acceptance command: Run one inference command followed by full tests, raw-offset validation, JSON validation, and ZIP membership validation.
- Expected evidence: A clean environment reproduces byte-identical outputs from the same commit, configuration, artifacts, and ontology hashes.
- Stop condition: Do not submit if any output file fails validation or if reproduction metadata is missing.

## Checkpoint 9: Baseline error analysis

- Inputs: End-to-end outputs, local metrics where available, and validator reports.
- Outputs: Error buckets for span, type, assertion, section, drug parsing, laboratory parsing, ICD retrieval, and RxNorm retrieval.
- Acceptance command: Review a stratified sample and record counts, examples, and the next falsifiable hypothesis.
- Expected evidence: Every proposed model addresses a measured error category and declares its parameter-budget impact.
- Stop condition: Do not train a model solely because it is popular or published as state of the art.

## High-information leaderboard experiments

Each experiment must use the template in `docs/experiments.md` and change one primary variable where possible.

### Experiment 1: Candidate cardinality

- Hypothesis: Conservative top-one candidates outperform fixed top-k sets under candidate Jaccard.
- Frozen variables: Spans, types, assertions, ontology, and retrieval scores.
- Variants: Top one, calibrated threshold, and at most one small fixed-k control.
- Information gained: Whether multi-code recall is worth the false-positive Jaccard cost.

### Experiment 2: RxNorm target granularity

- Hypothesis: The organizer labels a consistent RxNorm term-type granularity conditional on mention specificity.
- Frozen variables: Drug spans, assertions, retrieval implementation, and all non-drug outputs.
- Variants: IN, SCDC, SCD, BN, and SBD after the official snapshot is confirmed.
- Information gained: The target semantic level and whether strength and dose form affect labels.

### Experiment 3: ICD namespace and version

- Hypothesis: Organizer labels align with either WHO ICD-10 2019 or the Vietnamese 4469 catalog where the two differ.
- Frozen variables: Diagnosis spans, types, assertions, and lexical ranking.
- Variants: Only codes that disambiguate the candidate namespaces and are valid in their pinned sources.
- Information gained: Which local ontology should become canonical.

### Experiment 4: Assertion components

- Hypothesis: Conservative negation rules add value while historical or family priors may overpredict.
- Frozen variables: Spans, types, and candidates.
- Variants: Negation only, negation plus historical, and negation plus historical plus family.
- Information gained: Marginal score contribution and error direction for each flag family.

### Experiment 5: Current-illness section prior

- Hypothesis: Treating history-of-present-illness as current improves assertion precision.
- Frozen variables: All entity spans and non-historical assertions.
- Variants: Current default versus historical-by-header control.
- Information gained: Organizer interpretation of translated current-illness headers.

### Experiment 6: Type precision threshold

- Hypothesis: Higher type-specific confidence thresholds improve total score because wrong types create both a missing and an extra concept.
- Frozen variables: Candidate and assertion logic for retained spans.
- Variants: One threshold per entity type around locally estimated precision-recall knees.
- Information gained: Whether precision or recall dominates for each entity type.

## Reproducibility record

Every experiment records the commit, complete configuration, artifact and ontology hashes, model-budget ledger, prediction diff, score before and after, score delta, conclusion, and next decision.
Negative and null results remain in the ledger.
