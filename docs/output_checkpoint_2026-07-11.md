# Output boundary checkpoint - 2026-07-11

## Verified evidence

- Source: The 19-entity official example preserved in `tests/fixtures/official_example.json`, derived from the saved authenticated competition HTML and accessed 2026-07-11.
- Evidence: The strict serializer validated all entities, emitted UTF-8 JSON, parsed the result again, and revalidated every type-dependent field and raw offset.
- Result: The serialized entity list contains 19 entities, occupies 2,113 UTF-8 bytes, and has SHA-256 `7dfe76f9f728ca1646e3f768f72460e18f9f567aec5ab20added626551258f93`.
- Evidence: Automated tests preserve repeated symptom mentions and reject missing or empty drug candidates, extra fields, unknown or duplicate list values, boolean or inclusive positions, unknown types, and non-list top-level values.
- Confidence: High for fixture round-trip, checksum, schema enforcement, and offset validation because each result is deterministic and executable.
- Strategic impact: Invalid final entities now fail before file generation instead of being silently repaired or dropped.

## Working schema policy

- `THUỐC` and `CHẨN_ĐOÁN` require `text`, `type`, `candidates`, `assertions`, and `position`.
- `TRIỆU_CHỨNG` requires `text`, `type`, `assertions`, and `position`.
- `TÊN_XÉT_NGHIỆM` and `KẾT_QUẢ_XÉT_NGHIỆM` default to `text`, `type`, and `position`.
- Laboratory schemas remain injectable through the same validator and serializer code path.
- Only `isNegated`, `isFamily`, and `isHistorical` are accepted assertion labels.
- Candidate identifiers must be unique non-empty strings, but ontology membership awaits a pinned local ontology index.
- The active model parameter budget remains `0 / 9B`.

## Known limits

- Diagnosis and laboratory field policies remain hidden evaluator variables rather than verified schema facts.
- This checkpoint validates one document's entity list and does not create filenames, directories, `output.zip`, or submission metadata.
- A valid empty entity list is allowed, but an incomplete entity is always rejected.
- The output checksum covers the preserved official fixture only and is not a leaderboard artifact.

## Next checkpoint

Implement deterministic multi-document file generation and packaging, then add the provisional local evaluator with matching assumptions isolated in configuration.
