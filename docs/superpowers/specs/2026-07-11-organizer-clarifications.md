# Organizer Clarifications and Experiment Constraints

## Confirmed model budget

The combined parameter count of every model used by the solution must not exceed 9B.
The repository must record the running total before any model is added.
The architecture should prefer shared backbones, compact models, rules, lexical retrieval, ontology indices, and deterministic postprocessing.

## Leaderboard protocol

Every leaderboard submission must test a documented hypothesis from a reproducible commit and configuration.
Prefer changing only one primary variable per submission.
Record the prediction diff, score delta, and conclusion.
Do not optimize blindly for public leaderboard gains or introduce public-test-specific hard-coding.

## Unconfirmed quota observation

The observation that submission quotas may apply per team member rather than per team is unconfirmed.
Monitor organizer clarification, but do not use this observation as an architectural assumption.
