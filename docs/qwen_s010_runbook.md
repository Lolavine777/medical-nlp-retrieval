# Submission 10 Manual Kaggle Runbook

This run produces model proposal evidence, not a competition submission.
Use a Kaggle notebook with two T4 GPUs and internet enabled while cloning the repository and downloading the pinned model.

Run exactly the four cells below.
Do not add accumulated debugging cells to the notebook.

## Cell 1: Get the current verified code

```python
from pathlib import Path
import subprocess

repo = Path("/kaggle/working/medical-nlp-retrieval")
url = "https://github.com/Lolavine777/medical-nlp-retrieval.git"
if not repo.exists():
    subprocess.run(["git", "clone", url, str(repo)], check=True)
subprocess.run(["git", "-C", str(repo), "switch", "master"], check=True)
subprocess.run(
    ["git", "-C", str(repo), "pull", "--ff-only", "origin", "master"],
    check=True,
)
subprocess.run(["git", "-C", str(repo), "rev-parse", "HEAD"], check=True)
```

Record the printed commit with the returned artifacts.

## Cell 2: Install and prepare the canonical input

```python
import os
import subprocess
import sys
from pathlib import Path

repo = Path("/kaggle/working/medical-nlp-retrieval")
subprocess.run(
    [
        sys.executable,
        "-m",
        "pip",
        "install",
        "-r",
        str(repo / "requirements-model.txt"),
    ],
    check=True,
)
os.chdir(repo)
sys.path[:0] = [str(repo), str(repo / "src")]
from tools.run_kaggle_s009 import prepare_input_zip

input_zip = prepare_input_zip(
    Path("/kaggle/input"),
    Path("/kaggle/working/input.zip"),
)
print("Code:", repo)
print("Input ZIP:", input_zip)
```

The input preparation must report `/kaggle/working/input.zip` without ambiguity errors.

## Cell 3: Run the ten-document smoke shard

```python
command = """CUDA_VISIBLE_DEVICES=0 PYTHONPATH=.:src python tools/generate_model_proposals.py \
  --input /kaggle/working/input.zip \
  --output /kaggle/working/qwen3-4b-s010-smoke \
  --diagnostics-output /kaggle/working/qwen3-4b-s010-smoke-diagnostics \
  --prompt-version 2 \
  --max-chars 2500 \
  --shard-index 0 \
  --shard-count 10"""
subprocess.run(command, shell=True, check=True, cwd=repo)
```

Stop after this cell.
Send the final summary JSON to the team lead before running Cell 4.

The smoke gate requires:

- exactly 10 documents;
- parse errors below 20 percent of chunks;
- only symptom and laboratory proposal types;
- no systematic whole-line, heading, metadata, or procedure proposals in the diagnostics.

## Cell 4: Run the full dual-GPU job after approval

```python
command = """PYTHONPATH=.:src python tools/run_kaggle_s009.py \
  --input-root /kaggle/input \
  --work-root /kaggle/working \
  --run-name qwen3-4b-s010 \
  --prompt-version 2"""
subprocess.run(command, shell=True, check=True, cwd=repo)
```

After the final JSON reports 100 documents, download both:

- `/kaggle/working/qwen3-4b-s010.zip`;
- `/kaggle/working/qwen3-4b-s010-diagnostics.zip`.

Return both archives and the final JSON to the team lead.
Never upload either proposal archive to the competition portal.
The portal accepts only the locally rebuilt and preflighted final output archive.

## Offline replay of a completed run

The raw Qwen proposal and diagnostics archives are evidence artifacts, not portal inputs.
Replay them locally to retain valid siblings from imperfect chunks without another model run:

```powershell
$env:PYTHONPATH = "src;."
$env:PYTHONIOENCODING = "utf-8"
.\.venv\Scripts\python.exe tools\replay_model_diagnostics.py `
  --input input.zip `
  --proposals outputs\kaggle\qwen3-4b-s010.zip `
  --diagnostics outputs\kaggle\qwen3-4b-s010-diagnostics.zip `
  --output outputs\model_proposals\qwen3-4b-s010-salvaged
```

The replay command must validate 100 documents and report its recovered and rejected item counts.
Use the replayed directory for the local build, diff, and submission preflight commands below.
Never upload the raw Qwen archive or diagnostics archive.

## Local return path

After the proposal archive is returned and extracted under `outputs/model_proposals/qwen3-4b-s010`, the team lead runs:

```powershell
$env:PYTHONPATH = "src;."
$env:PYTHONIOENCODING = "utf-8"
.\.venv\Scripts\python.exe tools\build_submission.py --input input.zip --config configs\submissions\10_qwen_targeted.json --model-proposals outputs\model_proposals\qwen3-4b-s010 --output outputs\submissions\10_qwen_targeted.zip --report outputs\submissions\10_qwen_targeted.report.json
.\.venv\Scripts\python.exe tools\diff_submissions.py outputs\submissions\08_qwen_grounded.zip outputs\submissions\10_qwen_targeted.zip --output outputs\submissions\08_qwen_grounded_to_10_qwen_targeted.diff.json
.\.venv\Scripts\python.exe tools\validate_submission.py --input input.zip outputs\submissions\10_qwen_targeted.zip
```

These local commands are not Kaggle cells.
Do not build or upload Submission 10 until its local promotion gate passes.
