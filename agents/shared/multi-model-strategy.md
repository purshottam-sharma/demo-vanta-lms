# Multi-Model Orchestration Strategy

Vanta LMS uses multiple AI models and data sources in the same pipeline, routing
each step to the best tool for it.

## Data Source Priority (Design Agent)

```
1. Figma MCP structured data  → exact px, hex, Auto Layout constraints  ← PRIMARY
2. Figma variables/styles      → design token names                      ← PRIMARY
3. Gemini Vision (PNG)         → visual intent, non-obvious choices      ← SUPPLEMENTARY ONLY
```

Never use Vision to measure px values or colors — that's what causes Visual Diff loops.

## Model Assignments

| Agent / Step | Model | Reason |
|---|---|---|
| PM Agent | Claude Sonnet 4.6 | Task analysis, ClickUp tool use |
| Design Agent — Steps 2+3: MCP data + tokens | Claude Sonnet 4.6 | Structured data via Figma MCP tools |
| **Design Agent — Step 5: Vision analysis** | **Gemini 2.5 Flash** | Visual intent only (not measurements) |
| Backend Agent | Claude Sonnet 4.6 | FastAPI + SQL code gen |
| Frontend Agent | Claude Sonnet 4.6 | React + Tailwind code gen, file editing |
| Reflector Agent | Claude Sonnet 4.6 | Contract verification |
| Testing Agent | Claude Sonnet 4.6 | pytest + vitest + Playwright test writing |
| **Visual Diff Agent — loop runner** | **Claude Opus 4.6** | Deep reasoning across multi-turn fix loops |
| **Visual Diff Agent — Step 3: diff PNG reading** | **Gemini 2.5 Flash** | Pixel diff interpretation |
| Review Agent | Claude Sonnet 4.6 | Code review scoring |
| GitHub Agent | Claude Sonnet 4.6 | Branch + commit + PR via GitHub MCP |
| Orchestrator | Claude Sonnet 4.6 | Pipeline coordination, checkpoint decisions |

## Figma MCP Tools Used

| MCP Tool | Used In | What It Returns |
|---|---|---|
| `get_file_nodes` | Design Agent Step 2a | Full node tree — exact px, colors, Auto Layout |
| `list_variables_for_file` | Design Agent Step 2b | Design token names + resolved values |
| `list_styles_in_file` | Design Agent Step 2c | Named color + typography styles |
| `list_components` | Design Agent (optional) | Component inventory |

**Why not `get_design_context`?** That tool is from the official Figma Dev Mode MCP server
(requires Figma desktop app). The `figma-mcp-server` npm package wraps the REST API instead.
When the official Figma desktop MCP becomes available in this environment, switch to it —
`get_design_context` returns a pre-processed React+Tailwind representation that eliminates
the manual Auto Layout → Tailwind mapping step entirely.

## Routing Rules

**Use Gemini when:**
- The task is purely visual: reading an image, identifying pixel differences, interpreting UI layout from a screenshot
- The input is a PNG/image file and the output is a text description or JSON of what's in the image

**Use Claude Opus when:**
- The task requires multi-turn reasoning with state across many steps
- The agent must apply code fixes, read files, edit code, AND evaluate quality all in one loop
- High-stakes decisions where reasoning depth matters more than speed/cost

**Use Claude Sonnet when:**
- Code generation (any language)
- Structured data extraction from text
- Tool use (MCP calls, file read/edit, bash)
- Anything that involves writing or modifying source files

## How Gemini Is Called

Gemini is invoked as a subprocess, not as a sub-agent. This keeps it clean and isolated:

```bash
# Vision call (diff PNG analysis)
python3 agents/shared/gemini.py \
  --prompt-file /tmp/prompt.txt \
  --image /tmp/diff.png \
  --json \
  > /tmp/gemini-output.json

# Text-only call
python3 agents/shared/gemini.py \
  --prompt "Summarise these design notes" \
  > /tmp/summary.txt
```

See `agents/shared/gemini.py` for full usage.

## Configuration

```env
# .env
GEMINI_API_KEY=...
GEMINI_MODEL=gemini-2.5-flash   # confirmed working on free tier
```

## Fallback Behavior

If `gemini.py` exits with code 1 (API error, missing key, timeout):
- Design Agent Step 4: fall back to Claude Vision (read PNG directly)
- Visual Diff Agent Step 3: fall back to Claude Vision (read diff PNG directly)

Both fallbacks log a warning to the console. The pipeline never halts due to a Gemini failure.
