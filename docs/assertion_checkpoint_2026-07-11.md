# Assertion checkpoint - 2026-07-11

## Verified evidence

- Source: `input.zip`, SHA-256 `46fe4a578b2c4478faa7c570b218218f539c0bbf1ea409168ae67a14ad86ca35`, accessed 2026-07-11.
- Evidence: `tools/audit_assertions.py` processed all 100 documents and classified 184 existing drug, laboratory-name, and laboratory-value spans.
- Result: The rules emitted `isHistorical` for 64 spans, emitted no other organizer label on this extracted subset, and raised zero offset errors.
- Evidence: A corpus-derived regression reproduced and removed cross-comma propagation from `âm tính nitrite` to earlier laboratory spans.
- Confidence: High for the deterministic counts and offset integrity because they come from code executed against the pinned artifact.
- Strategic impact: Treat these counts as rule behavior, not as assertion accuracy or evidence of evaluator policy.

## Implemented policy

- Rules validate every input span against the immutable raw text before reading context.
- Newlines, commas, sentence punctuation, semicolons, `nhưng`, and `tuy nhiên` stop cue propagation.
- Pre-mention Vietnamese negation cues and post-mention `âm tính` are scoped to the containing clause.
- Past-history and medication-before-admission sections default to historical.
- Current-illness sections remain current without a local historical cue.
- Hypothetical cues override historical section priors but remain an internal state.
- Family reporter language remains patient-experiencer, while explicit illness of a relative becomes family-experiencer.
- Only `isNegated`, `isHistorical`, and `isFamily` can be exposed as organizer labels.
- No model or ontology code was added, so the active parameter budget remains `0 / 9B`.

## Known limits

- The current extracted subset contains no family-experiencer or hypothetical candidate span, so those branches are verified by synthetic tests rather than corpus frequency.
- Hypothetical and other-experiencer states have no verified organizer output label and are not serialized.
- Cue inventories and section priors remain hidden-policy variables for frozen-span leaderboard ablations.
- Drug and laboratory candidate quality limits still affect which spans enter this audit.

## Next checkpoint

Connect exact spans and assertion labels to a type-dependent serializer and strict output validator without adding unverified fields or ontology codes.
