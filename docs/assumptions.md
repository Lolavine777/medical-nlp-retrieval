# Assumption Register

Every item below is unresolved unless marked confirmed.

## A1: ICD namespace and release

- Assumption: Diagnosis candidates use a form of ICD-10.
- Evidence: The handoff says ICD-10, but the saved official phase HTML does not name an ICD ontology.
- Confidence: Low.
- Risk if wrong: The linker could return valid identifiers from the wrong namespace.
- Default behavior: Do not emit diagnosis codes until an organizer-provided ontology or clarification is available.
- Falsification: Obtain the official code list or a named organizer example.

## A2: RxNorm namespace, release, subset, and term type

- Assumption: Drug candidates are RxCUIs and may target IN, SCDC, SCD, BN, or SBD according to mention specificity.
- Evidence: The handoff says RxNorm, while the official example provides opaque numeric identifiers.
- Confidence: Low.
- Risk if wrong: Drug normalization could target the wrong vocabulary, release, or semantic level.
- Default behavior: Keep parsed drug attributes separate and do not generalize beyond an approved snapshot.
- Falsification: Obtain the organizer ontology and target term-type clarification.

## A3: Complete type-dependent schema

- Assumption: `TÊN_XÉT_NGHIỆM`, `KẾT_QUẢ_XÉT_NGHIỆM`, and `CHẨN_ĐOÁN` have field sets not shown in the phase example.
- Evidence: Only `THUỐC` and `TRIỆU_CHỨNG` appear in the saved official output.
- Confidence: High that the schema is unknown.
- Risk if wrong: Extra or missing fields may invalidate JSON or alter scoring.
- Default behavior: Block full submission validation until official examples are obtained.
- Falsification: Obtain the full output specification or examples for all types.

## A4: Mention matching algorithm

- Assumption: Matching may use text and type, duplicate disambiguation, nearest position, tolerant search, overlap, or assignment.
- Evidence: The organizer said position helps locate a genuine concept but declined to disclose matching details.
- Confidence: Low for every specific behavior.
- Risk if wrong: The local evaluator could reward behavior that the official evaluator penalizes.
- Default behavior: Isolate matching and position policy behind provisional configuration.
- Falsification: Obtain evaluator details or run one-variable controlled submissions.

## A5: Position and end semantics

- Assumption: End-exclusive offsets are useful locally but may not be required exactly by the evaluator.
- Evidence: The example supports `end - start == len(text)` and reconstructed spans satisfy `raw_text[start:end] == text`, while website offset drift suggests a hidden serialization.
- Confidence: High for the local invariant and low for evaluator behavior.
- Risk if wrong: Offset conversion could reduce matching quality or corrupt duplicate handling.
- Default behavior: Preserve raw LF text and clean local offsets; keep alternate strategies disabled.
- Falsification: After all non-position predictions stabilize, compare raw offsets with simulated CRLF offsets.

## A6: History-of-present-illness sections are current

- Assumption: Current-illness headers do not imply `isHistorical` by section alone.
- Evidence: Clinical semantics support this interpretation, but no labeled competition example covers it.
- Confidence: Medium.
- Risk if wrong: Historical precision or recall will fall across common sections.
- Default behavior: Require a local temporal cue rather than the header alone.
- Falsification: Obtain labeled examples or run a frozen-span assertion ablation.

## A7: Family reporter is not family experiencer

- Assumption: A relative reporting the patient's condition does not set `isFamily`.
- Evidence: ConText distinguishes experiencer, but organizer policy is absent.
- Confidence: Medium.
- Risk if wrong: Family assertions will be systematically misclassified.
- Default behavior: Track reporter and experiencer separately.
- Falsification: Obtain official examples for both constructions.

## A8: Multi-code candidate frequency

- Assumption: Some mentions may have multiple ground-truth candidates because the metric accepts sets.
- Evidence: Jaccard is defined over sets, but the official example uses one code per drug.
- Confidence: Low.
- Risk if wrong: Top one may lose recall, while speculative extras reduce Jaccard.
- Default behavior: Return top one until calibrated evidence supports more codes.
- Falsification: Inspect labeled data or run a frozen-output cardinality sweep.

## A9: Combined model budget

- Assumption: None for the limit itself.
- Evidence: The organizer confirmed that total solution model parameters must not exceed 9B.
- Confidence: High.
- Risk if wrong: No current risk because conservative accounting is enforced.
- Default behavior: Count independent checkpoints separately, ignore quantization, and update the ledger before adding a model.
- Falsification: Replace only with a newer organizer clarification.

## A10: Auxiliary model accounting

- Assumption: Synthetic-data generators, distillation teachers, ontology-embedding models, and base plus LoRA parameters may count toward 9B.
- Evidence: The combined limit is confirmed, but these cases are not clarified.
- Confidence: Low for inclusion rules.
- Risk if wrong: A reproducible pipeline could exceed organizer accounting.
- Default behavior: Conservatively count every required model and checkpoint.
- Falsification: Obtain explicit organizer rulings for each category.

## A11: External data label transfer

- Assumption: Allowed public medical datasets can improve adaptation and span detection after explicit label mapping.
- Evidence: External data use is confirmed, but competition annotation policy remains separate.
- Confidence: Medium.
- Risk if wrong: Blind label merging creates systematic span and type errors.
- Default behavior: Complete `data/DATA_SOURCES.md` and validate mappings before training.
- Falsification: Compare mapped external-data training on a competition-aligned validation slice.

## A12: Submission quota scope

- Assumption: The quota may apply per member rather than per team.
- Evidence: This is an unconfirmed player observation.
- Confidence: Low.
- Risk if wrong: Submission scheduling could assume unavailable capacity.
- Default behavior: Plan under the conservative visible quota and never evade limits.
- Falsification: Monitor organizer clarification.
