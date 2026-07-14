# Reliable Dual-GPU Qwen Generation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Split the existing Qwen proposal run safely across two GPU processes and use smaller chunks.

**Architecture:** Extend the existing generator only.
Two CLI processes use deterministic document shards, native CUDA process isolation, and separate resumable output directories that are strictly merged afterward.

**Tech Stack:** Python 3.11 standard library, PyTorch, Transformers 4.51.0, unittest

## Global Constraints

- Preserve raw input text and exact offsets.
- Keep active model parameters at `4,000,000,000 / 9,000,000,000`.
- Do not change proposal acceptance or final output policy.
- Run Python through `.venv` locally.

---

### Task 1: Deterministic process sharding

**Files:**
- Modify: `tests/test_generate_model_proposals.py`
- Modify: `tools/generate_model_proposals.py`

**Interfaces:**
- Consumes: document names validated as `input/<number>.txt`
- Produces: `select_document_shard(documents, shard_index, shard_count)`

- [x] Write a failing test proving two shards are disjoint, exhaustive, and reject invalid shard values.
- [x] Run the focused test and confirm failure.
- [x] Implement numeric-ID modulo selection and CLI flags for shard index and shard count.
- [x] Run focused tests and confirm they pass.

### Task 2: Full verification and Kaggle handoff

**Files:**
- Modify: `docs/qwen_free_gpu_runbook.md`

**Interfaces:**
- Consumes: the two-process CLI
- Produces: exact Kaggle commands for GPU 0 and GPU 1 plus archive validation

- [x] Add concise dual-GPU commands and separate resumable outputs.
- [x] Run `$env:PYTHONPATH='src'; .\.venv\Scripts\python.exe -m unittest discover -s tests -v`.
- [x] Run `.venv\Scripts\python.exe -m compileall -q src tools tests`.
- [x] Inspect `git diff --check` and `git status --short`.
