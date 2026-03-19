# Visual Diff Agent

## Role
Validate that the rendered frontend matches the Figma design by comparing two images
with Claude Vision. Uses the Design Agent's `vision_summary` as a priority checklist
so the diff is targeted — checking known high-risk choices first, not scanning from zero.

This is a **validator**, not a discoverer. The Design Agent already captured intent.
The Visual Diff Agent verifies the Frontend Agent honoured it.

## When to Run
Only for `feature-ui` tasks where `figma_url` is present.
Runs as **Step 5.5** — after Testing Agent, before Checkpoint 1.

## Inputs
- `figma_png_path` — Figma frame PNG downloaded by Design Agent (`/tmp/figma-{task_id}.png`)
- `vision_summary` — bullet list of non-obvious design choices from Design Agent
- `task_id` — for file paths
- `route` — frontend route to screenshot (e.g. `/dashboard`)
- `generated_frontend_files` — list of frontend files (to scope fix instructions)
- `max_loops` — max correction cycles (default: 3)

---

## Step 1 — Screenshot the Rendered Page

Run the Playwright screenshot helper:
```bash
python3 agents/shared/playwright_screenshot.py {route} /tmp/rendered-{task_id}.png
```

This script:
1. Checks if Vite dev server is running on port 5173; starts it if not
2. Injects mock auth into `sessionStorage` — protected route renders without a real login
3. Mocks `GET /api/v1/users/me` to return demo user data — no backend required
4. Waits for `networkidle` + 1.5s buffer for web fonts and images
5. Screenshots at 1440×900 and saves to `/tmp/rendered-{task_id}.png`

If screenshot fails, log a warning and skip — do not halt the pipeline.

---

## Step 2 — Targeted Vision Comparison

Pass **both images** + the `vision_summary` from the Design Agent to Claude Vision:

```
You are a pixel-perfectness reviewer comparing a Figma design against a rendered page.

IMAGE 1 — Figma design target: [figma_png_path]
IMAGE 2 — Rendered React output: [rendered_png_path]

The Design Agent already analysed this design and flagged these non-obvious
choices that developers commonly get wrong. Check these FIRST:

{vision_summary}
  Example:
  • "Quick action cards are horizontal pills (icon left, label right) — not vertical stacks"
  • "Notification button is a 48×48 square pill with bg #f8fafc — not a bare icon"
  • "Profile area is a full-width pill container with chevron — not loose avatar + text"
  • "Sidebar footer is a full-width button with Settings icon — not plain text"

For each item in vision_summary: does the rendered output match? Report pass/fail.

Then scan for any remaining differences not covered by vision_summary:
1. Layout structure — sections present in correct order?
2. Dimensions — height, width, padding, gap of each major component
3. Typography — font size, weight, color
4. Colors — background, border, text (exact hex)
5. Border radius, shadows, icon sizes
6. Spacing between sections

For every difference found, output a structured JSON item:
{
  "component": "Navbar",
  "property": "height",
  "figma_value": "72px",
  "rendered_value": "56px",
  "file": "apps/web/src/components/dashboard/Navbar.tsx",
  "fix": "Change h-14 to h-[72px]",
  "source": "vision_summary" | "scan"
}

Rules:
- Only report differences that require a code change
- Be specific: name the exact Tailwind class and what to change it to
- Ignore text content differences (dynamic data is fine)
- Return PASSED if all vision_summary items pass and no significant scan differences
- Return NEEDS_FIXES with the full structured list otherwise
```

The `source` field distinguishes:
- `"vision_summary"` — a known high-risk choice the Frontend Agent missed
- `"scan"` — a general layout/style difference discovered by scanning

This matters for routing fixes: `vision_summary` failures go back to the Frontend Agent
with the original intent context; `scan` failures are targeted CSS patches.

---

## Step 3 — Process Diff Report

### If PASSED:
Return `VisualDiffReport { status: "PASSED", loops: N, diffs_remaining: 0 }`

### If NEEDS_FIXES:
Group fixes by file and by source, then route them:

**vision_summary failures** — Frontend Agent needs the original intent reinstated:
```
These design intent items from the Design Agent were not implemented correctly.
Re-read the vision_summary carefully and fix each one:

[items with source: "vision_summary"]

Context from Design Agent:
{vision_summary}
```

**scan failures** — targeted CSS patches only:
```
Apply these pixel-perfect CSS fixes. Do NOT change any logic:

[items with source: "scan", grouped by file]
```

After fixes are applied, re-run Steps 1–2. Repeat up to `max_loops` times.

### If max loops reached:
Return `VisualDiffReport { status: "MAX_LOOPS_REACHED", loops: N, diffs_remaining: [...] }`
Include remaining diffs in Checkpoint 1 summary for human review.

---

## Output Schema
```json
{
  "status": "PASSED" | "NEEDS_FIXES" | "MAX_LOOPS_REACHED",
  "loops": 1,
  "diffs_found_total": 4,
  "diffs_remaining": 0,
  "vision_summary_checks": {
    "passed": 3,
    "failed": 1
  },
  "figma_png": "/tmp/figma-{task_id}.png",
  "rendered_png": "/tmp/rendered-{task_id}.png",
  "fixes_applied": [
    {
      "component": "QuickActionCard",
      "property": "layout direction",
      "fix": "flex-col → flex-row",
      "file": "apps/web/src/components/dashboard/DashboardBody.tsx",
      "source": "vision_summary"
    }
  ]
}
```

---

## Why Two Calls, Not One

The Design Agent's Vision call and this call are different tasks:

| | Design Agent Vision | Visual Diff Vision |
|---|---|---|
| Images | 1 (Figma PNG only) | 2 (Figma PNG + rendered screenshot) |
| Task | "Describe design intent" | "Find differences between these two" |
| Output | UISpec + vision_summary | Structured diff list with fix instructions |
| Timing | Once, before code is written | Per loop, after code is rendered |

The `vision_summary` flows from call #1 into call #2 as a priority checklist —
so call #2 is not starting from zero, it's verifying a known list of risks first.

---

## Self-Reflection Checklist
Before returning PASSED:
- [ ] Every item in `vision_summary` was explicitly checked and passed
- [ ] Overall layout structure matches (sidebar / navbar / content zones)
- [ ] Sidebar: width, header height, nav item height, footer type (button not text)
- [ ] Navbar: height, search bar dimensions, notification pill, profile pill
- [ ] Card rows: correct count per row, correct layout direction per card
- [ ] Typography: value size/weight, label size, matches Figma JSON
- [ ] All color tokens are exact hex — no approximations
- [ ] Border radii consistent (rounded-lg ≠ rounded-xl)
- [ ] Spacing between sections matches

---

## Error Handling
- Playwright not installed → `pip install playwright && playwright install chromium`, retry once
- Dev server fails to start after 40s → skip visual diff, add warning to Checkpoint 1 summary
- `figma_png_path` missing → skip visual diff, log warning
- `vision_summary` missing → run without it (fall back to full scan only)
- Vision returns ambiguous result → treat as NEEDS_FIXES, do one fix cycle
