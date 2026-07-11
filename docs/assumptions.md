# Assumption Register

Every item below is unresolved unless marked confirmed.

## A1: ICD namespace and release

- Assumption: Diagnosis candidates use a form of ICD-10.
- Evidence: The handoff says ICD-10, but the saved official phase HTML does not name an ICD ontology.
- Confidence: Low.
- Risk if wrong: The linker could return syntactically valid identifiers from the wrong namespace and receive zero candidate credit.
- Default behavior: Do not emit diagnosis codes until an organizer-provided ontology or clarification is available.
- Falsification: Obtain the official code list, forum clarification, or an unambiguous organizer example with a named edition.

## A2: RxNorm namespace, release, and subset

- Assumption: Drug candidate identifiers are RxCUIs from RxNorm.
- Evidence: The handoff says RxNorm, while the official example provides numeric identifiers without naming the ontology.
- Confidence: Low.
- Risk if wrong: Drug normalization could target the wrong vocabulary or release.
- Default behavior: Treat official example identifiers as opaque and do not generalize beyond an approved snapshot.
- Falsification: Resolve the example identifiers against the organizer-provided drug ontology or obtain an official clarification.

## A3: RxNorm target term type

- Assumption: Ground truth may select IN, SCDC, SCD, BN, or SBD according to mention specificity.
- Evidence: NLM defines all these granularities, but the organizer has not named one.
- Confidence: Low.
- Risk if wrong: Correct drugs could be linked at the wrong semantic level.
- Default behavior: Keep parsed drug attributes separate and postpone target selection.
- Falsification: Inspect a labeled organizer ontology or run a controlled term-type leaderboard ablation after the snapshot is known.

## A4: Complete type-dependent schema

- Assumption: `TÊN_XÉT_NGHIỆM`, `KẾT_QUẢ_XÉT_NGHIỆM`, and `CHẨN_ĐOÁN` have specific field sets not shown in the phase example.
- Evidence: Only `THUỐC` and `TRIỆU_CHỨNG` appear in the saved official output.
- Confidence: High that the schema is unknown.
- Risk if wrong: Extra or missing fields may invalidate JSON or alter scoring.
- Default behavior: Implement serializers only for observed types and block full submission validation until official examples are obtained.
- Falsification: Obtain the full output specification or examples for all types.

## A5: Mention matching algorithm

- Assumption: The evaluator matches mentions using some combination of text, type, and possibly position.
- Evidence: The metric explanation describes samples and candidates but does not publish matching code.
- Confidence: Low.
- Risk if wrong: The local evaluator could reward a system behavior that the official evaluator penalizes.
- Default behavior: Isolate matching behind a provisional evaluator configuration.
- Falsification: Obtain evaluator code or design controlled submissions that vary only positions or duplicate mentions.

## A6: Position participation in score

- Assumption: Position is at least validated and may participate in mention matching.
- Evidence: Every example entity has a position, but the score formula does not mention it directly.
- Confidence: Medium for validation and low for scoring.
- Risk if wrong: Offset bugs could either invalidate submissions or create mismatched mentions.
- Default behavior: Always enforce exact end-exclusive offsets regardless of scoring.
- Falsification: Obtain official validation rules or a direct organizer clarification.

## A7: History-of-present-illness sections are current

- Assumption: `Tiền sử bệnh hiện tại`, `Bệnh sử hiện tại`, and `Lịch sử bệnh hiện tại` do not imply `isHistorical` by section alone.
- Evidence: Clinical semantics support this interpretation, but no labeled competition example covers it.
- Confidence: Medium.
- Risk if wrong: Historical precision or recall will fall across common sections.
- Default behavior: Require a local temporal cue instead of assigning historical status from these headers.
- Falsification: Obtain labeled entities from these sections or run a frozen-span assertion ablation.

## A8: Family reporter is not family experiencer

- Assumption: A relative reporting the patient's condition does not set `isFamily`.
- Evidence: ConText distinguishes experiencer, and clinical meaning supports the distinction, but organizer policy is absent.
- Confidence: Medium.
- Risk if wrong: Family assertions will be systematically overpredicted or underpredicted.
- Default behavior: Track reporter and experiencer separately and serialize only family experiencer.
- Falsification: Obtain official examples covering both constructions.

## A9: Multi-code candidate frequency

- Assumption: Some mentions may have multiple ground-truth candidates because the metric accepts sets.
- Evidence: Jaccard is defined over candidate sets, but the official example uses one code for every drug.
- Confidence: Low.
- Risk if wrong: Always returning top one may lose recall, while speculative extras reduce Jaccard.
- Default behavior: Return top one until calibrated evidence supports additional codes.
- Falsification: Inspect labeled development data or run a candidate-cardinality sweep with all other outputs frozen.

## A10: Combined model budget

- Assumption: None.
- Evidence: The organizer has confirmed that the total parameter count across all models must not exceed 9B.
- Confidence: High.
- Risk if wrong: No current risk because the stricter combined accounting is enforced.
- Default behavior: Record each model, shared weights, standalone parameters, and running total before it enters any pipeline.
- Falsification: Replace only with a newer organizer clarification.

## A11: Submission quota scope

- Assumption: The quota may apply per team member rather than per team.
- Evidence: This is an unconfirmed observation only.
- Confidence: Low.
- Risk if wrong: Submission scheduling could be based on unavailable capacity.
- Default behavior: Plan experiments under the visible conservative quota and do not alter architecture.
- Falsification: Monitor organizer forum or obtain a direct clarification.
