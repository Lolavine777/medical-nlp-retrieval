# Deterministic Output Package Design

## Scope

Build and verify one deterministic ZIP containing exactly 100 serialized output files.
The component will not generate predictions, repair invalid entities, include metadata inside the ZIP, submit an artifact, or implement evaluation.
The first generated artifact will contain empty lists and will be named `outputs/NON_SUBMITTABLE-empty-output.zip`.
The active model parameter budget remains `0 / 9B`.

## Interface

`build_output_zip(documents, predictions, destination, schemas=DEFAULT_SCHEMAS)` consumes two mappings keyed by `input/1.txt` through `input/100.txt`.
Each document value is its immutable raw string.
Each prediction value is the complete entity list for that document.

The function returns a report containing:

- `entry_count`;
- `entity_count`;
- `empty_document_count`;
- `byte_count`;
- `sha256`.

## Validation and safety

Document and prediction keys must exactly match the expected 100 input names.
Missing, extra, or malformed source membership is rejected before ZIP construction.
Mapping insertion order is ignored and output is always normalized to numeric document order.
Each entity list is passed through the strict type-dependent serializer before packaging.

All ZIP bytes are built in memory and reopened for verification before any filesystem write.
The verifier requires exactly `output/1.json` through `output/100.json` in numeric order, parses each file as UTF-8 JSON, and runs the strict entity validator against the corresponding raw document.
No directory entry, traversal path, raw input, manifest, or extra file is allowed.

The destination parent must already exist.
The final write uses exclusive creation and refuses to overwrite any existing artifact.

## Determinism

Every entry uses a fixed ZIP timestamp of `1980-01-01 00:00:00` and `ZIP_STORED` compression.
Entries are written in numeric order with stable file permissions.
JSON bytes come directly from the deterministic serializer.
Identical inputs must produce identical ZIP bytes and SHA-256 values across repeated builds.

## Dry-run policy

The initial dry-run uses the pinned 100-document `input.zip` and one empty prediction list per document.
Empty lists are valid serializer inputs and exercise the complete packaging boundary without inventing ICD or RxNorm identifiers.
The filename contains `NON_SUBMITTABLE` and the artifact is not recorded in `docs/submissions.csv` because it must never be uploaded.

## Verification

Tests will build 100 empty outputs twice and compare exact bytes and checksums.
Tests will inspect the 100 entry names and contents.
Tests will reject missing or extra document keys, invalid entities, an existing destination, and a destination whose parent does not exist.
The pinned dry-run will be reopened and revalidated after creation, and its checksum will be recorded as format evidence rather than a leaderboard artifact.

## Known limits

An all-empty package verifies format and reproducibility only.
It provides no information about extraction, linking, assertions, evaluator matching, or leaderboard score.
The provisional local evaluator remains a separate checkpoint.
