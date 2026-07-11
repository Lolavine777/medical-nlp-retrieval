# Annotation Policy

This policy separates rules demonstrated by official evidence from provisional rules that require organizer clarification or labeled data.

## Verified rules

### Raw text and offsets

- Never mutate the raw input string used for output.
- Use exact UTF-8 text from the source for every entity `text` value.
- Store offsets as `[start, end]` with an end-exclusive boundary.
- Require `raw_text[start:end] == entity["text"]` for every serialized entity.
- Preserve line endings and leading spaces because rendered HTML can collapse offset-significant whitespace.

### Mention identity

- Emit separate objects for separate occurrences even when surface text and concept are identical.
- Do not deduplicate `táo bón`, `lo âu`, or any other repeated mention across positions.

### Observed entity fields

- A `THUỐC` object in the official example has `text`, `type`, `candidates`, `assertions`, and `position`.
- A `TRIỆU_CHỨNG` object in the official example has `text`, `type`, `assertions`, and `position` and does not have `candidates`.
- Do not add `relations` or any other unapproved output field.
- Treat schemas for `CHẨN_ĐOÁN`, `TÊN_XÉT_NGHIỆM`, and `KẾT_QUẢ_XÉT_NGHIỆM` as unresolved.

### Drug spans

- Include the medication name and the contiguous regimen text shown in the official examples, including strength, dose form, route, frequency, and PRN markers when present.
- Exclude a following indication introduced by constructions such as `điều trị` when the official examples separate it into another mention.
- Keep the full raw medication span even when ontology normalization uses only some parsed attributes.

### Ontology safety

- Treat organizer example identifiers as opaque until the ontology is verified.
- Never invent an ICD or RxNorm code.
- Emit only identifiers found in an approved local snapshot with recorded provenance and checksum.

## Provisional rules

### Section-aware type priors

- Prefer `CHẨN_ĐOÁN` in confirmed diagnosis, chronic disease, and diagnostic finding sections.
- Prefer `TRIỆU_CHỨNG` in current symptom and admission-reason sections.
- Do not let section prior override a clear local construction without evaluation evidence.

### Historical status

- Treat past medical, surgical, and pre-admission medication sections as historical priors.
- Do not mark history-of-present-illness sections historical by header alone.
- Let explicit local temporal cues override weak section priors.

### Negation scope

- Apply negation within a clause rather than across an entire line or section.
- Terminate scope at sentence boundaries, section boundaries, list-item boundaries, semicolons, and contrast markers such as `nhưng` or `tuy nhiên`.
- Keep trigger, pseudo-trigger, and terminator lexicons versioned and testable.

### Family status

- Track family reporter separately from family experiencer.
- Set the internal family-experiencer state only when the condition belongs to a relative.
- Do not set family merely because a relative reports the patient's condition.

### Candidate sets

- Use top one as the conservative default until multi-code evidence exists.
- Add another candidate only when calibrated expected Jaccard improves.
- Calibrate thresholds separately by entity type and ontology granularity.

## Review triggers

Revise this policy when the organizer publishes a new example, ontology snapshot, evaluator clarification, forum ruling, or reproducible leaderboard result that falsifies a provisional rule.
Record the source, access date, affected rule, and expected prediction diff with every revision.
