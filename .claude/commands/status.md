---
description: Check the current status of an agent workflow for a ClickUp task. Read the persisted WorkOrder and display a human-readable summary.
argument-hint: CU-{task_id}
---

Check the workflow status for ClickUp task `$ARGUMENTS`.

## What to Do

1. Read `agents/logs/$ARGUMENTS/workorder.json`
   - If file does not exist → "No active workflow found for $ARGUMENTS. Run /pm $ARGUMENTS to start."

2. Display a clean status summary:

```
Task:    $ARGUMENTS — {task_title}
Status:  {status}
Step:    {current_step}/9 — {step_name}
Cost:    ${total_cost_usd} (no limit — Claude Code handles billing)

Agents completed:
  ✓/✗  Design Agent    — {result or pending}
  ✓/✗  Backend Agent   — {X files generated}
  ✓/✗  Frontend Agent  — {X files generated}
  ✓/✗  Reflector       — {PASSED / X violations fixed}
  ✓/✗  Testing Agent   — {X tests written, X passing}
  ✓/✗  Review Agent    — {score}/100 (loop {n}/3)
  ✓/✗  GitHub Agent    — {PR URL or pending}

Errors: {list any errors}

Next action: {what the human needs to do, or what is running}
```

3. Also fetch the live task status from ClickUp MCP and show which checkpoint fields are checked.

**Step name reference:**
- 0: Requirements review gate
- 1: Design Agent
- 2: Backend Agent
- 3: Frontend Agent
- 4: Reflector Agent
- 5: Testing Agent
- 6: Awaiting Checkpoint 1 (agent_code_approved)
- 7: Review Agent
- 8: Awaiting Checkpoint 2 (agent_pr_approved)
- 9: GitHub Agent / Complete
