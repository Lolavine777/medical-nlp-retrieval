# Assumption Register

The organizer has declared ontology, recognition, span, candidate, and position policies hidden challenge variables.
Resolve them through controlled experiments, not expected clarification.

## A1: ICD target

- Assumption: The evaluator uses an unknown ICD namespace, version, alias set, and candidate policy.
- Confidence: Low for any specific target.
- Default: Index legally usable references with provenance and keep namespace policy configurable.
- Test: Change only ICD source or candidate policy in controlled submissions.

## A2: RxNorm target

- Assumption: Evaluator targets may include active, historical, ingredient, clinical, branded, combination, or component RXCUIs.
- Evidence: Official examples appear to include obsolete or inconsistent current mappings.
- Confidence: Medium that active-only retrieval is unsafe and low for the exact target policy.
- Default: Ingest active and historical concepts plus replacement relationships and never auto-replace a retired code.
- Test: Isolate status, term type, and combination policy one variable at a time.

## A3: Hidden schemas and spans

- Assumption: Diagnosis and laboratory schemas plus entity boundaries follow undisclosed annotation policy.
- Confidence: High that policy is hidden and low for each hypothesis.
- Default: Keep type-specific schema and core versus modifier-inclusive span strategies configurable.
- Test: Freeze other outputs and compare one schema or boundary policy at a time.

## A4: Mention and position matching

- Assumption: Matching may use text, type, duplicate assignment, nearest position, tolerant search, or overlap.
- Confidence: Low for each mechanism.
- Default: Preserve clean raw offsets and keep alternate strategies disabled.
- Test: Compare raw LF with one alternative position strategy only after other predictions stabilize.

## A5: Current illness and assertions

- Assumption: Current-illness headers do not imply `isHistorical`, and family reporter differs from family experiencer.
- Confidence: Medium.
- Default: Use local cues and clause scope over section-only decisions.
- Test: Frozen-span assertion ablations.

## A6: Candidate cardinality

- Assumption: Some mentions may have multiple ground-truth candidates.
- Confidence: Low.
- Default: Return top one until calibrated Jaccard evidence supports more.
- Test: Top-one versus thresholded or top-two sets with all else frozen.

## A7: Combined model budget

- Confirmed: Total solution model parameters must not exceed 9B.
- Default: Count independent checkpoints separately and ignore quantization reductions.
- Unknown: Accounting for generators, teachers, ontology embedders, LoRA, and merged checkpoints.

## A8: External data transfer

- Confirmed: Licensed public external training data is allowed.
- Assumption: Explicitly mapped data improves adaptation or span detection.
- Default: Complete the data manifest and validate label mappings before training.

## A9: Submission quota

- Assumption: The daily quota may apply per member.
- Confidence: Low.
- Default: Plan conservatively and never evade limits.
