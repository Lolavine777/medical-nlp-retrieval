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
