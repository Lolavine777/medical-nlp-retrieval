# Experiment and Leaderboard Ledger

Use the leaderboard as a limited experimental feedback loop.
Plan around five guaranteed daily submissions and treat up to ten legitimate team-member submissions as bonus exploration capacity.

## Stable pipeline rule

Maintain one stable pipeline with configurable policies.
Exploratory work changes configuration or isolated components rather than creating unrelated codebases.

## Submission gate

- Require commit, config, output checksum, parent submission, and hypothesis.
- Prefer one primary change.
- Inspect a semantic prediction diff before submission.
- Record changed entities, candidates, assertions, score delta, conclusion, confidence, and generalization class.
- Record null and negative results.
- Never hard-code public-test data or evade submission limits.

## Capacity usage

- Guaranteed capacity: high-confidence improvements and high-information uncertainty reduction.
- Bonus capacity: model, ontology, threshold, span, and evaluator-policy branches.
- Bonus capacity must never become a dependency of the baseline plan.

## Promotion gate

Promote an exploratory result only when it is reproducible from its commit and config, interpretable from its prediction diff, and plausibly generalizable to the private test.
Classify results as `generalizable`, `public-specific-risk`, or `unknown`.

## Model gate

Every active pipeline declares its model subset and parameter report in `configs/model_configurations.json`.
The combined count must not exceed 9B and final artifacts must exclude unused checkpoints.
