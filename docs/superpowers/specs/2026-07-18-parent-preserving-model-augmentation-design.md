# Parent-Preserving Model Augmentation Design

## Objective

Improve model-assisted recall without removing or changing any entity already promoted in Submission 8.
The first controlled artifact will augment the validated Submission 8 archive with high-precision proposals from the original Submission 10 run.
It will not use the broader item-level salvage output in this experiment.

## Evidence

Submission 8 contains 521 entities and 17 accepted Qwen additions.
The original Submission 10 proposal archive contains 431 proposals and produces 147 accepted model entities when rebuilt from rules.
That rebuild adds 146 entities relative to Submission 8 but removes 16 promoted Qwen entities because the new prompt replaces the previous proposal layer.
The salvaged Submission 10 proposal archive contains 1,397 proposals and produces 531 accepted model entities, which is too large a precision change for a controlled first probe.

## Considered Approaches

### Parent-preserving augmentation from complete chunks

Use the validated Submission 8 archive as the immutable prediction parent.
Apply the existing grounding, section, structure, linking, assertion, and overlap gates only to proposals from complete Submission 10 chunks.
This is the selected approach because it changes one primary variable and cannot remove a promoted prediction.

### Parent-preserving augmentation with parse-only salvage

Also recover valid siblings from diagnostic chunks categorized as parse failures.
This may increase recall, but it introduces a second variable and will be considered only after the complete-chunk control is scored.

### Learned proposal filter

Train a classifier to rank or reject model proposals.
This is deferred because there is no trustworthy proposal-level gold set yet and a learned filter would add complexity without a reliable local target.

## Interface

Add `tools/augment_submission.py` with a reusable function:

```python
augment_submission(
    input_zip: Path,
    parent_zip: Path,
    proposal_root: Path,
    rxnorm_zip: Path,
    config_path: Path,
    destination: Path,
    icd_path: Path,
) -> dict[str, object]
```

The command-line interface will expose equivalent arguments and retain the pinned ontology checksum defaults used by the existing submission builder.
The configuration must enable model proposals and will supply the existing concept level and candidate policy.

## Data Flow

1. Read the canonical input ZIP without modifying raw text.
2. Validate document names and strict UTF-8 decoding.
3. Read and validate all 100 parent records against the canonical raw documents.
4. Read the pinned model proposal directory with the existing manifest and raw hash checks.
5. Treat every parent entity as protected stable evidence.
6. Pass each document's proposals through the existing exact grounding, section, structure, linking, assertion, and overlap gates.
7. Reject every proposal that overlaps a parent entity.
8. Resolve overlap among remaining proposals with the existing deterministic longest-span policy.
9. Append accepted entities to the unchanged parent entities and serialize with the existing output builder.
10. Validate the final archive and report the semantic diff against the parent.

## Invariants

- Every parent entity must remain byte-for-byte equivalent as a JSON value.
- Every new span must satisfy `raw_text[start:end] == text`.
- No raw text, ontology file, candidate identifier, or assertion label may be invented or modified.
- Parent entity order may be normalized by the existing position sort, but entity content must not change.
- New candidates may only come from the pinned ICD-10 or RxNorm snapshots through existing linkers.
- Combined active model parameters remain 4B.
- The output archive contains exactly `output/1.json` through `output/100.json`.

## Report

The augmentation report will include the parent checksum, proposal manifest identity, model parameter count, accepted and rejected proposal counts, output checksum, entity counts, candidate counts, assertion counts, and semantic diff summary.
The report must distinguish accepted additions from rejection categories already produced by `accept_model_proposals`.

## Promotion Gate

The local artifact is eligible for a portal probe only when all existing validators pass and the semantic diff reports:

- zero removed entities;
- zero changed entities;
- zero changed text, type, position, assertions, or candidates;
- exactly 150 total candidates;
- at least one accepted addition.

Passing this gate permits a controlled leaderboard experiment but does not automatically promote the artifact.
Promotion still requires an interpretable score gain that is plausible on private data.

## Testing

Tests will begin with a failing end-to-end augmentation case using a canonical input ZIP, a validated parent archive, and a proposal directory containing one overlapping proposal and one valid new proposal.
The test will verify that the parent entity is unchanged, the overlap is rejected, the new entity is added, and the result passes the submission validator.
Additional failure cases will cover a parent archive with invalid offsets, mismatched document names, or a proposal directory whose raw hashes do not match the canonical input.
The complete test suite and compilation checks must pass before merge or packaging.

## Scope Boundaries

This change does not alter Qwen prompts, run another GPU inference job, salvage diagnostic responses, train a classifier, change candidate cardinality, or modify the stable rule extractors.
The first local artifact uses Submission 8 as parent and the original non-salvaged Submission 10 proposal directory as its only new evidence source.
