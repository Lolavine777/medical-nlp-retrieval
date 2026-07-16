# Three-Person Collaboration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Publish one active handoff page for the three human workstreams and route new teammates to it from onboarding.

**Architecture:** Keep the collaboration setup entirely in documentation.
One dated workstream page holds assignments, branch commands, acceptance gates, and the upgrade freeze, while the existing onboarding page links to it.

**Tech Stack:** Markdown, Git, and the existing Python `unittest` suite.

## Global Constraints

The repository retains one configurable pipeline and one stable `master` baseline.
Only the team lead may integrate cross-cutting changes, create submission configurations, package archives, submit experiments, or edit `docs/submissions.csv`.
No teammate may hard-code Round 1 documents, phrases, spans, candidates, or answers.
The organizer upgrade is not treated as live until the team lead confirms and preserves the new official artifacts.
Raw text, offsets, model budget, provenance, and output-schema rules in `AGENTS.md` remain mandatory.

---

### Task 1: Publish the active workstream handoffs

**Files:**

- Create: `docs/TEAM_WORKSTREAMS_2026-07-16.md`

**Interfaces:**

- Consumes: `docs/superpowers/specs/2026-07-16-three-person-collaboration-design.md`, `docs/TEAM_ONBOARDING.md`, and `docs/post_update_bringup_checklist.md`.
- Produces: one copy-paste handoff for Teammate A, one for Teammate B, one lead workstream, and exact shared Git commands.

- [ ] **Step 1: Create the active handoff page**

Write these sections in order:

1. Current state and the expected 21 July upgrade boundary.
2. Shared setup commands using `git pull --ff-only origin master`, the repository virtual environment, and the full test command.
3. Teammate A ownership, first deliverable, prohibited files, focused tests, and pull-request evidence.
4. Teammate B ownership, first deliverable, prohibited files, focused tests, and pull-request evidence.
5. Team lead ownership and first deliverables.
6. Merge and submission rules.
7. The stop-and-audit procedure that links to `docs/post_update_bringup_checklist.md`.

The handoffs must name only the human team lead and must not present Codex as a team member.

- [ ] **Step 2: Check the handoff page for unsafe scope**

Run:

```powershell
rg -n "Codex|hard-code|pipeline.py|submissions.csv|21 July|post_update_bringup" docs\TEAM_WORKSTREAMS_2026-07-16.md
```

Expected: no `Codex` match, and explicit matches for the ownership boundaries and upgrade freeze.

### Task 2: Route onboarding to the active assignments

**Files:**

- Modify: `docs/TEAM_ONBOARDING.md`

**Interfaces:**

- Consumes: `docs/TEAM_WORKSTREAMS_2026-07-16.md`.
- Produces: a visible active-assignment link before the general reading list.

- [ ] **Step 1: Add the active assignment notice**

Add this paragraph immediately after the opening paragraph:

```markdown
The active three-person assignments, file boundaries, and Git workflow are in [Team Workstreams, 16 July 2026](TEAM_WORKSTREAMS_2026-07-16.md).
Read that page before choosing a task from the general list below.
```

- [ ] **Step 2: Verify documentation and the repository**

Run:

```powershell
git diff --check
rg -n "TEAM_WORKSTREAMS_2026-07-16.md" docs\TEAM_ONBOARDING.md
$env:PYTHONPATH = "src;."
$env:PYTHONIOENCODING = "utf-8"
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Expected: no whitespace errors, one onboarding link, and `Ran 157 tests` followed by `OK`.

- [ ] **Step 3: Commit and push the verified baseline**

Run:

```powershell
git add docs\TEAM_WORKSTREAMS_2026-07-16.md docs\TEAM_ONBOARDING.md docs\superpowers\plans\2026-07-16-three-person-collaboration.md
git diff --cached --check
git commit -m "docs: add team workstream handoffs"
git push origin master
```

Expected: the commit succeeds, `master` is pushed to `origin`, and the unrelated untracked organizer and notebook artifacts remain untouched.
