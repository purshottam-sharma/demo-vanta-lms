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
1. ClickUp MCP — fetch task `$ARGUMENTS`. If this fails, try direct REST API via curl using `CLICKUP_API_TOKEN` from `.env`. If both fail, halt with clear error.
2. Postgres MCP — run `SELECT 1`. If this fails, halt.
3. GitHub MCP — verify repo `purshottam-sharma/demo-vanta-lms` is accessible. If not, halt.

Note: If MCP env vars are not loaded (tokens missing), load them from `.env` using `source .env` in bash and use direct REST API calls as fallback.

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

**If figma_url is present — attach Figma screenshot to ClickUp before spawning agents:**
Parse the node-id from figma_url (e.g. `node-id=0-1` → id `0:1`). Then:
```bash
source .env
# Export frame as PNG
IMAGE_URL=$(curl -s "https://api.figma.com/v1/images/$FIGMA_FILE_ID?ids={node_id}&format=png&scale=2" \
  -H "X-Figma-Token: $FIGMA_API_TOKEN" | python3 -c "import sys,json; d=json.load(sys.stdin); print(list(d['images'].values())[0])")
# Download PNG
curl -sL "$IMAGE_URL" -o /tmp/figma-{task_id}.png
# Attach to ClickUp task
curl -s -X POST "https://api.clickup.com/api/v2/task/{task_id}/attachment" \
  -H "Authorization: $CLICKUP_API_TOKEN" \
  -F "attachment=@/tmp/figma-{task_id}.png;filename=figma-design.png;type=image/png"
```
If the export fails, log a warning and continue — do not halt.

Spawn both sub-agents **simultaneously** using the Agent tool:

**Design Agent** (only if figma_url is present):
- Provide: task title, figma_url, task_id, acceptance_criteria (UI-relevant only)
- Instruction: read `agents/design/SKILL.md`, fetch Figma node JSON + download frame PNG, run Claude Vision analysis on PNG, merge JSON measurements + Vision observations into enriched UISpec, self-reflect vs criteria
- Returns: UISpec JSON + `figma_png_path` + `vision_summary` (3-5 bullet points of non-obvious design choices)

**Backend Agent** (only if api_endpoints or DB tables are present):
- Provide: task description, affected tables/columns, api_endpoints, acceptance_criteria (backend-relevant)
- Instruction: read `agents/backend/SKILL.md` and `skills/fastapi-patterns.md` and `skills/postgres-schema.md`, then generate FastAPI router + service + Pydantic models + SQL queries, self-reflect vs acceptance criteria
- Returns: list of GeneratedFile (path, content, language, agent_source="backend")

Save WorkOrder after both complete. `current_step: 2`.

## Step 3 — Frontend Agent
Read `agents/frontend/SKILL.md`.

Spawn Frontend Agent sub-agent:
- Provide: UISpec JSON (from Design Agent), `figma_png_path`, `vision_summary`, API contract (endpoints + Pydantic models from Backend Agent), acceptance_criteria
- Instruction: read `agents/frontend/SKILL.md` and `skills/react-shadcn.md`, generate React pages + components + React Query hooks + TypeScript types using shadcn/ui. Pay close attention to `vision_summary` — these are non-obvious design choices that numbers alone won't convey. Self-reflect vs UISpec + vision_summary + API contract.
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

## Step 5.5 — Visual Diff Agent (feature-ui tasks only)
**Skip this step entirely if `figma_url` is not present or task_type is not `feature-ui`.**

Read `agents/visual-diff/SKILL.md`.

Spawn Visual Diff Agent sub-agent:
- Provide: `figma_png_path` (`/tmp/figma-{task_id}.png`), `task_id`, `route` (primary route from acceptance_criteria, e.g. `/dashboard`), `generated_frontend_files`
- Instruction: read `agents/visual-diff/SKILL.md`, run Playwright screenshot helper, use Claude Vision to compare rendered output vs Figma PNG, generate fix list, route fixes to Frontend Agent, loop until PASSED or max 3 cycles
- Returns: `VisualDiffReport { status, loops, diffs_found_total, diffs_remaining, fixes_applied }`

**If status = PASSED:** proceed to Step 6, include "Visual diff: PASSED (N diffs fixed)" in Checkpoint 1 summary.
**If status = MAX_LOOPS_REACHED:** proceed to Step 6, include remaining diffs in Checkpoint 1 summary so the human can decide.
**If Visual Diff Agent errors (Playwright missing, server won't start):** log warning, skip, proceed to Step 6.

Save WorkOrder. `current_step: 5.5`.

## Step 6 — Human Checkpoint 1
Post to ClickUp task:
- All generated file diffs (file path + full content)
- Test results summary (X passed, Y failed)
- Any Reflector violations that were fixed

Set task status → "in progress".

**Then use the AskUserQuestion tool with exactly these two options:**
- Question: "Tests passed X/Y. Here are the key changes: [list files changed]. Do you approve this code?"
- Header: "Checkpoint 1"
- Option 1 label: "Approve" — description: "Looks good, proceed to Review Agent"
- Option 2 label: "Request changes" — description: "Something needs to change — I'll tell you what"

**If "Approve":**
- Update `agent_code_approved` to true in ClickUp via API
- Proceed to Step 7

**If "Request changes":**
Enter a **conversational hardening loop**:
- Ask: "What needs to change?" and engage in open conversation — the user can describe issues, ask questions, suggest alternatives, or paste examples
- Do NOT rush to spawn agents — first fully understand what they want through back-and-forth dialogue
- When the user is satisfied with the direction and says something like "ok go ahead" / "make that change" / "looks right":
  - Summarise the agreed changes
  - Route fixes to the correct agent(s) by file:
    - Backend files (`apps/api/`, `agents/`) → Backend Agent
    - Frontend files (`apps/web/`, `libs/`) → Frontend Agent
    - Both → spawn both with targeted instructions
  - Re-run: Reflector → Testing (counts toward existing max cycle limits)
  - Push the updated files to the existing branch (same branch, new commit)
  - Post a comment to ClickUp summarising what changed and why
  - Show the user the updated diffs and ask again via AskUserQuestion
- Repeat until the user selects "Approve" — no hard cycle limit on conversation, but max 3 agent re-runs

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

**Then use the AskUserQuestion tool with exactly these two options:**
- Question: "Review score: X/100 (Correctness: A, Completeness: B, Quality: C, Architecture: D, DX: E). Ready to create the PR. Do you approve?"
- Header: "Checkpoint 2"
- Option 1 label: "Approve" — description: "Create the PR now"
- Option 2 label: "Request changes" — description: "Something needs to change before the PR"

**If "Approve":**
- Update `agent_pr_approved` to true in ClickUp via API
- Proceed to Step 9

**If "Request changes":**
Enter the same **conversational hardening loop** as Checkpoint 1:
- Engage in open dialogue to understand what needs to change
- When user confirms direction, route fixes to correct agent(s), re-run Review Agent
- Push updated files to the existing branch as a new commit
- Post ClickUp comment summarising what changed and why
- Show updated score and ask again via AskUserQuestion
- Max 3 agent re-runs (no hard limit on conversation turns)

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

**Then pull the branch locally so the user can test immediately:**
```bash
git fetch origin
git checkout feature/$ARGUMENTS-{slug}
```

Tell the user: "PR created: {url}. Branch checked out locally — you can now run `uv sync` / `npm install` / `nx serve` to test."

## Step 10 — PR Review Agent
Spawn a PR Review Agent sub-agent immediately after the PR is created:

- Provide: PR URL, all generated files, acceptance_criteria, task_type, review score + violations from Step 7
- Instruction:
  1. Re-read all generated files with fresh eyes as a senior engineer doing a real code review
  2. Check for issues NOT already caught by the Review Agent rubric — e.g. security issues, missing edge cases, confusing naming, brittle patterns, anything that would block a real PR approval
  3. For each issue found: post an inline GitHub PR comment on the specific file + line using the GitHub MCP (`create_pull_request_review` with `COMMENT` event)
  4. If no blocking issues: approve the PR using GitHub MCP (`create_pull_request_review` with `APPROVE` event) with a summary comment
  5. If blocking issues exist: request changes using GitHub MCP (`create_pull_request_review` with `REQUEST_CHANGES` event) listing each issue

- After GitHub review is posted:
  - Post a ClickUp comment summarising the review outcome:
    - If approved: "PR Review Agent approved the PR. X inline comments left. **Merge is manual — please do a final review and merge when ready.**"
    - If changes requested: "PR Review Agent requested changes. Issues: [list]. Please review inline comments on the PR before merging."
  - Update ClickUp status → keep "in review" in both cases (merging is always manual)
  - **Never merge the PR** — the agent only reviews and comments, the human always merges

- Then notify the user directly in the conversation:
  - If approved: "PR Review Agent approved ✅. [X] inline comments posted. Do a final read on GitHub and merge when you're happy: {pr_url}"
  - If changes requested: "PR Review Agent flagged issues ⚠️. Inline comments posted on GitHub. Review them at {pr_url} — you decide whether to fix or merge as-is."

Save WorkOrder with `current_step: 10`, `pr_review: "approved"|"changes_requested"`.

## On PR Merge (automated — GitHub Actions)
The workflow `.github/workflows/sync-clickup-on-merge.yml` fires automatically when any PR targeting `main` is merged. No agent action required.

It:
1. Extracts the task ID from the branch name (`feature/{task_id}-{slug}`) or PR title (`[{task_id}]`)
2. Posts a ClickUp comment: PR URL, merged by, timestamp
3. Sets ClickUp task status → `complete`

**Requires**: `CLICKUP_API_TOKEN` added as a GitHub repository secret (Settings → Secrets → Actions).

## Error Handling
- Any sub-agent returns an error → post to ClickUp, save WorkOrder with error, halt
- Check for `status: cancelled` in WorkOrder at the start of every step → if found, halt cleanly
