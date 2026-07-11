# Output Serializer and Validator Design

## Scope

Implement a strict final boundary for one document's entity list.
The component validates type-dependent schemas and raw offsets, then emits deterministic UTF-8 JSON.
It will not extract entities, invent candidates, repair invalid records, write directories, or package `output.zip`.
The active model parameter budget remains `0 / 9B`.

## Interface

`validate_entities(raw_text, entities, schemas=DEFAULT_SCHEMAS)` validates the complete list and returns no transformed data.
`serialize_entities(raw_text, entities, schemas=DEFAULT_SCHEMAS)` validates first and returns JSON with one trailing newline.

The schema mapping remains an explicit argument so hidden laboratory policies can be probed without forking the pipeline.
The default mapping is:

- `THUỐC`: `text`, `type`, `candidates`, `assertions`, and `position`.
- `CHẨN_ĐOÁN`: `text`, `type`, `candidates`, `assertions`, and `position`.
- `TRIỆU_CHỨNG`: `text`, `type`, `assertions`, and `position`.
- `TÊN_XÉT_NGHIỆM`: `text`, `type`, and `position`.
- `KẾT_QUẢ_XÉT_NGHIỆM`: `text`, `type`, and `position`.

The laboratory defaults are provisional policy, not verified evaluator behavior.

## Validation

The top level must be a list of entity mappings.
Each entity must contain exactly the required fields for its type and no additional field.
Unknown types are rejected.

`text` must be a non-empty string.
`position` must be a two-integer JSON list with an end-exclusive slice satisfying `raw_text[start:end] == text`.
Boolean values are not accepted as positions even though Python treats booleans as integers.

`assertions` must be a list containing unique values from `isNegated`, `isFamily`, and `isHistorical`.
`candidates` must be a non-empty list of unique non-empty strings.
Candidate membership in an ontology is deliberately outside this component and will be enforced after a pinned ontology index exists.

The validator rejects the entire document on the first invalid entity and includes the entity index in the error message.
It never drops, repairs, deduplicates, sorts, or supplements entities.

## Serialization

Entity order and duplicate mentions are preserved exactly.
Fields are emitted in the configured schema order for deterministic checksums.
JSON uses `ensure_ascii=False` and one trailing newline.
Raw text is used only for validation and is not included in the output entity list.

## Verification

Tests will verify that all 19 official example entities validate and round-trip without changing order or duplicate mentions.
Tests will reject a missing drug candidate, an extra field, an unknown assertion, a duplicate candidate, an inclusive offset, a boolean position, and an unknown entity type.
Tests will verify exact Unicode output and configurable laboratory fields.

The checkpoint will serialize the official fixture, parse the emitted JSON again, validate it a second time, and record the output checksum.

## Known uncertainty

Diagnosis and laboratory schemas remain hidden evaluator variables.
The defaults implement the approved working hypothesis and must change only through documented, one-variable configurations.
No incomplete entity is allowed through the final boundary, even for internal experiments.
