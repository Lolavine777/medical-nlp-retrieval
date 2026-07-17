# Submission 10 Targeted Qwen Design

## Objective

Turn the existing Qwen proposal path into a useful source of additional symptom and laboratory mentions without changing the stable rules, linkers, candidates, or previously accepted entities.

Submission 10 is created only if the new proposal run makes a meaningful, auditable semantic change over the stable Submission 8 output.
The upgraded problem expected on 21 July is not treated as live until the team lead confirms and preserves the official artifacts.

## Evidence

Submission 8 added 17 grounded symptom entities and improved the score from `15.86380` to `16.13250`.
Submission 9 used the same prompt and produced the same final output, so it was a reproducibility control rather than an improvement.

The Submission 9 proposal run processed 110 chunks and recorded 61 parse errors.
It produced zero proposals for 52 of the 100 documents.
Its 636 parsed proposals comprised 298 symptoms, 151 laboratory results, 9 laboratory names, 119 diagnoses, and 59 drugs.
The stable builder rejected 152 proposals for section incompatibility, 337 for invalid structure, 64 for stable overlap, and 65 for missing candidates.
Only the same 17 symptoms accepted for Submission 8 survived all gates.

The current all-type prompt spends output capacity on diagnosis and drug proposals that cannot become final entities unless the pinned linkers resolve them.
Candidate retrieval and reranking belong to Workstream A, so Submission 10 will not duplicate or bypass that work.

## Considered approaches

### Relax response parsing

The generator could accept Markdown fences, prose, or a JSON substring instead of requiring the entire response to be a JSON array.
This might recover some of the 61 failed chunks, but the raw failed responses were not retained and the successfully parsed proposals still contained 337 structural failures.
Relaxing the parser without evidence would combine a format-policy change with uncertain proposal quality.

### Fine-tune a span model

A compact token classifier could provide faster and more stable inference.
It is deferred because there is no competition-aligned gold training set, and a same-day weak-label training run would not provide a trustworthy promotion signal.

### Use a task-focused prompt profile

This is the selected approach.
The model, model revision, strict parser, chunk size, deterministic gates, and stable pipeline remain fixed.
Prompt version 2 asks only for symptoms, laboratory names, and laboratory results and gives concise atomic-span rules.

This tests one primary hypothesis: reducing task breadth and specifying atomic boundaries will lower format and structural failures enough to produce useful new entities.

## Model and parameter budget

The only active model remains `Qwen/Qwen3-4B-Instruct-2507` at revision `1b4199c4f36b0cef378bfb12390c18780c18af4c`.
The active parameter count remains `4,000,000,000 / 9,000,000,000`.
No training, second model, hosted inference API, quantization dependency, or unused checkpoint is added.

## Prompt profiles and backward compatibility

Prompt version 1 remains registered with its existing exact text and SHA-256 so Submission 8 and Submission 9 proposal artifacts stay readable and reproducible.
Prompt version 2 becomes the default only for new generation.

The implementation will keep a small version-to-prompt registry containing versions 1 and 2.
Manifest validation will require a known integer prompt version and the exact SHA-256 registered for that version.
Proposal records using prompt version 2 may contain only `TRIỆU_CHỨNG`, `TÊN_XÉT_NGHIỆM`, and `KẾT_QUẢ_XÉT_NGHIỆM`.
Version 1 retains the five existing allowed proposal types.

The generator receives an explicit prompt version and writes it into the manifest.
Existing version 1 manifests require no migration.

## Prompt version 2 contract

The prompt continues to receive raw lines formatted as global line index, section, role, and raw text separated by tabs.
The response must remain one strict JSON array with objects containing exactly `line_index`, `text`, and `type`.
No Markdown fence, explanation, confidence, offset, candidate, assertion, or additional field is allowed.

The prompt permits only these output types:

- `TRIỆU_CHỨNG`;
- `TÊN_XÉT_NGHIỆM`;
- `KẾT_QUẢ_XÉT_NGHIỆM`.

The prompt requires every `text` value to be copied verbatim from one supplied raw line.
It asks for atomic mentions rather than a complete bullet, sentence, heading, or clause.
It excludes headings, metadata, procedures, normal-state descriptions, dates, standalone units, and treatment actions.

For a laboratory line, the test name and its value or qualitative result must be separate objects.
A short synthetic example will demonstrate two name-result pairs on one line and a symptom line with assertion cues excluded from the copied symptom span.
The example must not contain a phrase copied from the Round 1 documents.

The prompt stays concise and replaces the version 1 header rather than appending an accumulating instruction history.

## Generation and diagnostics

The full run keeps deterministic generation with `do_sample=false`, `max_new_tokens=2048`, and `max_chars=2500`.
Two independent workers continue to shard documents across two T4 GPUs and merge only after both workers finish successfully.

The generator will retain the raw model response for a failed chunk in a separate ignored diagnostics location.
Each diagnostic record contains the document name, chunk ordinal, prompt version, error category, and raw response.
Diagnostic records are never read by the prediction pipeline, included in the final submission archive, committed to Git, or used as document-specific corrections.

The strict response parser is not relaxed for Submission 10.
Malformed, truncated, fenced, explanatory, or otherwise non-conforming responses continue to fail closed.

## Smoke run

Before the full run, one GPU processes the deterministic ten-document shard selected by `shard_index=0` and `shard_count=10`.
This selection depends only on numeric document IDs and is not chosen from public-test content.

The full run proceeds only when:

- fewer than 20 percent of smoke-run chunks have parse errors;
- every parsed proposal uses one of the three version 2 types;
- a manual inspection finds no systematic whole-line, heading, metadata, or procedure output;
- the proposal directory passes strict manifest, checksum, grounding, and deterministic-order validation.

If the smoke gate fails, no full run or Submission 10 archive is created.
The saved diagnostics will determine a later single-variable parser, chunking, or prompt experiment.

## Full run and build flow

The accepted flow is:

```text
Round 1 raw documents
  -> existing line-role and section representation
  -> prompt version 2 chunks
  -> pinned local Qwen generation on two T4 GPUs
  -> strict JSON and prompt-profile validation
  -> exact raw-line grounding
  -> existing section and atomic-structure gates
  -> existing assertion derivation for symptoms
  -> merge over unchanged Submission 8 entities
  -> existing serializer, preflight, deterministic ZIP, and semantic diff
```

Submission 10 uses Submission 8 as its semantic parent.
The stable rule configuration, diagnosis behavior, drug behavior, ontology snapshots, candidate policy, assertion engine, and output schema remain unchanged.

Because prompt version 2 cannot propose diagnoses or drugs, Submission 10 must preserve all 150 existing candidates and produce zero candidate changes.
Model proposals remain add-only and cannot remove or modify a stable entity.

## Local promotion gate

A portal-ready archive is created only when all of these checks pass:

- the complete proposal directory covers all 100 documents and validates against the canonical input hashes;
- fewer than 20 percent of full-run chunks have parse errors;
- at least 25 new entities survive all deterministic gates;
- accepted additions occur in at least 10 documents;
- the semantic diff reports zero removals and zero changes to existing text, type, position, assertions, or candidates;
- the candidate count remains 150 and candidate diff count remains zero;
- every accepted addition satisfies `raw_text[start:end] == text`;
- manual review of every addition finds no obvious heading, metadata, procedure, whole-line, or normal-state false positive;
- final preflight, deterministic rebuild, full tests, prompt manifest, and 4B budget report pass.

An archive that fails any gate remains a diagnostic model run and is not numbered or submitted as Submission 10.

## Portal decision

The portal hypothesis is that task-focused Qwen proposals recover genuine symptom and laboratory mentions missed by the stable pipeline while leaving candidates unchanged.

The result is promoted only if the score exceeds `16.13250` and the component changes are consistent with improved mention coverage.
Candidate Jaccard is expected to remain exactly unchanged.
A score loss, candidate change, unexplained component movement, or non-generalizable gain rejects promotion.

The submission ledger will record the implementation commit, prompt version and SHA-256, model revision, parameter budget, proposal checksum, config checksum, final ZIP checksum, parent, semantic diff, rejection counts, portal metrics, and conclusion.

## Upgrade boundary

If the organizer publishes the upgraded problem before the portal run, Submission 10 pauses.
The team first preserves the official artifacts and executes `docs/post_update_bringup_checklist.md`.
Prompt version 2 is then evaluated as a control on the upgraded data rather than assumed to transfer unchanged.
