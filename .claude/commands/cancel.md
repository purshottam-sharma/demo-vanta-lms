---
description: Cancel a running agent workflow. Sets the cancelled flag in the WorkOrder, posts a comment to ClickUp, and cleans up staging files.
argument-hint: CU-{task_id}
---

Cancel the agent workflow for ClickUp task `$ARGUMENTS`.

## What to Do

1. Read `agents/logs/$ARGUMENTS/workorder.json`
   - If not found → "No active workflow for $ARGUMENTS"

2. Update the WorkOrder:
   - Set `status` → `cancelled`
   - Save back to `agents/logs/$ARGUMENTS/workorder.json`

3. Clean up staging files:
   - Delete `agents/staging/$ARGUMENTS/` directory if it exists

4. Post comment to ClickUp task:
   "🚫 Workflow cancelled by developer at step {current_step}. Task returned to backlog."

5. Set ClickUp task status → "to do"


6. Confirm to the developer:
   "Workflow for $ARGUMENTS cancelled. Run /build $ARGUMENTS to restart when ready."

## Note
If a sub-agent is currently mid-execution, it will complete its current action before the cancellation takes effect. The WorkOrder flag is checked at the start of each step in /build.
