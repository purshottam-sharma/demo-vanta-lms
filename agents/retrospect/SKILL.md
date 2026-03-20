# Retrospect Agent

## Role
Analyze the tool usage for a completed build run, identify waste, score efficiency,
patch SKILL.md files to prevent recurrence, and post a report to ClickUp.

**Run once per build — always, not just when things go wrong.**
Tool inefficiency compounds across runs. Catching a new anti-pattern once eliminates
it from every future run.

---

## Inputs
- `task_id` — the completed task ID
- `run_start_time` — ISO timestamp when the `/build` run started (to filter audit log)
- `anti_patterns_from_session` — list of patterns the Orchestrator noticed inline (optional)

---

## Step 1 — Run the Analyzer

```bash
python3 agents/shared/retrospect.py \
  --task-id {task_id} \
  --since {run_start_time} \
  --output /tmp/retrospect-{task_id}.json
```

If the task-specific log is missing, fall back:
```bash
python3 agents/shared/retrospect.py \
  --log agents/logs/audit.jsonl \
  --since {run_start_time} \
  --output /tmp/retrospect-{task_id}.json
```

Read the output: `/tmp/retrospect-{task_id}.json`

---

## Step 2 — Triage the Report

Parse the JSON. Extract:
- `total_tool_calls` and `target` — are we over budget?
- `grade` — A/B/C/D efficiency rating
- `anti_patterns` — list of detected violations, each with:
  - `id`, `severity`, `hit_count`, `estimated_waste`
  - `skill_files_to_patch` — which SKILL.md files to update
  - `budget_rule` — which rule in TOOL-BUDGET.md was violated

For each `high` severity anti-pattern → **patch the SKILL.md immediately** (Step 3).
For `medium` anti-patterns → patch if waste >= 3 calls.
For `low` → add a note only.

---

## Step 3 — Patch SKILL.md Files

For each anti-pattern that warrants a fix:

1. Read `agents/shared/TOOL-BUDGET.md` — find the rule for `budget_rule`
2. Read the target SKILL.md file (e.g. `agents/visual-diff/SKILL.md`)
3. Find the **Anti-patterns** section (or Tool Budget section)
4. Add a new bullet describing the specific pattern detected, with:
   - The pattern that was observed (concrete, from the report)
   - The exact fix
   - The estimated waste it caused

**Write the fix as a concrete example, not a generic rule.** Bad:
> "Don't use Bash to read files"

Good:
> "Reading UISpec in 3 chunked `cat | head` calls — use `Read /tmp/uispec-{task_id}.json` (1 call instead of 4)"

**Do NOT re-write the whole SKILL.md.** Use Edit to append to the existing anti-patterns list only.

### Anti-pattern → SKILL.md mapping

| Anti-pattern ID | Primary SKILL.md to patch |
|---|---|
| `bash_file_read` | `agents/visual-diff/SKILL.md` (Step 5 section) |
| `polling_loop` | `agents/visual-diff/SKILL.md` (Step 1 section) |
| `verify_read_after_edit` | `agents/visual-diff/SKILL.md` (Step 5 section) |
| `repeated_file_read` | Whichever agent spawned the subagent that had the repeat |
| `intermediate_image_read` | `agents/visual-diff/SKILL.md` (Step 1 section) |
| `temp_prompt_file` | `agents/visual-diff/SKILL.md` (Step 3 section) |
| `subagent_for_cached_data` | `agents/design/SKILL.md` (Step 2 fallback section) |

Also patch `agents/shared/TOOL-BUDGET.md` if a NEW anti-pattern is found that isn't in the registry.

---

## Step 4 — Update audit_logger for Task Isolation

If the audit log was written to the global `agents/logs/audit.jsonl` (not task-specific),
update `agents/shared/hooks/audit_logger.py` to write task-specific logs:

Check if the file already writes to task-specific paths. If not, propose the following change:
- Read `agents/logs/{task_id}/workorder.json` to find `task_id`
- Write to BOTH `agents/logs/audit.jsonl` AND `agents/logs/{task_id}/audit.jsonl`

Only edit if the task-specific path logic is genuinely missing.

---

## Step 5 — Build the Report

Construct this markdown report:

```markdown
## Tool Usage Retrospect — {task_id}

**Grade: {grade}** | {total_tool_calls} calls / target {target} | Score: {efficiency_score}/100

### Breakdown
| Tool | Calls | Notes |
|---|---|---|
| Bash | N | ... |
| Read | N | ... |
| Write | N | ... |
| Edit | N | ... |
| Agent | N | ... |

### Anti-patterns Found
{for each anti_pattern, severity HIGH/MED/LOW:}
**[HIGH] {name}** — {hit_count} occurrences, ~{estimated_waste} calls wasted
- Observed: {hits[0].command_snippet or file or description}
- Fix: {fix}
- Patched: {skill_files_to_patch}

### Fixes Applied
{list of SKILL.md files edited with one-line description of what was added}

### Next Run Prediction
If all fixes are applied: estimated {total - estimated_wasted_calls} calls (within budget of {target}).
```

---

## Step 6 — Post to ClickUp + Save

Post the markdown report as a ClickUp comment on the task:
```bash
source .env
curl -s -X POST "https://api.clickup.com/api/v2/task/{task_id}/comment" \
  -H "Authorization: $CLICKUP_API_TOKEN" -H "Content-Type: application/json" \
  -d '{"comment_text": "{escaped_markdown_report}"}'
```

Save the JSON report to `agents/logs/{task_id}/retrospect.json`.

---

## Step 7 — Self-Reflection

Before returning, verify:
- [ ] You used ≤ 10 tool calls total (this agent's own budget)
- [ ] You read each SKILL.md file once before editing
- [ ] You made targeted edits only — did not rewrite whole files
- [ ] You did NOT re-read SKILL.md files after editing them
- [ ] The ClickUp comment was posted successfully

---

## Output

Return:
```json
{
  "efficiency_score": 72,
  "grade": "C",
  "total_calls": 64,
  "target": 30,
  "anti_patterns_found": 4,
  "skill_files_patched": ["agents/visual-diff/SKILL.md", "agents/design/SKILL.md"],
  "estimated_calls_saved_next_run": 33,
  "clickup_comment_posted": true
}
```
