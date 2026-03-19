# Vanta LMS

## What This Project Is
A Learning Management System built with an **agentic dev workflow**.
Developers don't write code manually — they run slash commands inside Claude Code.
Claude Code IS the agent runtime — it reads ClickUp tasks, references Figma designs,
spawns sub-agents via the Agent tool, generates code, runs tests, and opens GitHub PRs.

No separate Anthropic API key needed. No Python AI calls. Claude Code handles everything.

## Stack
- **Monorepo**: Nx (single repo — backend + frontend)
- **Backend**: Python + FastAPI + PostgreSQL (Neon) — `apps/api/`
- **Frontend**: React + Tailwind + shadcn/ui — `apps/web/`
- **Database**: PostgreSQL via Neon (agents use read-only role)
- **Shared libs**: `libs/` (shared-types, ui, api-client)
- **Agent Runtime**: Claude Code (slash commands + Agent tool)

## Developer Workflow
1. PM grooms a task: `/pm CU-{task_id}`
2. Review groomed task in ClickUp → check `agent_task_approved`
3. Trigger build: `/build CU-{task_id}`
4. Review diffs + test results posted to ClickUp → check `agent_code_approved`
5. Review score report → check `agent_pr_approved`
6. PR created automatically → review on GitHub

## Agent System (Claude Code native — no Python API calls)

| # | Agent | How It Runs | Role |
|---|---|---|---|
| 0 | PM Agent | `/pm` slash command | Task grooming + self-reflection |
| 1 | Orchestrator | `/build` slash command | Coordinates all sub-agents |
| 2 | Design Agent | Agent tool (sub-agent) | Figma → UISpec JSON |
| 3 | Backend Agent | Agent tool (sub-agent) | FastAPI + SQL code gen |
| 4 | Frontend Agent | Agent tool (sub-agent) | React + shadcn/ui code gen |
| 5 | Reflector Agent | Agent tool (sub-agent) | Backend ↔ Frontend contract check |
| 6 | Testing Agent | Agent tool (sub-agent) | pytest + vitest + Playwright |
| 7 | Review Agent | Agent tool (sub-agent) | Evaluator-Optimizer (score 0-100) |
| 8 | GitHub Agent | Agent tool (sub-agent) | Branch + commit + PR |

## Human Checkpoints

| Checkpoint | When | ClickUp Field |
|---|---|---|
| 0 | After PM Agent grooms task | `agent_task_approved` |
| 0.5 | Only if Orchestrator finds ambiguities | `agent_requirements_approved` |
| 1 | After code gen + tests complete | `agent_code_approved` |
| 2 | After review loop passes | `agent_pr_approved` |

## Slash Commands
- `/pm CU-{id}` — Claude Code acts as PM Agent: reads task, fills all fields, posts to ClickUp
- `/build CU-{id}` — Claude Code acts as Orchestrator: runs full pipeline via sub-agents
- `/status CU-{id}` — reads WorkOrder JSON, shows current pipeline state
- `/retry CU-{id} [--from-step N]` — resume from last checkpoint or specific step
- `/cancel CU-{id}` — cleanly cancels workflow, posts to ClickUp

## MCP Integrations (used natively by Claude Code)
- **ClickUp** — read tasks, update custom fields, post comments, set status
- **GitHub** — create branches, commit files, open PRs, add labels, assign reviewers
- **Figma** — fetch design files, extract frames for UISpec generation
- **PostgreSQL (Neon)** — read-only schema inspection (tables, columns, constraints)

## Key Conventions
- **NEVER** write directly to PostgreSQL from agent code (read-only MCP role enforced)
- **NEVER** push to `main` or `develop` directly
- **NEVER** write files to the project during code generation — all output stays in WorkOrder (in-memory / JSON)
- Testing Agent is the **only** exception — writes to `agents/staging/{task_id}/` temporarily, cleans up after
- Branch naming: `feature/CU-{id}-{slug}`, `fix/CU-{id}-{slug}`
- Commit format: `feat(scope): description [CU-{id}]`
- Review pass threshold: score >= 80/100

## ClickUp Status Flow
```
to do → ready → in progress → in review → complete
                     ↓
                  blocked (waiting for human input)
                  cancelled (workflow stopped)
```
| Status | Group | Set By |
|---|---|---|
| `to do` | Not Started | Default / timeout / cancel |
| `ready` | Not Started | PM Agent after DEVELOPMENT_READY |
| `in progress` | Active | Orchestrator when build starts |
| `blocked` | Active | Orchestrator when ambiguities found / PM NEEDS_PM_REVIEW |
| `in review` | Active | GitHub Agent after PR created |
| `complete` | Done | GitHub webhook on PR merge |
| `cancelled` | Closed | /cancel command |

## WorkOrder Persistence
Every step of `/build` saves state to `agents/logs/{task_id}/workorder.json`.
If a session crashes or is interrupted, `/build` or `/retry` automatically resumes from the last completed step.

## Python Utilities (not AI — just helpers)
These Python scripts handle utility tasks only. They do NOT call the Anthropic API.
- `agents/shared/hooks/bash_guard.py` — hook: blocks dangerous shell commands
- `agents/shared/hooks/postgres_guard.py` — hook: blocks destructive SQL
- `agents/shared/hooks/github_guard.py` — hook: blocks push to main/force push
- `agents/shared/hooks/audit_logger.py` — hook: logs every tool call to JSONL

## Safety Guardrails (hooks in settings.json)
- `bash_guard.py` — blocks rm -rf, curl | bash, kill -9, etc.
- `postgres_guard.py` — blocks DROP, TRUNCATE, DELETE without WHERE, ALTER on prod tables
- `github_guard.py` — blocks push to main/develop, force push, repo deletion
- `audit_logger.py` — logs every tool call to `agents/logs/{task_id}.jsonl`

## Project Structure
```
agents/         → SKILL.md files per agent + Python utility hooks
agents/shared/  → Python utilities: hooks, persistence, health check
agents/staging/ → temp test files (gitignored, always cleaned after tests)
agents/logs/    → WorkOrder JSON + audit JSONL per task
skills/         → shared knowledge base loaded into sub-agents as context
apps/api/       → FastAPI backend (Nx Python app)
apps/web/       → React frontend (Nx app)
libs/           → shared-types, ui (shadcn), api-client
.mcp.json       → Claude Code MCP server config (ClickUp, GitHub, Figma, Postgres)
.mcp/           → field IDs, Figma config, user mapping
```

## ClickUp Custom Field IDs
See `.mcp/clickup-fields.json` for all field IDs. Key checkpoint fields:
- `agent_task_approved` — Checkpoint 0
- `agent_requirements_approved` — Checkpoint 0.5
- `agent_code_approved` — Checkpoint 1
- `agent_pr_approved` — Checkpoint 2
