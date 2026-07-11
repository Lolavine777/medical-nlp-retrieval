# Annotation Policy

## Mandatory local invariants

- Preserve exact raw UTF-8 text, whitespace, line endings, and duplicate mentions.
- Generate local offsets satisfying `raw_text[start:end] == entity["text"]`.
- Keep normalized text separately mapped to raw indices.
- Treat exact evaluator position matching and boundary policy as hidden.
- Do not add unapproved fields or emit codes absent from a pinned local ontology.

## Observed fields and spans

- Observed `THUỐC` objects have `text`, `type`, `candidates`, `assertions`, and `position`.
- Observed `TRIỆU_CHỨNG` objects have no `candidates` field.
- Diagnosis and laboratory schemas remain hidden variables.
- Drug examples include contiguous regimen modifiers and exclude separable following indications.

## Configurable hidden policies

- Compare core spans with modifier-inclusive spans by entity type.
- Keep active and historical RxNorm concepts plus replacement relationships when legally available.
- Do not automatically replace retired RXCUIs with current successors.
- Keep ingredient, clinical-drug, branded-drug, combination, and component candidate policies configurable.
- Use top one until calibrated experiments support broader candidate sets.
- Use section, history, negation, family, and type rules as tested priors rather than hidden-policy assumptions.
- Compare raw offsets with alternative position strategies only when all non-position predictions are identical.

## External data

Map every source label explicitly into competition types.
Use external data mainly for adaptation and span detection; competition evidence and controlled experiments determine final policy.

Revise this file only from source evidence or reproducible controlled submissions.
