# Submission Strategy

Plan around five guaranteed submissions per day.
Up to ten submissions from the other two legitimate team members are bonus exploration capacity and are never required by the development plan.

## Capacity allocation

- Use guaranteed capacity for high-confidence improvements and experiments that resolve important uncertainty.
- Use bonus capacity for parallel model, ontology, threshold, span, and evaluator-policy hypotheses.
- Change one primary variable per probing submission whenever possible.
- Keep one stable configurable pipeline rather than separate diverging implementations.

## Artifact identity

Every submitted artifact records its commit, config, output checksum, parent submission, and hypothesis in `docs/submissions.csv`.
Also record prediction diff, changed entity or candidate counts, score delta, conclusion, confidence, and generalization class.

## Promotion gate

Promote exploratory behavior into the stable baseline only when the improvement is reproducible, interpretable, and plausibly generalizable to private test data.
Do not promote an unexplained public score increase.

## Model gate

Every pipeline declares its active model subset in `configs/model_configurations.json`.
The combined parameter count must be at most 9B, a budget report is required for every configuration, and unused checkpoints must not be included in the final solution.
