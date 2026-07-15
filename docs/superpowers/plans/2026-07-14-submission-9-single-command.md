# Submission 9 Single-Command Kaggle Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the debugging notebook with one tested Submission 9 Kaggle runner and a minimal notebook.

**Architecture:** Keep the existing model generator unchanged and add one standard-library orchestration script around it.
The notebook only locates the mounted repository, installs pinned requirements, and runs the script in the foreground.

**Tech Stack:** Python 3.11 standard library, Hugging Face Hub, existing Transformers/PyTorch generator, unittest, Jupyter notebook JSON

## Global Constraints

- Preserve canonical raw bytes and exact offsets.
- Keep the pinned 4B Qwen model as the only active model.
- Do not change entity acceptance policy or create a portal artifact.
- Use two separate GPU processes and separate resumable output shards.
- Run local Python through `.venv`.

---

### Task 1: Input preparation and shard merge

**Files:**
- Create: `tools/run_kaggle_s009.py`
- Create: `tests/test_run_kaggle_s009.py`

- [ ] Write failing tests for one canonical text directory, ambiguous sources, and strict two-shard merge.
- [ ] Run the focused tests and confirm the expected missing imports fail.
- [ ] Implement the minimum input preparation and merge functions.
- [ ] Run the focused tests and confirm they pass.

### Task 2: Worker orchestration

**Files:**
- Modify: `tools/run_kaggle_s009.py`
- Modify: `tests/test_run_kaggle_s009.py`

- [ ] Write a failing test proving all worker exit codes are collected before failure is raised.
- [ ] Implement two-process launch, log files, progress polling, and exit-code reporting.
- [ ] Run the focused tests and confirm they pass.

### Task 3: Minimal notebook and handoff

**Files:**
- Create: `notebooks/submission9_kaggle.ipynb`
- Modify: `docs/qwen_free_gpu_runbook.md`

- [ ] Add a two-cell notebook that installs requirements and invokes the runner in the foreground.
- [ ] Replace the manual dual-GPU runbook block with the single command.
- [ ] Validate notebook JSON and run the full repository suite, compilation, and diff check.
- [ ] Commit and package the code ZIP from the verified commit.
