---
description: Resume a crashed or failed workflow from the last saved checkpoint, or force restart from a specific step.
argument-hint: CU-{task_id} [--from-step N]
---

Resume the agent workflow for ClickUp task `$ARGUMENTS`.

## What to Do

1. Parse the arguments: task ID and optional `--from-step N`

2. Read `agents/logs/$ARGUMENTS/workorder.json`
   - If file does not exist → "No saved WorkOrder for $ARGUMENTS. Run /build $ARGUMENTS to start fresh."

3. If `--from-step N` was provided:
   - Update `current_step` in the WorkOrder to N
   - Save the WorkOrder
   - Post to ClickUp: "Workflow restarted from step N by developer"

4. Run `/build $ARGUMENTS` — it will automatically read the WorkOrder and resume from `current_step`

## Step Reference

| N | Step |
|---|---|
| 0 | Requirements review gate |
| 1 | Design Agent |
| 2 | Backend Agent |
| 3 | Frontend Agent |
| 4 | Reflector Agent |
| 5 | Testing Agent |
| 6 | Human Checkpoint 1 (poll agent_code_approved) |
| 7 | Review Agent |
| 8 | Human Checkpoint 2 (poll agent_pr_approved) |
| 9 | GitHub Agent |

## When to Use --from-step
- A specific agent produced bad output → re-run from that step
- You manually edited a generated file → re-run from the Review step (7)
- A checkpoint was accidentally approved → re-run from the agent step before it
