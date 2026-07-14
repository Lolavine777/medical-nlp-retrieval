# Qwen Proposal Generation on Free GPU Compute

This run produces proposal evidence only.
It does not produce a leaderboard submission, and it does not call an external inference API.

## Required artifacts

- Use the committed `qwen_grounded_code.zip` archive prepared from this repository.
- Use the canonical `input.zip` without editing or re-encoding any document.
- Use a Kaggle GPU runtime as the preferred free option.
- Google Colab is the fallback free option.

The only active model is `Qwen/Qwen3-4B-Instruct-2507` at revision `1b4199c4f36b0cef378bfb12390c18780c18af4c`.
The declared active parameter budget is `4,000,000,000 / 9,000,000,000`.

## Kaggle procedure

Create a private Kaggle notebook with GPU acceleration enabled.
Enable internet only while installing packages and downloading the pinned Hugging Face revision.
Upload and unpack `qwen_grounded_code.zip`, then place `input.zip` in the repository root.

Run from the unpacked repository root:

```bash
pip install -r requirements-model.txt
export PYTHONPATH=.:src
python tools/generate_model_proposals.py \
  --input input.zip \
  --output /kaggle/working/qwen3-4b-s008
cd /kaggle/working && zip -qr qwen3-4b-s008.zip qwen3-4b-s008
```

The generator prints the pinned manifest metadata before model loading.
Confirm that the printed revision is `1b4199c4f36b0cef378bfb12390c18780c18af4c`, the model parameter count is `4000000000`, and sampling is disabled.

Inspect `/kaggle/working/qwen3-4b-s008/manifest.json` before downloading the archive.
It must contain the pinned model ID and revision, prompt version `1`, the prompt SHA-256, and `{"do_sample": false, "max_new_tokens": 2048}`.
The `documents` directory must contain `1.json` through `100.json`.

Download `/kaggle/working/qwen3-4b-s008.zip` after generation completes.
Shut down the Kaggle runtime after confirming the download.

## Dual-GPU overnight rerun

The rerun uses smaller 2,500-character chunks to reduce oversized JSON responses.
Each process sees one T4 through `CUDA_VISIBLE_DEVICES` and writes a separate shard directory.

Run this cell from the copied repository at `/kaggle/working/qwen_grounded_code`:

```python
import os
import subprocess
import sys
from huggingface_hub import snapshot_download

CODE = "/kaggle/working/qwen_grounded_code"
INPUT = "/kaggle/working/input.zip"
MODEL = snapshot_download(
    "Qwen/Qwen3-4B-Instruct-2507",
    revision="1b4199c4f36b0cef378bfb12390c18780c18af4c",
)
base = [
    sys.executable,
    "tools/generate_model_proposals.py",
    "--input", INPUT,
    "--model-path", MODEL,
    "--max-chars", "2500",
    "--shard-count", "2",
]
processes = []
for index in range(2):
    environment = os.environ.copy()
    environment["CUDA_VISIBLE_DEVICES"] = str(index)
    environment["PYTHONPATH"] = ".:src"
    processes.append(
        subprocess.Popen(
            base + [
                "--shard-index", str(index),
                "--output", f"/kaggle/working/qwen3-4b-s009-shard-{index}",
            ],
            cwd=CODE,
            env=environment,
        )
    )
codes = [process.wait() for process in processes]
if any(code != 0 for code in codes):
    raise RuntimeError(f"generator failed with exit codes {codes}")
```

After both processes finish, merge and strictly validate all 100 records:

```python
import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, CODE)
from medical_race.model_proposals import prompt_chunks, read_proposal_directory
from tools.audit_sources import read_zip_documents

final = Path("/kaggle/working/qwen3-4b-s009")
documents = final / "documents"
documents.mkdir(parents=True, exist_ok=True)
shards = [Path(f"/kaggle/working/qwen3-4b-s009-shard-{index}") for index in range(2)]
manifests = [json.loads((shard / "manifest.json").read_text()) for shard in shards]
if manifests[0] != manifests[1]:
    raise RuntimeError("shard manifests differ")
shutil.copy2(shards[0] / "manifest.json", final / "manifest.json")
for shard in shards:
    for source in (shard / "documents").glob("*.json"):
        shutil.copy2(source, documents / source.name)

raw_documents = read_zip_documents(Path(INPUT))
proposals = read_proposal_directory(final, raw_documents)
records = [json.loads(path.read_text()) for path in documents.glob("*.json")]
if any(
    record["chunk_count"] != len(prompt_chunks(raw_documents[record["name"]], 2500))
    for record in records
):
    raise RuntimeError("a shard record does not use 2,500-character chunks")
print("Documents:", len(proposals))
print("Chunks:", sum(record["chunk_count"] for record in records))
print("Parse errors:", sum(record["parse_error_count"] for record in records))
print("Proposals:", sum(len(values) for values in proposals.values()))
archive = shutil.make_archive("/kaggle/working/qwen3-4b-s009", "zip", final.parent, final.name)
print("Archive:", archive)
```

Download `/kaggle/working/qwen3-4b-s009.zip` only after strict validation reports 100 documents.

## Google Colab fallback

Enable a GPU runtime and use the same commands from the unpacked repository root.
Replace `/kaggle/working/qwen3-4b-s008` with `/content/qwen3-4b-s008`.
Replace the final packaging command with:

```bash
cd /content && zip -qr qwen3-4b-s008.zip qwen3-4b-s008
```

Download `/content/qwen3-4b-s008.zip`, then shut down the Colab runtime.

## Resume and transfer rules

Rerunning the same command skips only document records that fully validate against their raw input hashes.
An invalid or interrupted document record is regenerated atomically.
Do not edit the manifest or any per-document JSON file.
Do not upload the proposal archive to the competition portal.
Return the archive to the local repository for checksum validation, deterministic grounding, ontology linking, and final submission packaging.
