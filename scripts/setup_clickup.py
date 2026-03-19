"""
One-time ClickUp setup script.
Creates all custom fields and implementation tasks for Vanta LMS.
Run from project root: python scripts/setup_clickup.py
"""

import json
import time
import urllib.request
import urllib.error

API_TOKEN = "pk_284562467_9YG78Z5VITDB6MWPOMJUERG3Q40JHUFG"
LIST_ID   = "901614094612"
ASSIGNEE  = 284562467  # Purshottam

HEADERS = {
    "Authorization": API_TOKEN,
    "Content-Type": "application/json",
}


def api(method: str, path: str, body: dict | None = None) -> dict:
    url = f"https://api.clickup.com/api/v2{path}"
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(url, data=data, headers=HEADERS, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        err = e.read().decode()
        print(f"  ERROR {e.code}: {err[:200]}")
        return {}


def create_field(name: str, field_type: str, type_config: dict | None = None) -> str | None:
    body = {"name": name, "type": field_type}
    if type_config:
        body["type_config"] = type_config
    result = api("POST", f"/list/{LIST_ID}/field", body)
    field_id = result.get("id")
    print(f"  {'✓' if field_id else '✗'} {name} ({field_type}) → {field_id}")
    return field_id


def create_task(title: str, description: str, priority: int = 3) -> str | None:
    body = {
        "name": title,
        "description": description,
        "assignees": [ASSIGNEE],
        "priority": priority,  # 1=urgent 2=high 3=normal 4=low
        "status": "to do",
    }
    result = api("POST", f"/list/{LIST_ID}/task", body)
    task_id = result.get("id")
    print(f"  {'✓' if task_id else '✗'} [{task_id}] {title}")
    return task_id


# ── Step 1: Custom Fields ─────────────────────────────────────────────────────

print("\n── Creating custom fields ──────────────────────────────────────────")

TASK_TYPES = [
    "feature", "bug", "chore", "refactor", "docs",
    "infrastructure", "performance", "security", "test", "spike"
]

fields = {}

fields["task_type"] = create_field(
    "task_type", "drop_down",
    {"options": [{"name": t, "orderindex": i} for i, t in enumerate(TASK_TYPES)]}
)
time.sleep(0.3)

fields["figma_url"] = create_field("figma_url", "url")
time.sleep(0.3)

fields["neo4j_labels"] = create_field("neo4j_labels", "text")
time.sleep(0.3)

fields["api_endpoints"] = create_field("api_endpoints", "text")
time.sleep(0.3)

fields["acceptance_criteria"] = create_field("acceptance_criteria", "text")
time.sleep(0.3)

fields["reproduction_steps"] = create_field("reproduction_steps", "text")
time.sleep(0.3)

fields["root_cause_hypothesis"] = create_field("root_cause_hypothesis", "text")
time.sleep(0.3)

fields["affected_files"] = create_field("affected_files", "text")
time.sleep(0.3)

fields["story_points"] = create_field("story_points", "number")
time.sleep(0.3)

fields["agent_task_approved"] = create_field("agent_task_approved", "checkbox")
time.sleep(0.3)

fields["agent_requirements_approved"] = create_field("agent_requirements_approved", "checkbox")
time.sleep(0.3)

fields["agent_code_approved"] = create_field("agent_code_approved", "checkbox")
time.sleep(0.3)

fields["agent_pr_approved"] = create_field("agent_pr_approved", "checkbox")
time.sleep(0.3)


# ── Step 2: Implementation Tasks ─────────────────────────────────────────────

print("\n── Creating implementation tasks ───────────────────────────────────")

TASKS = [
    (
        "Setup: Nx monorepo + Python environment",
        """Initialize the Nx monorepo with apps/api (FastAPI), apps/web (React), and libs/.
Set up uv for Python workspace management.
Configure pyproject.toml for the agents/ package.
Add .gitignore covering .env, agents/staging/, agents/logs/, __pycache__, node_modules.""",
        2,
    ),
    (
        "Build: agents/shared/models.py — core data contracts",
        """Create the central Pydantic data models that every agent communicates through.
Includes: WorkOrder, GeneratedFile, UISpec, ReviewReport, TaskType, TaskStatus, AgentSource enums.
All 4 human checkpoint fields must be present on WorkOrder.
This is the contract everything else builds to — no agent code should be written before this.""",
        1,
    ),
    (
        "Build: agents/shared — infrastructure layer",
        """Build the shared infrastructure modules:
- persistence.py: WorkOrder serialize/deserialize to agents/logs/{task_id}/workorder.json
- cost_tracker.py: record_usage() per API call, enforce AGENT_MAX_COST_USD budget
- logging.py: structured JSON logging per task to agents/logs/{task_id}.jsonl
- health_check.py: pre-flight ping of ClickUp, Neo4j, GitHub, Figma connections
- mcp_clients.py: thin Python wrappers around MCP tool calls
- component_scanner.py: scan libs/ui/ for existing shadcn components
- status.py: /status command handler — reads WorkOrder, prints human-readable summary""",
        2,
    ),
    (
        "Build: agents/shared/hooks — safety guardrails",
        """Build the Claude Code hook scripts (called by settings.json pre/post tool use):
- bash_guard.py: block dangerous shell patterns (rm -rf, curl | bash, kill -9, etc.)
- neo4j_guard.py: block write Cypher keywords (CREATE, MERGE, DELETE, SET, REMOVE, DROP)
- github_guard.py: block push to main/develop, force push, branch/repo deletion
- audit_logger.py: append every tool call as JSON line to agents/logs/{task_id}.jsonl
Each script reads tool call context from stdin and exits 0 (allow) or 1 (block).""",
        2,
    ),
    (
        "Build: skills/ — agent knowledge base",
        """Write all 6 skill reference documents loaded as cached system prompts:
- skills/nx-monorepo.md: Nx commands, project.json targets, tag conventions, affected graph
- skills/neo4j-schema.md: node/rel naming, Cypher patterns, constraints, index strategy
- skills/fastapi-patterns.md: router structure, DI, auth middleware, error format, async patterns
- skills/react-shadcn.md: shadcn/ui components, React Query, form patterns, Tailwind conventions
- skills/neo4j-auth.md: JWT flow, role mapping, Neo4j auth plugin config
- skills/clickup-workflow.md: status lifecycle, custom field IDs, priority meanings, checkpoint flow""",
        2,
    ),
    (
        "Build: agents/pm_agent — PM Agent",
        """Build the PM Agent that grooms raw ClickUp tasks into dev-ready specs.
Entry: python -m agents.pm_agent <task_id>
Modules:
- pm_agent.py: entry point, loads env, calls skill with extended thinking (budget_tokens=8000)
- task_classifier.py: classify into 10 task types, ask sub-question for UI vs no-UI features
- figma_searcher.py: search Figma file for frames matching task title keywords
- schema_analyzer.py: query Neo4j labels list, infer relevant labels from description
- endpoint_planner.py: reason about required API endpoints from requirements
- criteria_writer.py: write numbered, testable acceptance criteria (each = automated assertion)
- bug_analyzer.py: extract reproduction steps + root cause hypothesis
- task_reflector.py: self-reflection as Senior Tech Lead — DEVELOPMENT_READY or NEEDS_PM_REVIEW
SKILL.md must be loaded with cache_control: ephemeral.""",
        2,
    ),
    (
        "Build: agents/design — Design Agent",
        """Build the Design Agent that converts Figma frames into structured UISpec JSON.
Entry: called by Orchestrator as async API call (not standalone).
Modules:
- design_agent.py: system prompt from SKILL.md (cached), receives figma_url + acceptance_criteria
- figma_parser.py: extract components, color tokens, typography, interactions from Figma frame
Self-reflection: after generating UISpec, switch to critic prompt and verify vs Figma + acceptance criteria.
Returns UISpec via forced tool_use structured output.""",
        3,
    ),
    (
        "Build: agents/backend — Backend Agent",
        """Build the Backend Agent that generates FastAPI + Neo4j code from the WorkOrder.
Entry: called by Orchestrator in parallel with Design Agent.
Modules:
- backend_agent.py: system prompt from SKILL.md + skills/fastapi-patterns.md + skills/neo4j-schema.md (all cached)
- fastapi_generator.py: generate router, service, Pydantic models, Neo4j queries
- neo4j_schema_reader.py: inspect existing schema via Neo4j MCP (read-only)
Self-reflection: after generating, verify code vs acceptance criteria (backend-relevant only).
Returns list[GeneratedFile] with agent_source='backend' via forced tool_use.""",
        3,
    ),
    (
        "Build: agents/frontend — Frontend Agent",
        """Build the Frontend Agent that generates React + shadcn/ui components.
Entry: called by Orchestrator AFTER Design + Backend complete (requires both outputs).
Modules:
- frontend_agent.py: receives UISpec + API contract + acceptance_criteria
- react_generator.py: generate React pages, components, React Query hooks, TypeScript types
Self-reflection: verify components vs UISpec + API contract (are all endpoints called actually implemented?).
Uses component_scanner.py output to avoid re-creating existing shadcn components.
Returns list[GeneratedFile] with agent_source='frontend' via forced tool_use.""",
        3,
    ),
    (
        "Build: agents/reflector — Reflector Agent",
        """Build the Reflector Agent — Senior Full-Stack integration reviewer.
Entry: called by Orchestrator after all 3 generators complete.
Modules:
- reflector_agent.py: receives all generated_files, checks cross-system consistency
- consistency_checks.py: rules engine —
  1. Every API endpoint the frontend calls must exist in backend router
  2. TypeScript types must match Pydantic model field names and types
  3. Auth headers used by frontend must be applied by backend middleware
  4. Neo4j property names in Cypher must match Pydantic model field names
If violations found: return them with file + line context so Orchestrator can route fixes.""",
        3,
    ),
    (
        "Build: agents/testing — Testing Agent",
        """Build the Testing Agent that writes and executes tests against generated code.
Entry: called by Orchestrator after Reflector passes.
Modules:
- testing_agent.py: orchestrates test generation + execution
- pytest_writer.py: generate pytest tests (success, validation error, auth error, not found per endpoint)
- vitest_writer.py: generate vitest + RTL tests (render, interaction, loading, error states)
- playwright_writer.py: generate Playwright e2e test for primary happy path
- test_runner.py: write to agents/staging/{task_id}/, run tests in parallel, parse results, clean up
Failure handling: group failures by backend/frontend/e2e, send back to originating agent (max 2 cycles).
Staging directory must always be cleaned up in a finally block.""",
        2,
    ),
    (
        "Build: agents/review — Review Agent",
        """Build the Review Agent — Evaluator-Optimizer final quality gate.
Entry: called by Orchestrator after Human Checkpoint 1.
Modules:
- review_agent.py: receives all generated_files + acceptance_criteria + task_description
- rubric.py: task-type-adaptive scoring (Correctness, Convention, Tests, Security, Accessibility)
  Pass threshold: 80. Score < 60: immediate halt. 60-79: revise. Max 3 loops.
Violation routing: use agent_source on GeneratedFile to route fixes to correct agent.
Returns ReviewReport (score, loop_count, violations, passed) via forced tool_use.""",
        2,
    ),
    (
        "Build: agents/github — GitHub Agent",
        """Build the GitHub Agent that creates the branch, commits, and opens the PR.
Entry: called by Orchestrator after Human Checkpoint 2.
Modules:
- github_agent.py: uses claude-haiku-4-5-20251001 (cheapest — mechanical task)
  1. Create branch: feature/CU-{id}-{slug} or fix/CU-{id}-{slug}
  2. Commit each GeneratedFile with message: feat(scope): description [CU-{id}]
  3. Create PR with structured body (score, test results, agent metadata)
  4. Add labels: agent-generated + {task_type}
  5. Request reviewer using user-mapping.json (ClickUp email → GitHub username)
  6. Post PR URL back to ClickUp task as a link + comment
  7. Set ClickUp status → In Review""",
        3,
    ),
    (
        "Build: agents/webhooks — GitHub webhook server",
        """Build the FastAPI webhook server that syncs GitHub events back to ClickUp.
- github_webhook.py: POST /webhook endpoint, validates GitHub signature header
  Events handled:
  - pull_request.opened → post PR URL to ClickUp task
  - check_run.completed (failed) → post CI failure to ClickUp + @mention assignee
  - pull_request_review.submitted (approved) → resume Orchestrator polling
  - pull_request.closed (merged) → set ClickUp task → complete + post merge comment
  - pull_request.closed (not merged) → notify ClickUp + @mention assignee
- README.md: ngrok/cloudflared setup for local dev, production deployment options""",
        3,
    ),
    (
        "Build: agents/orchestrator — Orchestrator (main coordinator)",
        """Build the Orchestrator — the last agent, wires everything together.
Entry: python -m agents.orchestrator <task_id> [--from-step N]
Modules:
- main.py: entry point, loads .env, validates task is approved, runs pre-flight health check
- orchestrator.py: full pipeline —
  Step -1: health check (abort if any MCP unreachable)
  Step 0: requirements review gate (post to ClickUp if ambiguous, wait for approval)
  Steps 1-2: asyncio.gather(design_agent, backend_agent) — parallel
  Step 3: frontend_agent (sequential — needs both outputs)
  Step 4: reflector_agent
  Step 5: testing_agent (with staging directory)
  Step 6: Human Checkpoint 1 (poll agent_code_approved with exponential backoff)
  Step 7: review_agent (loop up to 3x, route violations back to correct agent)
  Step 8: Human Checkpoint 2 (poll agent_pr_approved)
  Step 9: github_agent
- work_order.py: WorkOrder state machine, step tracking, crash recovery (read/write workorder.json)
Cost enforcement: halt if total_cost_usd > AGENT_MAX_COST_USD at any step.""",
        1,
    ),
    (
        "Setup: end-to-end pipeline test",
        """Run the full agent pipeline on a real ClickUp task to verify everything works.
Verification checklist:
1. /pm on a test task → DEVELOPMENT_READY verdict → custom fields populated in ClickUp
2. agent_task_approved checked → /build triggered
3. Pre-flight health check passes (all 4 MCP services reachable)
4. Design + Backend agents run in parallel, outputs in WorkOrder
5. Frontend Agent runs after both complete
6. Reflector passes (no contract violations)
7. Testing Agent writes tests to staging, runs them, staging cleaned up
8. ClickUp comment posted with diffs + test results
9. agent_code_approved checked → Review Agent runs, score >= 80
10. agent_pr_approved checked → GitHub PR created with correct branch name
11. PR URL posted to ClickUp task
12. Total cost under $15.00 budget""",
        2,
    ),
]

task_ids = []
for title, desc, priority in TASKS:
    tid = create_task(title, desc, priority)
    if tid:
        task_ids.append(tid)
    time.sleep(0.4)  # rate limit

print(f"\n── Done ────────────────────────────────────────────────────────────")
print(f"Custom fields created: {sum(1 for v in fields.values() if v)}/{len(fields)}")
print(f"Tasks created: {len(task_ids)}/{len(TASKS)}")
print(f"\nOpen your ClickUp list:")
print(f"  https://app.clickup.com/90161512815/v/li/901614094612")
