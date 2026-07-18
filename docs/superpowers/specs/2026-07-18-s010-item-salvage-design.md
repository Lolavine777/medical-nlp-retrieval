# Submission 10 Item-Level Salvage Design

## Evidence

The Submission 10 model run produced 431 accepted proposals and 70 failed chunks across 110 chunks.
All 70 failed responses begin with a JSON array.
Nine responses contain at least one invalid type value.
Sixty-one responses contain at least one proposal that is not verbatim on its declared line or lies outside its prompt chunk.
Replaying every response item independently found 966 additional proposals that already satisfy the strict schema, prompt-chunk boundary, and verbatim grounding rules.

## Goal

Retain every independently valid model proposal without weakening raw-text, offset, type, or prompt-boundary validation.
Reuse the completed Qwen run and avoid another GPU inference job.

## Considered approaches

### Item-level strict validation and offline replay

Parse the outer JSON array once, validate each object with the existing strict parser, verify its line belongs to the source chunk, and ground that single proposal verbatim.
Keep valid items and reject invalid items without affecting their siblings.
This is the selected approach because it fixes the all-or-nothing failure while preserving every existing trust boundary.

### Fuzzy text alignment

Normalize case, punctuation, or whitespace and map approximate text back to raw spans.
This could recover more proposals but risks turning paraphrases and hallucinations into accepted entities.
This approach is excluded from Submission 10.

### Prompt revision and model rerun

Change the prompt and repeat Qwen inference.
This costs GPU time and does not fix the generator's chunk-level rejection behavior.
This approach is deferred until item-level results are measured.

## Runtime behavior

A response that is not a JSON array remains a failed chunk with no accepted proposals.
A JSON array is processed one item at a time.
An item is accepted only when it has exactly `line_index`, `text`, and `type`, uses an allowed prompt-version type, refers to a line in its prompt chunk, and grounds verbatim in the immutable raw document.
Invalid items are discarded without normalization, type correction, fuzzy matching, or offset synthesis.
The chunk receives one diagnostic record when any item is discarded.
The diagnostic category is `parse` when any item fails schema or type validation, otherwise `grounding`.
The existing `parse_error_count` remains the count of imperfect chunks and therefore remains at most `chunk_count`.

## Offline replay

A small command-line tool consumes the canonical input ZIP, the original proposal ZIP, and the diagnostics ZIP.
It validates both archives, replays each failed response through the same item-level validator, merges only new valid proposals into their original document record, and writes a normal proposal directory.
The original manifest and per-document chunk counts remain unchanged.
The original imperfect-chunk counts remain unchanged for provenance.
The tool reports recovered, rejected, and final proposal counts by type.

## Promotion gate

The replayed proposal directory must pass `read_proposal_directory` against the canonical 100 documents.
The rebuilt competition archive must pass the submission validator.
The semantic diff against Submission 8 must contain zero removals and zero changes to stable entities or candidates.
Candidate count must remain 150.
Every newly accepted model entity must still pass the existing section, structure, overlap, and linking gates.
The current raw Qwen archive is never uploaded directly to the portal.

## Tests

Regression tests must demonstrate that a valid item survives beside an invalid grounding item, a valid item survives beside an unknown type, an invalid JSON response still fails closed, and replay produces a proposal directory accepted by the existing reader.
The full repository test suite and compilation checks must pass before integration.
