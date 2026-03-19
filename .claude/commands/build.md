---
description: Run the full agentic build pipeline for a groomed ClickUp task. You ARE the Orchestrator — spawn sub-agents for Design, Backend, Frontend, Reflector, Testing, and Review, manage human checkpoints, then create the GitHub PR.
argument-hint: CU-{task_id}
---

You are the **Orchestrator** for Vanta LMS. Execute the full build pipeline for ClickUp task `$ARGUMENTS`.

## Your Inputs
- Task ID: `$ARGUMENTS`
- Field IDs: read `.mcp/clickup-fields.json`
- User mapping: read `.mcp/user-mapping.json`
- Figma config: read `.mcp/figma-config.json`
- WorkOrder (if resuming): read `agents/logs/$ARGUMENTS/workorder.json` if it exists

## Pre-Flight: Resume or Start Fresh
Check if `agents/logs/$ARGUMENTS/workorder.json` exists.
- If it exists → read it, identify `current_step`, resume from that step
- If not → start from Step 0

## Pre-Flight: Health Check
Before anything else, verify all MCP connections are live:
1. ClickUp MCP — fetch task `$ARGUMENTS`. If this fails, halt with clear error.
2. Postgres MCP — run `SELECT 1`. If this fails, halt.
3. GitHub MCP — verify repo `purshottam-sharma/vanta-lms` is accessible. If not, halt.

## Pre-Flight: Gate Check
Read the task from ClickUp. Check `agent_task_approved` custom field.
If false → post comment "Task not yet approved by PM. Run /pm $ARGUMENTS first, then check agent_task_approved." and halt.

## Step 0 — Requirements Review Gate
Read ALL task fields carefully. Check for:
1. **AMBIGUITIES** — anything unclear or open to interpretation?
2. **OPEN QUESTIONS** — decisions not yet made that block development?
3. **MISSING INFO** — required fields empty for this task type?
4. **CONFLICTS** — does anything contradict anything else?

If ALL CLEAR → proceed to Step 1.
If issues found:
- Post structured question list to ClickUp with @mention assignee
- Set task status → "blocked"
- Poll `agent_requirements_approved` every 5 minutes (max 48 hours)
- When approved: re-read task, re-check, then proceed

Save WorkOrder to `agents/logs/$ARGUMENTS/workorder.json` with `current_step: 0`.

## Step 1+2 — Design + Backend Agents (Parallel)
Read the SKILL.md files: `agents/design/SKILL.md` and `agents/backend/SKILL.md`.

Spawn both sub-agents **simultaneously** using the Agent tool:

**Design Agent** (only if figma_url is present):
- Provide: task title, figma_url, acceptance_criteria (UI-relevant only)
- Instruction: read `agents/design/SKILL.md`, then fetch the Figma frame, extract UISpec JSON (components, color tokens, typography, interactions), self-reflect vs Figma + criteria
- Returns: UISpec JSON

**Backend Agent** (only if api_endpoints or DB tables are present):
- Provide: task description, affected tables/columns, api_endpoints, acceptance_criteria (backend-relevant)
- Instruction: read `agents/backend/SKILL.md` and `skills/fastapi-patterns.md` and `skills/postgres-schema.md`, then generate FastAPI router + service + Pydantic models + SQL queries, self-reflect vs acceptance criteria
- Returns: list of GeneratedFile (path, content, language, agent_source="backend")

Save WorkOrder after both complete. `current_step: 2`.

## Step 3 — Frontend Agent
Read `agents/frontend/SKILL.md`.

Spawn Frontend Agent sub-agent:
- Provide: UISpec (from Design Agent), API contract (endpoints + Pydantic models from Backend Agent), acceptance_criteria
- Instruction: read `agents/frontend/SKILL.md` and `skills/react-shadcn.md`, generate React pages + components + React Query hooks + TypeScript types using shadcn/ui, self-reflect vs UISpec + API contract
- Returns: list of GeneratedFile (agent_source="frontend")

Save WorkOrder. `current_step: 3`.

## Step 4 — Reflector Agent
Read `agents/reflector/SKILL.md`.

Spawn Reflector Agent sub-agent:
- Provide: all generated files (backend + frontend combined)
- Instruction: read `agents/reflector/SKILL.md`, check:
  1. Every API endpoint the frontend calls exists in the backend router
  2. TypeScript types match Pydantic model field names and types
  3. Auth headers used by frontend are applied by backend middleware
  4. SQL column names in queries match Pydantic model fields
- Returns: PASSED or list of violations with file + description

If violations found → route fixes to correct agent (by agent_source), re-run Reflector. Max 2 correction cycles.
Save WorkOrder. `current_step: 4`.

## Step 5 — Testing Agent
Read `agents/testing/SKILL.md`.

Spawn Testing Agent sub-agent:
- Provide: all generated files, acceptance_criteria, task type
- Instruction: read `agents/testing/SKILL.md`, write pytest tests (one per endpoint: success, validation error, auth error, not found), write vitest+RTL tests (render, interaction, loading, error states), write Playwright e2e test (primary happy path). Write all files to `agents/staging/$ARGUMENTS/`. Run tests via bash. Parse results. Clean up staging dir.
- Returns: TestResults (passed/failed counts, failure details by agent_source)

If failures → send failures back to originating agent to fix. Max 2 fix cycles.
If still failing after 2 cycles → post failure log to ClickUp, halt, require human fix.
Save WorkOrder. `current_step: 5`.

## Step 6 — Human Checkpoint 1
Post to ClickUp task:
- All generated file diffs (file path + full content)
- Test results summary (X passed, Y failed)
- Any Reflector violations that were fixed
- Instruction: "Review diffs above. Check `agent_code_approved` to continue."

Set task status → "in progress".

Poll `agent_code_approved` with exponential backoff:
- 0–30 min: every 5 min
- 30 min–2 hr: every 15 min
- 2–24 hr: every 30 min
- After 24 hr: post timeout notice, set status → "to do", halt


Save WorkOrder. `current_step: 6`.

## Step 7 — Review Agent (max 3 loops)
Read `agents/review/SKILL.md` and `agents/review/rubric.py`.

Spawn Review Agent sub-agent:
- Provide: all generated files, acceptance_criteria, task description, task type
- Instruction: read `agents/review/SKILL.md`, score across 5 dimensions using the task-type-adaptive rubric (see rubric.py), return score + violations list
- Returns: ReviewReport (score 0-100, violations, passed)

**Scoring thresholds:**
- Score >= 80 → PASS, proceed to Step 8
- Score 60-79 → route violations back to correct agents, re-run Review Agent (max 3 total loops)
- Score < 60 → immediate halt, post violation report to ClickUp, require human fix
- After 3 loops still < 80 → halt, post report, require human fix

Post score report to ClickUp after each loop.
Save WorkOrder. `current_step: 7`.

## Step 8 — Human Checkpoint 2
Post to ClickUp:
- Final review score and dimension breakdown
- "Ready to create PR. Check `agent_pr_approved` to proceed."

Poll `agent_pr_approved` with same backoff as Checkpoint 1.
Save WorkOrder. `current_step: 8`.

## Step 9 — GitHub Agent
Read `agents/github/SKILL.md`.

Spawn GitHub Agent sub-agent:
- Provide: all approved generated files, task_id, task_title, task_type, assignee email
- Instruction: read `agents/github/SKILL.md`, use GitHub MCP to:
  1. Create branch `feature/$ARGUMENTS-{slug}` (or `fix/` for bugs)
  2. Commit each file with message `feat(scope): {description} [$ARGUMENTS]`
  3. Create PR with structured body (score, test results, agent metadata)
  4. Add labels: `agent-generated` + task_type
  5. Request reviewer using `.mcp/user-mapping.json`
- Returns: PR URL

Post PR URL to ClickUp task as a link + comment.
Set ClickUp status → "in review".
Save WorkOrder with `current_step: 9`, `status: done`, `pr_url`.

## Error Handling
- Any sub-agent returns an error → post to ClickUp, save WorkOrder with error, halt
- Check for `status: cancelled` in WorkOrder at the start of every step → if found, halt cleanly
