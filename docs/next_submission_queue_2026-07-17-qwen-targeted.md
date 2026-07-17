# Next Submission Queue, Targeted Qwen

## Hypothesis

Prompt version 2 recovers atomic symptom and laboratory mentions missed by Submission 8 while preserving every stable entity and all 150 candidates.

## Parent and controlled variable

The semantic parent is `local-s008` at score `16.13250`.
The only primary behavior change is the task-focused prompt profile.
The model, revision, strict parser, 2,500-character chunking, grounding, linkers, rules, assertions, and candidate policy remain fixed.

## Local gate

The proposal run must cover all 100 documents and keep parse errors below 20 percent of chunks.
At least 25 new entities must survive deterministic gates across at least 10 documents.
The semantic diff must report zero removals and zero changes to stable text, type, position, assertions, or candidates.
The final output must preserve all 150 candidates and produce zero candidate changes.
Every accepted addition receives manual structural review before a portal ZIP is created.

## Portal decision

Promote only above `16.13250` with component movement consistent with improved mention coverage and unchanged candidate Jaccard.
A failed local gate remains a diagnostic model run and is not numbered or submitted as Submission 10.

## Upgrade boundary

If the organizer upgrade becomes live before the portal run, pause this queue.
Preserve the new official artifacts and execute `docs/post_update_bringup_checklist.md` before adapting or submitting the prompt profile.
