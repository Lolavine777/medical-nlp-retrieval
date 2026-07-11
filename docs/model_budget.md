# Model Parameter Budget

The organizer-confirmed combined limit is 9B parameters across the active model subset.
Independent checkpoints count separately and quantization does not reduce parameter count.

Current model configurations and their parameter reports live in `configs/model_configurations.json`.
The stable rule baseline uses 0 of 9,000,000,000 parameters.

## Required report fields

Every configuration records:

- Configuration identifier and status.
- Active model identifiers only.
- Combined parameter count and compliance result.
- Shared-weight accounting evidence.
- Confirmation that unused checkpoints are excluded.

Reject a configuration that exceeds 9B, lacks a report, or includes unused checkpoints.
Count generators, teachers, ontology embedders, LoRA, and merged checkpoints conservatively until organizer accounting is known.
