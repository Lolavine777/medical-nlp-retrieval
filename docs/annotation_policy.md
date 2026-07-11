# Annotation Policy

This policy separates official observations and mandatory local invariants from provisional rules.

## Official observations and mandatory local invariants

### Raw text and offsets

- Never mutate the raw input string used for output.
- Use exact UTF-8 source text for every entity `text` value.
- Generate `[start, end]` offsets satisfying `raw_text[start:end] == entity["text"]` locally.
- Treat end-exclusive semantics and exact position matching as strong evidence, not disclosed evaluator behavior.
- Preserve line endings and whitespace and keep normalized text separately mapped to raw indices.
- Do not simulate CRLF offsets outside a controlled one-variable experiment.

### Mention identity and fields

- Preserve separate occurrences even when surface text and concepts are identical.
- The observed `THUỐC` schema has `text`, `type`, `candidates`, `assertions`, and `position`.
- The observed `TRIỆU_CHỨNG` schema has no `candidates` field.
- Do not add unapproved fields.
- Treat schemas for diagnosis and both laboratory types as unresolved.

### Drug spans and ontology safety

- Keep contiguous raw medication regimen text shown by official examples.
- Exclude following indications when official examples separate them.
- Treat example identifiers as opaque until the ontology is verified.
- Never emit a code absent from an approved local snapshot.

## Provisional rules

### Section and assertion context

- Use diagnosis and symptom sections as priors, not absolute type rules.
- Treat past medical, surgical, and pre-admission medication sections as historical priors.
- Do not mark current-illness sections historical by header alone.
- Scope negation to clauses and terminate at sentence, section, list, semicolon, and contrast boundaries.
- Track family reporter separately from family experiencer.

### Candidate sets

- Use top one until multi-code evidence supports broader sets.
- Add candidates only when calibrated expected Jaccard improves.
- Calibrate separately by type and ontology granularity.

## External data

- Map every source label explicitly into competition types before training.
- Use external data mainly for adaptation and span detection.
- Competition context, sections, examples, and schema override source-dataset policy.

## Review triggers

Revise this policy when organizer evidence, ontology snapshots, evaluator clarification, or reproducible submissions falsify a rule.
