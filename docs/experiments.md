# Experiment and Leaderboard Ledger

Leaderboard submissions are a limited experimental feedback loop, not an optimization oracle.
Every submission must test a documented hypothesis from a reproducible commit and configuration.
Prefer changing only one primary variable.
Public-test-specific hard-coding is prohibited.

## Required submission record

Copy this template before generating a submission.

```markdown
### Submission identifier

- Date and time:
- Commit:
- Configuration:
- Hypothesis:
- Baseline submission:
- Primary variable changed:
- Expected prediction effect:
- Prediction diff summary:
- Files changed in prediction:
- Entity additions:
- Entity removals:
- Type changes:
- Assertion changes:
- Candidate changes:
- Public score before:
- Public score after:
- Score delta:
- Conclusion:
- Next decision:
```

## Submission gate

- Reject a submission without a hypothesis, commit, and saved configuration.
- Reject a submission that bundles unrelated primary changes unless it is an explicitly documented integration test.
- Generate and inspect a semantic prediction diff before submission.
- Record a null or negative score result with the same care as a positive result.
- Do not repeat a failed hypothesis without new evidence.

## Quota monitoring

The observation that quotas may apply per team member rather than per team is unconfirmed.
Monitor organizer clarification and plan under the conservative visible quota.
Do not make quota interpretation a core architectural assumption.
