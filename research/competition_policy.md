# Competition Policy Knowledge

## Organizer-confirmed

- Combined model parameters must be at most 9B.
- Public Vietnamese medical NER and other external training data are allowed, subject to license, provenance, reproducibility, and redistribution requirements.
- Position was designed to help locate a genuine concept, but detailed evaluator matching will not be disclosed.

## Strong evidence, not confirmed evaluator behavior

- The official example supports `end - start == len(text)` and reconstructed spans satisfy `raw_text[start:end] == text` for all 19 entities.
- Website offset drift grows by about two characters per numbered item, consistent with hidden multiline serialization or different line endings.
- Preserve raw UTF-8 text and original line endings, keep normalized text separate, and do not convert LF offsets to CRLF outside a controlled experiment.

## Unconfirmed

- Matching may use text and type, duplicate disambiguation, nearest position, tolerant search, overlap, or assignment.
- The five-submission daily quota may apply per member rather than per team.
- Auxiliary model accounting for generation, distillation, ontology embeddings, and LoRA remains unclear.

## Strategy

- Optimize for private-test generalization.
- Use each submission to test one documented hypothesis from a reproducible commit and configuration.
- Record prediction diff, score delta, conclusion, confidence, and `generalizable`, `public-specific-risk`, or `unknown` classification.
- Probe raw LF versus simulated CRLF positions only after all non-position predictions are identical.
- Never hard-code public-test files, text, positions, candidates, or entities.
