# Conservative Assertion Rules Design

## Scope

Implement deterministic assertion classification for an existing exact raw span.
The component will not discover entities, alter offsets, infer ontology codes, or serialize final JSON.
The active model parameter budget remains `0 / 9B`.

## Interface

`classify_assertions(raw_text, span)` will return an immutable internal state with three independent dimensions:

- `negated`: a boolean.
- `temporality`: `current`, `historical`, or `hypothetical`.
- `experiencer`: `patient`, `family`, or `other`.

The input span must be non-empty, in bounds, and satisfy `raw_text[start:end] == span.text`.
Invalid spans will raise `ValueError` instead of producing assertions from incorrect context.

The internal state will expose a deterministic mapping to only the organizer-known labels `isNegated`, `isHistorical`, and `isFamily`.
Hypothetical and other-experiencer states remain internal because no corresponding organizer label is verified.

## Scope and cues

Rules will inspect the entity's physical line and the clause containing it.
Newlines, sentence punctuation, semicolons, and contrast terminators such as `nhưng` and `tuy nhiên` will stop cue propagation.

Negation will use a small Vietnamese cue inventory including `không`, `chưa`, `phủ nhận`, and post-mention findings such as `âm tính`.
False-trigger cases will be protected by clause scope rather than document-wide cue matching.

Historical status will use local temporal cues plus conservative section priors.
Past-history sections and medication-before-admission sections will default to historical.
Current-illness sections will not become historical solely from their section name.
Explicit hypothetical or planned language will take precedence over a historical prior.

Family status will require evidence that a relative is the clinical experiencer of the entity.
Reporter constructions such as `gia đình nhận thấy bệnh nhân` will retain patient experiencer.
Relative terms without a relation to the entity will not propagate across clause boundaries.

## Precedence

Local entity-clause cues take precedence over section priors.
Negation is independent of temporality and experiencer, so valid multi-label outputs remain possible.
When no rule fires, the default state is non-negated, current, and patient.

## Verification

Tests will cover:

- pre-mention and post-mention negation;
- clause and contrast-terminator boundaries;
- past-history and medication section priors;
- current-illness non-history behavior;
- explicit historical and hypothetical cues;
- family experiencer versus family reporter;
- exact-span validation and stable organizer-label ordering.

Corpus audit will run the rules against existing drug and laboratory spans, verify that offsets remain unchanged, and report assertion counts without treating them as evaluator accuracy.

## Known uncertainty

The organizer has intentionally hidden assertion matching details beyond the three known labels.
Cue inventories and section priors are provisional policies to be tested through frozen-span leaderboard ablations.
No public-test-specific cue or document-specific rule will be added.
