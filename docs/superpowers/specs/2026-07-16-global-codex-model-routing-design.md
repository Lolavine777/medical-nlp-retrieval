# Global Codex Model Routing

## Goal

Configure Codex globally so the root agent uses GPT-5.6 Sol with high reasoning for technical leadership and delegated implementation uses GPT-5.6 Luna with medium reasoning.
Keep authority with Sol while using Luna for faster, cheaper execution.

## Roles

Sol owns requirements, architecture, design, task decomposition, acceptance criteria, evals, test cases, and final review.
Before delegating non-trivial implementation, Sol must create or specify a failing test, eval, or explicit verification check.

Luna receives bounded implementation instructions and may edit code, run prescribed checks, diagnose direct failures, and report evidence.
Luna must not choose architecture, change requirements, weaken tests, redefine acceptance criteria, or make product decisions.
When instructions are ambiguous or conflict with the codebase, Luna must stop and return the ambiguity to Sol.

Terra is not assigned a standing role because design and code strategy belong to Sol.

## Global Configuration

Keep the existing global root settings at `gpt-5.6-sol` with `model_reasoning_effort = "high"`.
Override the built-in `default` and `worker` subagents with personal agent files under `~/.codex/agents/` that select `gpt-5.6-luna` with `model_reasoning_effort = "medium"`.
Add global agent guidance under `~/.codex/AGENTS.md` that defines the Sol-to-Luna workflow and authorizes automatic delegation only after Sol supplies bounded acceptance checks.

## Workflow

1. Sol analyzes the request and makes all high-level decisions.
2. Sol writes or specifies the test, eval, or verification check that defines success.
3. Sol delegates a bounded implementation task to Luna.
4. Luna implements the smallest compliant change and runs the prescribed checks.
5. Luna reports the diff, commands, results, and any ambiguity without changing the specification.
6. Sol reviews the implementation and evidence, then accepts, revises, or rejects the work.

Trivial tasks may remain with Sol when delegation would cost more than the work itself.

## Verification

Validate the global configuration with Codex strict configuration parsing.
Start a fresh Codex task and confirm that the root reports Sol-high while delegated `default` and `worker` tasks report Luna-medium.
Use a small test-first implementation prompt to confirm Luna follows the supplied check and escalates an intentionally ambiguous decision.
