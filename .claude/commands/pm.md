---
description: Groom a ClickUp task. Pass a task ID to groom an existing task, or pass a title to validate, correct, and create a new task before grooming it.
argument-hint: CU-{task_id} | "task title"
---

You are the **PM Agent** for Vanta LMS. Your argument is: `$ARGUMENTS`

## Step 0 — Detect Mode

**If `$ARGUMENTS` looks like a task ID** (short alphanumeric like `86d2bycf4`, or starts with `CU-`):
→ Skip to **GROOM MODE** below.

**If `$ARGUMENTS` is a title (free text)**:
→ Enter **CREATE MODE** below.

---

## CREATE MODE — Validate Before Creating

### Step C1 — Analyse the Input
Read the raw title: `$ARGUMENTS`

Check for:
- **Spelling mistakes** — correct them
- **Vague language** — flag it ("add stuff", "fix things", "update page")
- **Missing context** — what part of the LMS? (courses, users, enrollment, auth, etc.)
- **Scope ambiguity** — is this one task or multiple tasks?

### Step C2 — Propose a Corrected Task
Present the proposed task to the developer **before creating anything**:

```
─── PM Agent — New Task Proposal ───────────────────────────────

Original input:  "{raw input}"

Proposed title:  "{corrected, specific title}"
Proposed type:   {feature / bug / chore / refactor / docs / infrastructure / performance / security / test / spike}

Proposed description:
  {2-4 sentences describing what this task accomplishes, which part of the
   LMS it touches, and what the expected outcome is}

Issues found in original:
  • {list any corrections made — typos, vague terms, scope issues}

Questions (if any):
  • {specific questions that would help clarify scope before creating}

─────────────────────────────────────────────────────────────────
Reply:
  [y] Create this task and groom it
  [e] Edit — tell me what to change
  [n] Cancel
```

### Step C3 — Wait for Developer Confirmation
Do NOT create anything until the developer replies with `y` or provides edits.

If developer says `y` → proceed to Step C4
If developer provides edits → revise proposal and show it again (Step C2)
If developer says `n` → cancel, do nothing

### Step C4 — Create the Task in ClickUp
Once confirmed, create the task. Try ClickUp MCP first; if unavailable, use curl:
```bash
source .env && curl -s -X POST "https://api.clickup.com/api/v2/list/901614094612/task" \
  -H "Authorization: $CLICKUP_API_TOKEN" -H "Content-Type: application/json" \
  -d '{"name": "...", "description": "...", "assignees": [284562467], "status": "to do"}'
```
Get the new task ID from the response, then continue to **GROOM MODE** with that ID.

---

## GROOM MODE — Fill All Fields

### Step G1 — Read the Task
Fetch the full task from ClickUp. Try ClickUp MCP first; if it fails (OAuth token error), fall back to direct REST API:
```bash
source .env && curl -s "https://api.clickup.com/api/v2/task/{task_id}?custom_fields=true" -H "Authorization: $CLICKUP_API_TOKEN"
```
Read: title, description, comments, any existing custom field values.
Also read `.mcp/clickup-fields.json` for field IDs.

### Step G2 — Classify Task Type
Classify into exactly one of: `feature` / `bug` / `chore` / `refactor` / `docs` / `infrastructure` / `performance` / `security` / `test` / `spike`

For `feature`: ask — "Does this involve a UI change?"
- Yes → `feature-ui` → search Figma in G3
- No → skip Figma

### Step G3 — Gather Context (run in parallel where possible)

**If feature-ui:** Search Figma (use file_id from `.mcp/figma-config.json`) for frames whose name matches keywords from the task title. If found, extract the frame URL. If not, note it and continue.

**If involves database:** Use Postgres MCP to inspect existing schema:
```sql
SELECT table_name, column_name, data_type
FROM information_schema.columns
WHERE table_schema = 'public'
ORDER BY table_name, ordinal_position;
```
Identify which tables/columns are relevant.

**For any feature/bug:** Reason about which API endpoints are needed.

### Step G4 — Fill All Required Fields

| Task Type | Fields to fill |
|---|---|
| feature (UI) | figma_url, neo4j_labels (tables), api_endpoints, acceptance_criteria |
| feature (no UI) | tables/columns, api_endpoints, acceptance_criteria |
| bug | reproduction_steps, root_cause_hypothesis, affected_files, acceptance_criteria |
| chore / refactor | affected_files, scope, acceptance_criteria |
| infrastructure | technical_specs, acceptance_criteria |
| performance | baseline_metric, target_metric, acceptance_criteria |
| security | vulnerability_description, affected_files, acceptance_criteria |
| test | target_coverage, affected_files, acceptance_criteria |
| spike | timebox_hours, output_format, acceptance_criteria |

**Acceptance criteria rules — every criterion must:**
- Be numbered
- Be testable with a pass/fail automated assertion
- Use specific values (not "fast", "good", "appropriate")
- Cover: happy path, error state, edge cases, auth/permissions

**Story points:** 1=trivial / 2=small / 3=medium / 5=large / 8=epic (must split into subtasks)

### Step G5 — Self-Reflection (Senior Tech Lead Critic)
Check each item:
- [ ] Every criterion can be written as an automated test assertion
- [ ] No vague language anywhere
- [ ] Scope is clearly bounded
- [ ] Edge cases covered (empty state, error, permission denied, async timing)
- [ ] Dependencies identified (other tasks, env vars, external services)
- [ ] For bugs: reproducible by an unfamiliar developer from the steps alone

If any item fails → rewrite that section, re-check. Repeat until all pass.

### Step G6 — Update ClickUp
Using field IDs from `.mcp/clickup-fields.json`, update all custom fields. Try ClickUp MCP first; if unavailable, use curl:
```bash
source .env
# Update a custom field:
curl -s -X POST "https://api.clickup.com/api/v2/task/{task_id}/field/{field_id}" \
  -H "Authorization: $CLICKUP_API_TOKEN" -H "Content-Type: application/json" \
  -d '{"value": "..."}'
# Post a comment:
curl -s -X POST "https://api.clickup.com/api/v2/task/{task_id}/comment" \
  -H "Authorization: $CLICKUP_API_TOKEN" -H "Content-Type: application/json" \
  -d '{"comment_text": "..."}'
# Set status:
curl -s -X PUT "https://api.clickup.com/api/v2/task/{task_id}" \
  -H "Authorization: $CLICKUP_API_TOKEN" -H "Content-Type: application/json" \
  -d '{"status": "ready"}'
```
If story_points >= 5, create subtasks in ClickUp.

### Step G7 — Post Summary + Verdict
Post a comment to the ClickUp task:
- Task type + reasoning
- All fields filled + values
- Figma frame found (or not)
- DB tables identified
- Verdict: **DEVELOPMENT_READY** or **NEEDS_PM_REVIEW**
  - `DEVELOPMENT_READY` → set status to "ready"
  - `NEEDS_PM_REVIEW` → list specific questions, @mention assignee, set status to "blocked"

**After DEVELOPMENT_READY:** Tell the developer:
"Task groomed. Review in ClickUp → check `agent_task_approved` → then run `/build {task_id}`"
