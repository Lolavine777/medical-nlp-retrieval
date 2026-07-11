# Model Parameter Budget

The organizer confirmed that the combined parameter count of all models in the solution must not exceed 9B.
Count independent ensemble checkpoints separately and do not treat quantization as reducing parameter count.

The current budget is 0 of 9,000,000,000 parameters.
Update this file and `configs/model_budget.json` before adding any model.

| Model | Purpose | Base parameters | Adapter parameters | Shared weights | Counted parameters | Running total |
|---|---|---:|---:|---|---:|---:|
| None | Rule baseline | 0 | 0 | Not applicable | 0 | 0 |

Use conservative accounting until the organizer clarifies whether synthetic-data generators, distillation teachers, ontology-embedding models, LoRA adapters, and merged checkpoints count.
