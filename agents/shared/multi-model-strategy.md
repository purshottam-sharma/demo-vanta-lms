# Multi-Model Orchestration Strategy

Vanta LMS uses multiple AI models in the same pipeline, routing each step to the
model best suited for it.

## Model Assignments

| Agent / Step | Model | Reason |
|---|---|---|
| PM Agent | Claude Sonnet 4.6 | Task analysis, ClickUp tool use |
| Design Agent — Figma JSON extraction | Claude Sonnet 4.6 | Structured data parsing |
| **Design Agent — Step 4: Vision analysis** | **Gemini 2.5 Pro** | Better image understanding for dense UI frames |
| Backend Agent | Claude Sonnet 4.6 | FastAPI + SQL code gen |
| Frontend Agent | Claude Sonnet 4.6 | React + Tailwind code gen, file editing |
| Reflector Agent | Claude Sonnet 4.6 | Contract verification |
| Testing Agent | Claude Sonnet 4.6 | pytest + vitest + Playwright test writing |
| **Visual Diff Agent — loop runner** | **Claude Opus 4.6** | Deep reasoning across multi-turn fix loops |
| **Visual Diff Agent — Step 3: diff PNG reading** | **Gemini 2.5 Pro** | Best-in-class pixel diff interpretation |
| Review Agent | Claude Sonnet 4.6 | Code review scoring |
| GitHub Agent | Claude Sonnet 4.6 | Branch + commit + PR via GitHub MCP |
| Orchestrator | Claude Sonnet 4.6 | Pipeline coordination, checkpoint decisions |

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
GEMINI_MODEL=gemini-2.5-pro-preview   # override to pin a specific version
```

## Fallback Behavior

If `gemini.py` exits with code 1 (API error, missing key, timeout):
- Design Agent Step 4: fall back to Claude Vision (read PNG directly)
- Visual Diff Agent Step 3: fall back to Claude Vision (read diff PNG directly)

Both fallbacks log a warning to the console. The pipeline never halts due to a Gemini failure.
