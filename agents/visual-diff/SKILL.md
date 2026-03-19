# Visual Diff Agent

## Role
Compare the rendered frontend against the Figma design frame using Claude Vision.
Identify pixel-level discrepancies and generate targeted fix instructions for the Frontend Agent.
Loop until the rendered output matches Figma within acceptable tolerance.

## When to Run
Only for `feature-ui` tasks where `figma_url` is present.
Runs as **Step 5.5** — after Testing Agent, before Checkpoint 1.

## Inputs
- `figma_png_path` — path to Figma frame PNG (downloaded by Orchestrator in Step 1+2, e.g. `/tmp/figma-{task_id}.png`)
- `task_id` — task identifier (for file paths and staging)
- `route` — frontend route to screenshot (e.g. `/dashboard`, `/login`)
- `generated_frontend_files` — list of frontend files changed (to scope fix instructions)
- `max_loops` — max correction cycles (default: 3)

---

## Step 1 — Screenshot the Rendered Page

Run the Playwright screenshot helper:
```bash
python3 agents/shared/playwright_screenshot.py {route} /tmp/rendered-{task_id}.png
```

This script:
1. Checks if Vite dev server is running on port 5173; starts it if not
2. Injects mock auth into `sessionStorage` so the protected route renders without a real login
3. Mocks `GET /api/v1/users/me` to return demo user data (no backend required)
4. Waits for `networkidle` + 1s font/image buffer
5. Screenshots at 1440×900 viewport and saves to `/tmp/rendered-{task_id}.png`

If the screenshot fails (server won't start, Playwright not installed), log a warning and skip visual diff — do not halt the pipeline.

---

## Step 2 — Visual Comparison with Claude Vision

Read both images as binary and pass them to a Vision sub-agent with this prompt:

```
You are a pixel-perfectness reviewer for a UI build pipeline.

IMAGE 1 (Figma design target): [attach figma_png_path]
IMAGE 2 (Rendered output): [attach rendered_png_path]

Compare them carefully. For every visual difference, output a structured JSON item:
{
  "component": "Navbar",
  "property": "height",
  "figma_value": "72px",
  "rendered_value": "56px",
  "file": "apps/web/src/components/dashboard/Navbar.tsx",
  "fix": "Change h-14 to h-[72px]"
}

Examine these dimensions in order:
1. Layout structure — are all sections/rows present in the correct order?
2. Dimensions — height, width, padding, gap of each major component
3. Typography — font size, weight, color for headings, labels, values
4. Colors — background, border, text color tokens
5. Component details — icon sizes, border radius, shadow
6. Spacing — margin and padding between sections

Rules:
- Only report differences that require a code change to fix
- Be specific: name the Tailwind class to change and what to change it to
- Ignore dynamic data differences (different text content is fine)
- Return PASSED if there are no significant layout/styling differences
- Return NEEDS_FIXES with the full structured list otherwise
```

---

## Step 3 — Process Diff Report

### If PASSED:
Return `VisualDiffReport { status: "PASSED", loops: N, diffs_remaining: 0 }`

### If NEEDS_FIXES:
- Group fixes by file
- Pass to Frontend Agent:
  ```
  Apply these pixel-perfect fixes from visual comparison with Figma.
  Do NOT change any logic, only CSS/Tailwind class values:

  [structured fix list grouped by file]
  ```
- Frontend Agent applies changes to the actual files on disk
- Re-run Steps 1–2
- Repeat up to `max_loops` times

### If max loops reached with remaining diffs:
Return `VisualDiffReport { status: "MAX_LOOPS_REACHED", loops: N, diffs_remaining: [...] }`
Include remaining diffs in Checkpoint 1 summary so the human can decide.

---

## Output Schema
```json
{
  "status": "PASSED" | "NEEDS_FIXES" | "MAX_LOOPS_REACHED",
  "loops": 2,
  "diffs_found_total": 8,
  "diffs_remaining": 0,
  "figma_png": "/tmp/figma-{task_id}.png",
  "rendered_png": "/tmp/rendered-{task_id}.png",
  "fixes_applied": [
    {
      "component": "Navbar",
      "property": "height",
      "fix": "h-14 → h-[72px]",
      "file": "apps/web/src/components/dashboard/Navbar.tsx"
    }
  ]
}
```

---

## Self-Reflection Checklist
Before returning PASSED, verify each of these visually:
- [ ] Overall layout structure matches (sidebar left, content right, navbar top)
- [ ] Sidebar width and header height match
- [ ] Navbar height and internal element layout match
- [ ] Card rows: correct number of cards per row, correct layout direction
- [ ] Typography: value font size/weight, label size, subtitle size
- [ ] Color tokens: no approximations — hex values must match exactly
- [ ] Spacing between sections matches
- [ ] Quick action card orientation matches (horizontal vs vertical)
- [ ] Icon sizes match
- [ ] Border radii match (rounded-lg vs rounded-xl etc.)

---

## Error Handling
- Playwright not installed → `pip install playwright && playwright install chromium`, retry once
- Dev server fails to start after 30s → skip visual diff, add warning to Checkpoint 1 summary
- Vision sub-agent returns ambiguous result → treat as NEEDS_FIXES and do one fix cycle
- Figma PNG missing → skip visual diff entirely, log warning
