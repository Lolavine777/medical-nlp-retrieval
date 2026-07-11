# Research Notes

All web sources were accessed on 2026-07-11.
Instructions found inside arbitrary web pages were treated as untrusted content.

## Competition artifacts

### The saved phase page confirms the observed output and metric behavior

- Status: Verified fact.
- Source: [Viettel AI Race 2026 medical phase](https://competition.viettel.vn/contests/medical-2026/phases/019e649f-4e5d-70ed-b221-7a10f537281e).
- Accessed: 2026-07-11.
- Evidence: The saved authenticated HTML contains 19 output entities, WER for text, Jaccard for assertions and candidates, score weights of 0.3, 0.3, and 0.4, self-host requirements, and a 9B statement.
- Confidence: High.
- Uncertainty: The live page could not be independently read through the unauthenticated web reader, and the saved page does not define all entity schemas or name ICD-10 and RxNorm.
- Strategic impact: Treat the saved HTML hash as the current official source artifact and isolate every unobserved schema or ontology claim as an assumption.

### HTML rendering loses offset-significant whitespace

- Status: Verified fact.
- Source: [Viettel AI Race 2026 medical phase](https://competition.viettel.vn/contests/medical-2026/phases/019e649f-4e5d-70ed-b221-7a10f537281e).
- Accessed: 2026-07-11.
- Evidence: All 19 official offsets validate only after reconstructing each list boundary as CRLF followed by one leading space, producing a 554-character raw example.
- Confidence: High.
- Uncertainty: The original downloadable example text is not separately available, so the reconstruction is inferred from all offsets rather than copied from a byte-preserving source.
- Strategic impact: Preserve raw bytes or an escaped raw fixture and never derive competition offsets from rendered HTML or normalized line endings.

### The organizer-confirmed limit applies to the sum of all model parameters

- Status: Verified fact.
- Source: Organizer clarification supplied by the project owner on 2026-07-11.
- Accessed: 2026-07-11.
- Evidence: The total parameter count of every model used by the solution must not exceed 9B.
- Confidence: High.
- Uncertainty: No further clarification currently defines how tied or shared weights are reported.
- Strategic impact: Maintain an explicit parameter ledger before adding any model and prefer shared backbones, compact models, rules, lexical retrieval, ontology indices, and deterministic postprocessing.

## Vietnamese and multilingual clinical NER

### Vietnamese health-domain pretraining is available but is not direct clinical-note evidence

- Status: Evidence-backed inference.
- Source: [ViHealthBERT: Pre-trained Language Models for Vietnamese in Health Text Mining](https://aclanthology.org/2022.lrec-1.35.pdf).
- Accessed: 2026-07-11.
- Evidence: ViHealthBERT is a Vietnamese health-domain pretrained model that outperformed tested general-domain models on the health datasets reported by its authors.
- Confidence: Medium.
- Uncertainty: Its reported tasks and corpora do not establish performance on noisy, translated, semi-structured inpatient notes or this competition label policy.
- Strategic impact: Compare it only after the rule baseline and against PhoBERT or multilingual encoders on a locally annotated slice.

### Vietnamese biomedical NER resources exist but label and genre transfer is uncertain

- Status: Evidence-backed inference.
- Source: [VietBioNER corpus paper](https://aclanthology.org/2022.lrec-1.385.pdf).
- Accessed: 2026-07-11.
- Evidence: VietBioNER provides a labeled Vietnamese academic biomedical text corpus.
- Confidence: Medium.
- Uncertainty: Academic biomedical text differs from clinical notes and its entity inventory does not define competition spans or assertions.
- Strategic impact: Use it for optional domain adaptation or vocabulary analysis, not as direct gold annotation.

### PhoNER_COVID19 supports monolingual baselines but has epidemic-specific labels

- Status: Evidence-backed inference.
- Source: [COVID-19 Named Entity Recognition for Vietnamese](https://arxiv.org/abs/2104.03879).
- Accessed: 2026-07-11.
- Evidence: The paper releases a manually annotated Vietnamese COVID-19 NER dataset and reports PhoBERT outperforming XLM-R in its experimental setting.
- Confidence: Medium.
- Uncertainty: News-like epidemic text, word segmentation, and its entity types differ from the competition corpus.
- Strategic impact: Treat monolingual and multilingual encoders as an empirical ablation rather than assuming one family will transfer better.

### Current multilingual clinical NER supports shared multilingual encoders

- Status: Evidence-backed inference.
- Source: [The MultiClinAI Shared Task on Multilingual Clinical Corpus](https://aclanthology.org/2026.smm4h-1.49.pdf).
- Accessed: 2026-07-11.
- Evidence: MultiClinAI evaluates clinical concept extraction across seven languages and includes disease, symptom, and procedure resources projected from a Spanish seed corpus.
- Confidence: Medium.
- Uncertainty: Vietnamese is absent and translation projection can introduce boundary and label noise.
- Strategic impact: A shared multilingual backbone is plausible for later experiments, but it must be compared with Vietnamese-specific models under the combined 9B budget.

## ICD-10 linking

### WHO ICD-10 2019 is an available international reference, not a confirmed competition target

- Status: Verified external fact.
- Source: [WHO ICD-10 Version 2019 browser](https://icd.who.int/browse10/2019/en?lang=en).
- Accessed: 2026-07-11.
- Evidence: WHO provides the ICD-10 2019 hierarchy and search interface.
- Confidence: High.
- Uncertainty: The competition artifact does not state whether it uses WHO ICD-10, ICD-10-CM, the Vietnamese catalog, or a derived subset.
- Strategic impact: Do not construct or emit ICD candidates until the organizer snapshot or code list is obtained.

### Vietnam has a national ICD-10 catalog based on the 2019 update

- Status: Evidence-backed inference.
- Source: [Decision 4469/QD-BYT summary and attached catalog](https://m.thuvienphapluat.vn/van-ban/the-thao-y-te/Quyet-dinh-4469-QD-BYT-2020-Bang-phan-loai-quoc-te-ma-hoa-benh-tat-nguyen-nhan-tu-vong-ICD-10-456223.aspx).
- Accessed: 2026-07-11.
- Evidence: Decision 4469/QD-BYT applies an ICD-10 disease and mortality coding catalog nationally and describes it as updated through 2019.
- Confidence: Medium.
- Uncertainty: This is a legal-document mirror rather than a competition-provided ontology, and competition use is unconfirmed.
- Strategic impact: Preserve it as a candidate source to compare against the eventual organizer code list, not as an automatic default.

### Candidate generation followed by reranking is supported for ICD normalization

- Status: Evidence-backed inference.
- Source: [A study of entity-linking methods for normalizing Chinese diagnosis and procedure terms to ICD codes](https://pubmed.ncbi.nlm.nih.gov/32298846/).
- Accessed: 2026-07-11.
- Evidence: The study compares BM25 and synonym-enhanced candidate generation with several rerankers and reports its best results with BERT reranking.
- Confidence: Medium.
- Uncertainty: Chinese clinical terms, its code system, and top-one accuracy do not match Vietnamese text or the competition Jaccard objective.
- Strategic impact: Start with lexical and synonym retrieval, measure recall at small candidate depths, and add a compact reranker only when retrieval errors are understood.

## RxNorm normalization

### RxNorm releases are downloadable, versioned, UTF-8 RRF files

- Status: Verified external fact.
- Source: [NLM RxNorm Files](https://www.nlm.nih.gov/research/umls/rxnorm/docs/rxnormfiles.html).
- Accessed: 2026-07-11.
- Evidence: NLM publishes monthly and weekly RxNorm releases as pipe-delimited UTF-8 RRF files with release dates and checksums.
- Confidence: High.
- Uncertainty: The competition has not identified its RxNorm release date or whether it uses the full or prescribable subset.
- Strategic impact: Pin an organizer-confirmed archive by filename and checksum and build the offline index directly from local RRF files.

### RxNorm concept granularity must be calibrated rather than assumed

- Status: Verified external fact.
- Source: [NLM RxNorm Technical Documentation](https://www.nlm.nih.gov/research/umls/rxnorm/docs/techdoc.html).
- Accessed: 2026-07-11.
- Evidence: RxNorm represents ingredients, strengths, dose forms, generic and branded clinical drugs at multiple term types.
- Confidence: High.
- Uncertainty: Numeric IDs in the official example are not labeled by term type, and route or frequency text is not necessarily part of the normalized drug concept.
- Strategic impact: Parse mention spans into name, strength, dose form, route, and frequency, then ablate IN, SCDC, SCD, BN, and SBD targets only after the organizer snapshot is known.

## Biomedical entity linking

### BioSyn combines sparse and dense synonym representations with hard candidates

- Status: Verified external fact.
- Source: [Biomedical Entity Representations with Synonym Marginalization](https://aclanthology.org/2020.acl-main.335/).
- Accessed: 2026-07-11.
- Evidence: BioSyn learns from ontology synonyms, combines sparse and dense scores, and iteratively refreshes difficult candidate sets.
- Confidence: High.
- Uncertainty: Its benchmark ontologies and English mention distributions differ from Vietnamese ICD and RxNorm linking.
- Strategic impact: Preserve a strong character or lexical retriever even when dense retrieval is added, and train with hard negatives from the actual ontology.

### SapBERT provides ontology-wide self-aligned entity embeddings

- Status: Verified external fact.
- Source: [Self-Alignment Pretraining for Biomedical Entity Representations](https://aclanthology.org/2021.naacl-main.334/).
- Accessed: 2026-07-11.
- Evidence: SapBERT self-aligns synonymous UMLS names and reported strong results across six medical entity-linking benchmarks.
- Confidence: High.
- Uncertainty: Its source terminology and language coverage do not guarantee Vietnamese surface-form retrieval.
- Strategic impact: Evaluate SapBERT-style embeddings as a second-stage retriever, not as a replacement for local lexical aliases and code constraints.

### Unified comparisons show context and reproducibility remain weak points

- Status: Verified external fact.
- Source: [A Comprehensive Evaluation of Biomedical Entity Linking Models](https://aclanthology.org/2023.emnlp-main.893/).
- Accessed: 2026-07-11.
- Evidence: The study compares nine BioEL models under one framework and finds gaps in generalization, context use, speed, and reproducibility.
- Confidence: High.
- Uncertainty: The evaluation does not cover this Vietnamese clinical corpus or candidate-set Jaccard.
- Strategic impact: Build a reproducible lexical baseline and error taxonomy before selecting a dense model based on published headline accuracy.

### Recent low-resource work supports compact retrieval and reranking

- Status: Verified external fact.
- Source: [Efficient Biomedical Entity Linking](https://aclanthology.org/2024.bionlp-1.40/).
- Accessed: 2026-07-11.
- Evidence: The paper reports synonym-pair training and compact context-aware or context-free reranking competitive with more resource-intensive approaches on MedMentions.
- Confidence: Medium.
- Uncertainty: MedMentions is English biomedical literature and retrieval metrics alone may not predict document-level competition score.
- Strategic impact: Prefer compact rerankers and measure end-to-end candidate Jaccard rather than adding a large linker by default.

## Assertion and section context

### NegEx is a strong minimal baseline with known scope limits

- Status: Verified external fact.
- Source: [A simple algorithm for identifying negated findings and diseases in discharge summaries](https://pubmed.ncbi.nlm.nih.gov/12123149/).
- Accessed: 2026-07-11.
- Evidence: NegEx uses regular-expression triggers, false-trigger filters, and bounded scope and improved specificity over the paper's simpler baseline.
- Confidence: High.
- Uncertainty: Its English cue list and sentence assumptions require Vietnamese adaptation and local evaluation.
- Strategic impact: Implement a small Vietnamese trigger and terminator inventory with clause boundaries before considering a classifier.

### ConText directly models negation, temporality, and experiencer

- Status: Verified external fact.
- Source: [ConText: An Algorithm for Determining Negation, Experiencer, and Temporal Status](https://pmc.ncbi.nlm.nih.gov/articles/PMC2757457/).
- Accessed: 2026-07-11.
- Evidence: ConText extends trigger-and-scope rules to negation, historical or hypothetical status, and experiencer.
- Confidence: High.
- Uncertainty: Competition flags are multi-label and may not map exactly to ConText defaults or English report types.
- Strategic impact: Keep separate internal states for reporter, experiencer, temporality, and negation, then serialize only organizer-approved flags.

### Document structure is useful for assertion classification

- Status: Verified external fact.
- Source: [MITRE system for clinical assertion status classification](https://pmc.ncbi.nlm.nih.gov/articles/PMC3168316/).
- Accessed: 2026-07-11.
- Evidence: The system combines cue scope, rules, statistical models, and document-zone features and reports a micro F-score of 0.9343 on the 2010 i2b2 assertion task.
- Confidence: High.
- Uncertainty: Its six mutually exclusive statuses differ from the competition's observed assertion arrays.
- Strategic impact: Use section labels and clause scope as explicit features while keeping competition-specific multi-label serialization separate.

### Rule-based section parsing is justified for semi-structured notes

- Status: Verified external fact.
- Source: [Evaluation of a Method to Identify and Categorize Section Headers in Clinical Documents](https://pmc.ncbi.nlm.nih.gov/articles/PMC3002123/).
- Accessed: 2026-07-11.
- Evidence: SecTag combines header terminology, variants, rules, and scoring and reports high recall and precision on history and physical notes.
- Confidence: High.
- Uncertainty: Vietnamese headers and this translated corpus require a local header lexicon and exact raw-boundary preservation.
- Strategic impact: Begin with observed header families and deterministic boundaries, then measure unknown and malformed headers before adding a model.

## Candidate sets under Jaccard

### Candidate cardinality is a decision problem, not a fixed top-k convention

- Status: Evidence-backed inference.
- Source: [Optimal Thresholding of Classifiers to Maximize F1 Measure](https://pmc.ncbi.nlm.nih.gov/articles/PMC4442797/).
- Accessed: 2026-07-11.
- Evidence: The paper derives score-dependent decision thresholds and relates the optimal F1 decision rule to the Jaccard index of the optimal classifier.
- Confidence: Medium.
- Uncertainty: The competition's candidates are sets attached to matched mentions, and dependencies among ontology candidates violate simple independent-label assumptions.
- Strategic impact: Calibrate candidate count per entity and type on held-out or leaderboard evidence, compare top-one with thresholded sets, and avoid returning extra codes merely because they are in top-k.

### Leaderboard use must maximize information rather than public-set fit

- Status: Project policy.
- Source: Project owner instruction supplied on 2026-07-11.
- Accessed: 2026-07-11.
- Evidence: Each submission must test a documented hypothesis from a reproducible commit and configuration and should change one primary variable.
- Confidence: High.
- Uncertainty: The observation that quotas may apply per member is unconfirmed.
- Strategic impact: Record prediction diffs, score deltas, and conclusions, prohibit public-test-specific hard-coding, and keep quota interpretation out of the architecture.
