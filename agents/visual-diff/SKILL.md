# Visual Diff Agent

## Role
Close the gap between the Figma design and the rendered frontend using a
**two-layer comparison**:
1. `pixelmatch.py` — real pixel-level diff (objective, per-region scores)
2. Claude Vision — reads the diff PNG to understand *what* is wrong and *how* to fix it

The agent applies CSS fixes **directly** using Read + Edit tools. It loops until
the pixelmatch full-page score ≥ 98% or max_loops reached.

---

## When to Run
Only for `feature-ui` tasks where `figma_url` is present.
Runs as **Step 5.5** — after Testing Agent, before Checkpoint 1.

---

## Inputs
- `figma_png_path` — Figma frame PNG at `/tmp/figma-{task_id}.png` (exported @2x by Design Agent)
- `vision_summary` — bullet list of measurable design choices from Design Agent
- `task_id`
- `route` — frontend route to screenshot (e.g. `/dashboard`)
- `generated_frontend_files` — list of editable source files
- `regions_json` — optional path to component region map (e.g. `agents/shared/dashboard-regions.json`)
- `max_loops` — default 5

---

## The Loop

```
LOOP up to max_loops:
  Step 1 — Screenshot at 1440×1332 (matches Figma @1x canvas height)
  Step 2 — pixelmatch: full-page score + per-region breakdown + diff PNG
  if full-page score ≥ 98% → PASSED
  Step 3 — Vision reads the diff PNG → identifies what's red and why
  Step 4 — Apply fixes directly (Read + Edit source files)
  Step 5 — sleep 1 (HMR)
  continue

return MAX_LOOPS_REACHED
```

---

## Step 1 — Screenshot

```bash
python3 agents/shared/playwright_screenshot.py {route} /tmp/rendered-{task_id}.png 1440 1332
```

**Why 1440×1332?** The Figma canvas exports at @2x (2880×2664 pixels). At @1x that is 1440×1332.
Matching the viewport height to the Figma @1x height aligns the two images so pixel comparison is valid.

If the page content fits in less than 1332px, the extra space is empty white — that's fine,
pixelmatch will score it as matching (white = white).

---

## Step 2 — Pixelmatch

```bash
python3 agents/shared/pixelmatch.py \
  {figma_png_path} \
  /tmp/rendered-{task_id}.png \
  /tmp/diff-{task_id}.png \
  --regions {regions_json}
```

Parse the JSON output:
- `score` — full-page similarity (0-100). Target: ≥ 98
- `diff_pixels` — total pixel count that differ
- `diff_image` — path to diff PNG (grey=same, red=wrong, yellow=antialiasing)
- `regions` — per-component breakdown: `{ "school_health": { "score": 96.2, "diff_pixels": 3000 } }`

**Important:** `regions` scores are only valid when section Y-coordinates in the
rendered page match the Figma @1x layout. If the Figma has significantly more
vertical spacing, region scores will be inaccurate — rely on the full-page score
and the diff PNG image instead.

---

## Step 3 — Vision Reads the Diff PNG

Read the diff PNG and ask Vision:

```
This is a pixel diff image comparing a Figma design vs a rendered React page.
- Grey pixels = identical (good)
- Yellow pixels = antialiasing differences (ignore)
- RED pixels = actual differences that need to be fixed

The Design Agent flagged these high-risk design choices to check first:
{vision_summary}

For every RED region you see:
1. Which UI component is it in? (e.g. "School Health Index progress bar")
2. What exactly is different? (shape, color, size, presence/absence)
3. Which source file likely controls it?
4. What exact CSS change would fix it?

Output as JSON array:
[
  {
    "component": "SchoolHealthProgressBar",
    "what_is_wrong": "segments are rounded pills, Figma shows square blocks",
    "file": "apps/web/src/components/dashboard/DashboardBody.tsx",
    "fix": "change rounded-full to rounded-[2px] on segment divs"
  }
]

If there are no red regions (only grey/yellow), return: { "status": "PASSED" }
```

---

## Step 4 — Apply Fixes

For each fix from Vision:

1. **Read** the file
2. **Find** the exact code (search for the class or element described)
3. **Edit** with the specific change
4. **Verify** the change is in the file

**Scoping rules:**
- Read the file first — never edit blind
- Use surrounding context to scope edits when the same class appears multiple times
- One diff → one Edit call
- If Vision says "add X" → find the element's className and append
- If Vision says "change X to Y" → find X in context and replace

---

## Step 5 — HMR Wait

```bash
sleep 1
```

---

## Score Thresholds

| Score | Action |
|---|---|
| ≥ 98% | PASSED — pixel-perfect |
| 95–97% | Apply fixes, next loop |
| 90–94% | Apply fixes, next loop. Log warning |
| < 90 after loop 2 | Halt, post report, require human |

---

## Known Limitation: Layout Height Mismatch

If the Figma canvas is taller than the rendered page (e.g. Figma=1332px, render content=720px),
the lower sections will be at different Y coordinates. In this case:

- **Full-page pixelmatch score** will be inflated (empty white space matches white background)
- **Region scores** for bottom sections will be inaccurate
- **Diff PNG** will show red from positional overlap between Figma sections and rendered sections

**Detection:** If the rendered screenshot has large empty white areas at the bottom AND diff shows
red in mid-page areas, this is likely positional mismatch, not actual visual differences.

**Fix strategy:** In this case, crop each component individually using Playwright element screenshots:
```bash
# Screenshot a specific element by CSS selector
python3 agents/shared/playwright_screenshot.py {route} /tmp/comp-{name}.png \
  --selector ".school-health-card"
```
Then compare the cropped component against the equivalent Figma crop.

---

## Output Schema

```json
{
  "status": "PASSED" | "MAX_LOOPS_REACHED" | "HALTED_LOW_SCORE",
  "final_score": 98.4,
  "loops_run": 2,
  "diff_pixels_start": 41549,
  "diff_pixels_end": 3200,
  "diff_image": "/tmp/diff-{task_id}.png",
  "fixes_applied": [
    {
      "component": "SchoolHealthProgressBar",
      "fix": "rounded-full → rounded-[2px]",
      "file": "apps/web/src/components/dashboard/DashboardBody.tsx"
    }
  ],
  "region_scores": {
    "navbar": 100.0,
    "sidebar": 99.9,
    "school_health": 98.1
  }
}
```

---

## Error Handling

| Error | Action |
|---|---|
| Playwright not installed | `pip install playwright && playwright install chromium`, retry once |
| Dev server not found | Log warning, skip visual diff, add to Checkpoint 1 summary |
| `figma_png_path` missing | Skip, log warning |
| `pixelmatch.py` fails | Fall back to Vision-only comparison (read both PNGs directly) |
| Vision returns invalid JSON | Retry once with stricter prompt |
| Score < 90 after loop 2 | Halt, post diff report + region scores to ClickUp |
