# Reliable Dual-GPU Qwen Generation Design

## Objective

Produce a more complete Qwen proposal archive overnight without training on unverified weak labels.

## Design

Reuse the existing prompt, strict parser, grounding, manifest, resumable records, and configurable chunk size.
Use smaller 2,500-character chunks to reduce oversized malformed responses.
Add deterministic document sharding so two independent processes can run on GPU 0 and GPU 1 and write separate shard directories for strict merging afterward.

The active model remains `Qwen/Qwen3-4B-Instruct-2507` at revision `1b4199c4f36b0cef378bfb12390c18780c18af4c`, with `4,000,000,000 / 9,000,000,000` active parameters.
No new dependency, model, output entity policy, or portal submission is introduced.

## Failure handling

Malformed output continues to fail closed under the existing parser.
Each worker processes documents whose stable numeric document ID maps to its shard.
Separate output directories avoid concurrent writes, and the merged archive must pass strict validation against all 100 canonical documents.

## Verification

Unit tests prove disjoint and exhaustive deterministic sharding.
The full suite, compilation, and a local two-shard smoke run must pass before Kaggle instructions are provided.
