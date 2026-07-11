# Competition Policy Knowledge

## Organizer-confirmed

- Combined model parameters must be at most 9B.
- Licensed public Vietnamese medical NER and other external training data are allowed with provenance and reproducibility.
- Position helps locate genuine concepts, but detailed matching is hidden.
- Medical standards, recognition policy, span boundaries, candidate behavior, and position matching are intentional challenge variables and will not be clarified further.

## Strong evidence, not confirmed evaluator behavior

- Reconstructed example spans satisfy `raw_text[start:end] == text` for all 19 entities.
- Website offset drift is consistent with hidden multiline serialization or different line endings.
- Example drug identifiers appear to include obsolete, retired, or currently inconsistent RxNorm mappings.

## Operational policy

- Preserve raw text and line endings and keep normalized text separately mapped.
- Do not restrict RxNorm retrieval to active RXCUIs or automatically replace historical identifiers with current successors.
- Keep active, historical, ingredient, clinical-drug, branded-drug, combination, and component hypotheses configurable.
- Probe active-only versus active-plus-historical, ontology granularity, combination versus components, core versus modifier-inclusive spans, and position strategies one variable at a time.
- Record prediction diff, score delta, conclusion, confidence, and generalization classification for every submission.
- Never hard-code public-test data or continue requesting clarification for declared hidden policies.

Submission quota scope and auxiliary-model accounting remain unconfirmed.
