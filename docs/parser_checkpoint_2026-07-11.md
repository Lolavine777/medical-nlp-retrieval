# Parser checkpoint - 2026-07-11

## Verified evidence

- Source: `input.zip`, SHA-256 `46fe4a578b2c4478faa7c570b218218f539c0bbf1ea409168ae67a14ad86ca35`, accessed 2026-07-11.
- Evidence: Code processed all 100 UTF-8 documents and validated every emitted drug, laboratory-name, and laboratory-result slice against the original raw text.
- Result: The conservative candidate parser emitted 82 drug spans from 35 documents and 51 laboratory name-result pairs from 18 documents, with zero local offset mismatches.
- Evidence: The drug regression fixture reproduces all 11 official drug texts and end-exclusive raw spans.
- Confidence: High for offset integrity and the stated counts, because both are deterministic code results on the pinned artifact.
- Strategic impact: These are candidate-extraction statistics, not estimates of evaluator precision or recall.

## Implemented policy

- Section and line roles preserve exact raw boundaries and recognize only explicitly observed heading variants.
- Drug extraction accepts explicit medication-section items and high-signal list regimens outside those sections.
- Laboratory extraction requires a known laboratory surface plus a numeric or qualitative value, with extra context required outside laboratory sections.
- Numeric laboratory values take precedence over direction words such as `tăng` or `giảm`.
- No ICD or RxNorm identifier is emitted, and the active model parameter budget remains `0 / 9B`.

## Known limits

- Drug spans are retrieval inputs, not final `THUỐC` entities, because generic therapies and malformed translated lines cannot be resolved safely without an approved ontology index.
- The laboratory lexicon is intentionally incomplete and currently returns one value per detected name occurrence.
- Trend expressions such as `tăng từ 5.2 lên 6.3` currently select the first numeric value, while the evaluator's preferred result span is hidden.
- Section contents can contain mislabeled or noisy list items, so ontology linking must act as a precision gate rather than inventing codes.
- Confidence: High that these limitations exist, but unknown regarding their leaderboard impact until a controlled submission is possible.

## Next checkpoint

Implement scoped assertion rules for negation, history, temporality, and experiencer, then connect the current parsers to the type-dependent serializer and validator.
