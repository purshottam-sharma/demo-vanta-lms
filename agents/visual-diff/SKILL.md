# Visual Diff Agent

## Role
Close the gap between the Figma design and the rendered frontend by running a
Vision-powered diff loop. Each iteration: screenshot → compare → patch files
directly → re-screenshot → compare again. Loop until score ≥ 95% or max loops.

The agent applies CSS fixes **itself** using Read + Edit tools. It does NOT route
fixes back to the Frontend Agent — that round-trip loses context and wastes loops.

---

## When to Run
Only for `feature-ui` tasks where `figma_url` is present.
Runs as **Step 5.5** — after Testing Agent, before Checkpoint 1.

---

## Inputs
- `figma_png_path` — Figma frame PNG at `/tmp/figma-{task_id}.png`
- `vision_summary` — bullet list of non-obvious design choices from Design Agent
- `task_id` — for file paths
- `route` — frontend route to screenshot (e.g. `/dashboard`)
- `generated_frontend_files` — list of frontend source files (scope for edits)
- `max_loops` — default 5

---

## The Loop

```
SCORE = 0
LOOP up to max_loops:
  Step 1 — Screenshot the rendered page
  Step 2 — Vision comparison → score + structured diff list
  if SCORE >= 95 → return PASSED
  Step 3 — Apply fixes directly (Read + Edit files)
  Step 4 — Wait 1.5s for HMR to apply changes
  continue loop

return MAX_LOOPS_REACHED with remaining diffs
```

---

## Step 1 — Screenshot the Rendered Page

```bash
python3 agents/shared/playwright_screenshot.py {route} /tmp/rendered-{task_id}.png 1440 900
```

This script auto-detects the Vite dev server port (checks 3000, 3001, 3002, 3003, 5173),
injects mock auth into sessionStorage, mocks `/api/v1/users/me`, waits for networkidle
+ 2s buffer, then screenshots at 1440×900.

**If screenshot fails:** log warning, skip loop, include warning in Checkpoint 1 summary.

---

## Step 2 — Vision Comparison

Read **both** PNG files and run Vision with this exact prompt:

```
You are a pixel-perfect UI reviewer. Compare IMAGE 1 (Figma target) vs IMAGE 2 (rendered output).

IMAGE 1 — Figma design: {figma_png_path}
IMAGE 2 — Rendered React: /tmp/rendered-{task_id}.png

PRIORITY CHECKLIST (check these first — known high-risk design choices):
{vision_summary}

For each priority item: explicitly state PASS or FAIL with a reason.

Then scan the full layout for remaining differences in this order:
1. Overall dimensions — sidebar width, navbar height, content padding
2. Component spacing — gap between cards, section margins, padding inside cards
3. Typography — font size, weight, color for each text element
4. Colors — exact background, border, text hex values
5. Border radius — rounded corners (e.g. rounded-lg vs rounded-xl vs rounded-[10px])
6. Icon sizes and colors
7. Layout direction — flex row vs col, grid columns

OUTPUT FORMAT — return valid JSON:
{
  "score": <integer 0-100, where 100 = identical>,
  "priority_checks": [
    { "item": "<vision_summary bullet>", "status": "PASS"|"FAIL", "reason": "<one line>" }
  ],
  "diffs": [
    {
      "component": "<component name>",
      "property": "<css property>",
      "figma_value": "<what figma shows>",
      "rendered_value": "<what the render shows>",
      "file": "<apps/web/src/...>",
      "fix": "<exact Tailwind class change, e.g. change h-[56px] to h-[72px]>",
      "severity": "HIGH"|"MEDIUM"|"LOW"
    }
  ]
}

Rules:
- score 95-100 = pixel-perfect (acceptable)
- score 80-94 = close but needs fixes
- score <80 = significant rework needed
- Only include diffs that require a code change
- For `fix`: be EXACT — name the current class and its replacement
- Ignore text/data content differences (dynamic data is fine)
- Ignore differences caused by browser font rendering (sub-pixel)
- If images look the same, return score 100 with empty diffs array
```

Parse the JSON response. If parsing fails, treat score as 0 and request a re-run.

---

## Step 3 — Apply Fixes Directly

For each diff in the list (ordered HIGH → MEDIUM → LOW):

1. **Read** the file at `diff.file`
2. **Locate** the problematic code — search for the CSS class or property mentioned in `diff.fix`
3. **Edit** the file with the exact change from `diff.fix`
4. **Verify** the edit was applied (re-read the changed lines)

**Fix translation rules:**

| Vision says | Edit action |
|---|---|
| "change h-[56px] to h-[72px]" | Find `h-\[56px\]` in file, replace with `h-[72px]` |
| "change gap-4 to gap-6" | Find `gap-4`, replace with `gap-6` in the target component |
| "change rounded-lg to rounded-[10px]" | Find `rounded-lg`, replace in the specific component context |
| "change text-sm to text-[13px]" | Find `text-sm` in the specific component, replace |
| "add border border-[#e3e8ef]" | Find the element's className, append the classes |
| "change w-[180px] to w-[218px]" | Find the width class, replace |

**Important scoping rules:**
- Always read the file first — confirm the class exists before editing
- When a class appears multiple times, use surrounding context (component name, parent className) to scope the edit precisely
- Make one diff's edit at a time — do not batch multiple diffs into one Edit call
- If a fix would break existing logic, skip it and note it in the report

---

## Step 4 — Wait for HMR

After applying all fixes for this loop:
```bash
sleep 1
```
Vite HMR applies changes in under 1s. The next screenshot will reflect the edits.

---

## Score Thresholds

| Score | Action |
|---|---|
| ≥ 95 | Return PASSED — pixel-perfect achieved |
| 80–94 | Apply fixes, run next loop |
| 60–79 | Apply fixes, run next loop. Log "significant rework" warning |
| < 60 | Apply fixes, run next loop. If still < 60 after loop 2, halt and report |

---

## Output Schema

```json
{
  "status": "PASSED" | "MAX_LOOPS_REACHED" | "HALTED_LOW_SCORE",
  "final_score": 96,
  "loops_run": 2,
  "diffs_found_total": 8,
  "diffs_remaining": 0,
  "priority_checks": {
    "passed": 4,
    "failed": 0
  },
  "figma_png": "/tmp/figma-{task_id}.png",
  "rendered_png": "/tmp/rendered-{task_id}.png",
  "fixes_applied": [
    {
      "component": "Navbar",
      "property": "height",
      "fix": "h-[56px] → h-[72px]",
      "file": "apps/web/src/components/dashboard/Navbar.tsx"
    }
  ],
  "diffs_remaining_list": []
}
```

---

## Self-Reflection Before Returning PASSED

Before marking score ≥ 95 as PASSED, confirm:
- [ ] Every `vision_summary` item was explicitly checked (not skipped)
- [ ] Sidebar width matches Figma px value
- [ ] Navbar height matches Figma px value
- [ ] Card border radius matches exactly (not approximated)
- [ ] Color values are exact hex — not "similar" or "close"
- [ ] Font sizes and weights match
- [ ] Spacing between major sections matches
- [ ] The rendered screenshot was taken AFTER all fixes were applied in this loop

---

## Error Handling

| Error | Action |
|---|---|
| Playwright not installed | `pip install playwright && playwright install chromium`, retry once |
| Dev server not found on any candidate port | Log warning, skip step, add to Checkpoint 1 summary |
| figma_png_path missing | Skip entire visual diff, log warning |
| vision_summary missing | Run without priority checklist (full scan only) |
| Vision returns invalid JSON | Retry the Vision call once with stricter prompt, else treat as score 0 |
| Edit tool finds no match for a fix | Log "fix not applicable — class not found in file", skip that diff |
| Score < 60 after loop 2 | Halt, post full diff list to report, require human review |
