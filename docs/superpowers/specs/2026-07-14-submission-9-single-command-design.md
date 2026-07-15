# Submission 9 Single-Command Kaggle Design

## Objective

Replace the accumulated debugging notebook with one reproducible repository command and a minimal Kaggle notebook.

## Boundary

The command performs Qwen proposal inference only.
It does not train a model, build a leaderboard submission, or change proposal acceptance policy.
The active model remains the pinned 4B Qwen revision under the combined 9B budget.

## Flow

The runner discovers one canonical 100-document input source under `/kaggle/input`, creates `/kaggle/working/input.zip`, downloads or reuses the pinned model snapshot, and launches one generator process per GPU.
Each worker writes a separate resumable shard and log.
The parent process prints completed-document counts until both workers exit.
It then merges the shards, validates all records and 2,500-character chunk counts, creates `qwen3-4b-s009.zip`, and prints its SHA-256.

The notebook contains only setup and one foreground runner invocation.
All orchestration and validation live in the tested Python script.

## Failure handling

Ambiguous input sources, invalid UTF-8, missing documents, unequal manifests, failed workers, wrong chunk counts, and invalid proposal records abort packaging.
Worker logs remain under `/kaggle/working` for diagnosis.
Existing valid shard records are resumed rather than regenerated.

## Verification

Unit tests cover canonical input preparation, ambiguity rejection, strict shard merge, and worker failure reporting without loading the model.
The full repository suite, compilation, notebook JSON validation, and diff check must pass before packaging the code ZIP.
