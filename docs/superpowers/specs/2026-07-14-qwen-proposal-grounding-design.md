# Qwen Proposal and Grounding Design

## Objective

Add model-assisted clinical mention recall to the stable Submission 7 pipeline without allowing a generative model to write final entities, offsets, assertions, candidates, or schema fields directly.

The first model-assisted submission will change one primary variable: enabling grounded Qwen mention proposals on top of Submission 7.

## Constraints

- Preserve raw input text, whitespace, line endings, and duplicate mentions.
- Require `raw_text[start:end] == text` for every output entity.
- Keep one configurable pipeline with Submission 7 as the model-off fallback.
- Emit only the five organizer-approved entity types and their existing type-dependent schemas.
- Emit diagnosis and drug candidates only through the pinned ICD-10 and RxNorm linkers.
- Keep combined active model parameters at or below `9,000,000,000`.
- Use no external inference API in the judged solution.
- Keep the final runner reproducible on arbitrary private documents.
- Never add document-specific rules, cached answers as program logic, or public-test lookup tables.

## Considered approaches

### Approach A: Qwen proposals with deterministic grounding

This is the selected approach.

One locally loaded instruction model proposes exact mention text and type while the existing pipeline owns every trusted output field.
It requires no training dataset and can improve multiple entity classes immediately.
Its main risk is false-positive proposals, which fail closed through exact grounding, section compatibility, linking, overlap, and schema gates.

### Approach B: Fine-tuned XLM-R token classifier

This would use fewer parameters and faster inference.
It is deferred because no competition-aligned labeled training set exists, and currently available Vietnamese medical NER resources have uncertain label and genre transfer.

### Approach C: Fuzzy ontology expansion without a model

This would add the least runtime complexity.
It is deferred because it cannot recognize symptoms and laboratory concepts that are absent from the pinned ontology titles and is unlikely to close the remaining `37.13620` public-score gap.

## Model identity and budget

The only active model will be `Qwen/Qwen3-4B-Instruct-2507` at Hugging Face revision `1b4199c4f36b0cef378bfb12390c18780c18af4c`.
The official model card reports `4.0B` parameters and Apache-2.0 licensing.
The active configuration therefore reports `4,000,000,000 / 9,000,000,000` parameters.

The model snapshot, revision, license, file checksums, acquisition command, redistribution status, and local path policy will be recorded before inference.
No secondary encoder, reranker, embedding model, or unused checkpoint will be active in this milestone.

## Runtime boundary

Kaggle is the preferred free development runtime, and the same notebook path must remain compatible with Google Colab.
The notebook loads the pinned weights into its own process and never calls a hosted inference endpoint.

Kaggle and Colab are development compute only.
The private-test solution will run the same local model-loading and proposal code on organizer-provided GPU infrastructure with network access disabled after artifacts are present.

The model runtime will use PyTorch and Hugging Face Transformers with `transformers>=4.51.0`, as required by the model card.
The first implementation will use the official BF16 safetensors rather than add a quantization or serving framework.

## Proposal interface

The model receives one bounded section chunk at a time.
Each prompt includes the recognized section heading and raw lines numbered relative to that chunk.

The model returns a strict JSON array containing only:

```json
[
  {
    "line_index": 0,
    "text": "exact substring copied from the supplied line",
    "type": "TRIỆU_CHỨNG"
  }
]
```

Allowed types are `TRIỆU_CHỨNG`, `TÊN_XÉT_NGHIỆM`, `KẾT_QUẢ_XÉT_NGHIỆM`, `CHẨN_ĐOÁN`, and `THUỐC`.
The model does not propose offsets, candidates, assertions, confidence scores, or extra metadata.

Generation uses `do_sample=false` and a fixed maximum output length.
Prompts contain only generic policy instructions and organizer-approved examples or synthetic examples, never document-specific corrections.

## Deterministic grounding and acceptance

Each proposed `line_index` must identify a supplied raw line.
Each proposed `text` must occur verbatim in that line.
Every verbatim occurrence in the identified line is grounded to an end-exclusive raw offset so duplicate mentions are preserved.

The acceptance pipeline applies these gates in order:

1. Parse strict JSON and reject unknown keys, types, or value shapes.
2. Ground the exact text in the identified raw line.
3. Enforce type-compatible section and line roles.
4. Drop exact duplicates and resolve overlaps in favor of existing Submission 7 predictions.
5. Require a pinned top-one ICD candidate for diagnoses and a pinned top-one RxNorm candidate for drugs.
6. Derive assertions with the existing deterministic assertion classifier.
7. Serialize through the existing type-specific schema and output validator.

Model proposals can add entities but cannot remove or change a Submission 7 entity.
Unlinked diagnosis and drug proposals are rejected rather than emitted with invented or empty candidates.

## Data flow

```text
Raw document
  -> existing loader and section parser
  -> bounded raw-line chunks
  -> local Qwen proposal generation
  -> strict JSON parser
  -> exact raw-line grounding
  -> section and line-role gate
  -> existing ICD or RxNorm linker when required
  -> existing assertion classifier
  -> merge over unchanged Submission 7 entities
  -> existing serializer and validators
  -> deterministic ZIP
```

Proposal records are saved per document with the input checksum, model revision, prompt version, generation configuration, and proposal checksum.
Per-document atomic files make interrupted Kaggle or Colab runs resumable.
These records are reproducibility evidence and an intermediate cache, not final-solution logic.

## Failure handling

Malformed model output fails closed for that chunk and leaves the Submission 7 output unchanged.
Hallucinated or normalized text fails exact grounding and is rejected.
Unknown types, fields, or line indices are rejected.
Unlinked diagnosis or drug proposals are rejected.
GPU interruption resumes from completed per-document proposal files.
Any invalid final entity aborts packaging through the existing validator.

No automatic prompt mutation, external repair API, or manual document-specific patch is permitted.

## Testing and validation

Unit tests will use static proposal payloads rather than loading the 4B model.
They will cover strict parsing, exact grounding, duplicate occurrences, malformed output, normalized-text rejection, section compatibility, overlap precedence, unlinked candidate rejection, assertion derivation, and strict schema output.

Regression tests will prove that model-off output remains byte-identical to Submission 7 behavior.
Integration tests will use a stub proposal provider to prove that accepted model proposals pass through the existing pipeline without changing stable entities.

The Kaggle notebook will run a synthetic smoke test before processing competition inputs.
The complete 100-document run must produce valid offsets and schemas, stable model and prompt metadata, per-type counts, rejection counts by gate, and a semantic diff against Submission 7.

The full repository test suite, Python compilation, output validation, deterministic packaging check, checksum report, and model-budget report must pass before an artifact is offered for upload.

## Submission and promotion gate

The model-assisted artifact will use Submission 7 as its parent.
Its ledger record will include commit, config, artifact checksum, model revision, prompt version, prediction diff, changed counts, hypothesis, and model budget.

The artifact is eligible for leaderboard submission only when it removes or changes zero Submission 7 entities and every added entity passes the deterministic gates.
The model path is promoted only if the score gain is reproducible, interpretable from the diff and rejection report, and plausibly generalizable to private documents.

## Sources

- Qwen model card and parameter report: https://huggingface.co/Qwen/Qwen3-4B-Instruct-2507
- Pinned model revision: https://huggingface.co/Qwen/Qwen3-4B-Instruct-2507/commit/1b4199c4f36b0cef378bfb12390c18780c18af4c
- Google Colab resource policy: https://research.google.com/colaboratory/faq.html
- Local competition policy: `research/competition_policy.md`
- Local submission policy: `docs/submission_strategy.md`
