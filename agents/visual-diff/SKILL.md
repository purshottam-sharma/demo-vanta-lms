# Visual Diff Agent

## Role
Close the gap between the Figma design and the rendered frontend using a
**two-layer comparison**:
1. `pixelmatch.py` — real pixel-level diff (objective, per-region scores)
2. Claude Vision — reads the diff PNG to understand *what* is wrong and *how* to fix it

The agent applies CSS fixes **directly** using Read + Edit tools. It loops until
the pixelmatch full-page score ≥ 98% or max_loops reached.

**Run as Claude Opus 4.6 (`claude-opus-4-6`) for best reasoning per fix loop.**

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
PRE-LOOP (run once before the pixel loop):
  Icon Audit — element screenshots + Figma crop comparison → fix all wrong icons first

LOOP up to max_loops:
  Step 1 — Full-page screenshot at 1440×1332 (matches Figma @1x canvas height)
  Step 2 — pixelmatch: full-page score + per-region breakdown + diff PNG
  if full-page score ≥ 98% → PASSED
  Step 3 — Vision reads the diff PNG → identifies what's red and why
  Step 4a — For any component with Y-mismatch: element-level screenshot + Figma lookup
  Step 4b — Apply fixes directly (Read + Edit source files)
  Step 5 — sleep 1 (HMR)
  continue

return MAX_LOOPS_REACHED
```

---

## PRE-LOOP — Icon Audit (mandatory, run once before pixel loop)

Icons are small and pixelmatch scores them as low-impact even when wrong shape.
Run this audit BEFORE the main loop so icons are correct by loop 1.

### Step A — Crop Figma into sections
```python
from PIL import Image
figma = Image.open(figma_png_path)  # @2x, e.g. 2880×2664
# Adjust y-coords based on actual Figma layout
figma.crop((0, 0, 472, figma.height)).save('/tmp/figma-icon-sidebar.png')        # sidebar @2x
figma.crop((472, 72, 2880, 370)).save('/tmp/figma-icon-quick-actions.png')       # quick actions @2x
figma.crop((472, 370, 2880, 610)).save('/tmp/figma-icon-stat-cards.png')         # stat cards @2x
figma.crop((472, 870, 2880, 1200)).save('/tmp/figma-icon-status-cards.png')      # status cards @2x
```

### Step B — Take element-level screenshots of same sections
```bash
python3 agents/shared/playwright_screenshot.py {route} /tmp/rendered-icon-sidebar.png \
  --selector "[data-component='sidebar']"
python3 agents/shared/playwright_screenshot.py {route} /tmp/rendered-icon-quick-actions.png \
  --selector "[data-component='quick-actions']"
python3 agents/shared/playwright_screenshot.py {route} /tmp/rendered-icon-stat-cards.png \
  --selector "[data-component='stat-cards']"
python3 agents/shared/playwright_screenshot.py {route} /tmp/rendered-icon-status-cards.png \
  --selector "[data-component='status-cards']"
```

### Step C — Ask Gemini to compare icon pairs section by section

Write prompt to file then call Gemini with ONE Figma crop + ONE rendered screenshot at a time.
Comparing section-by-section is more accurate than giving Gemini all images at once.

```bash
cat > /tmp/icon-prompt.txt << 'PROMPT'
Compare these two images of the SAME UI section. First is Figma (ground truth), second is rendered React.

Look at every icon in every card/row carefully. Compare shape, symbol, and style.
List ONLY mismatches (icons that look different between the two images).

For each mismatch output:
{
  "label": "card or nav item label",
  "figma_icon": "exact shape description (e.g. lightning bolt, envelope, graduation cap on person)",
  "rendered_icon": "exact shape description",
  "lucide_fix": "LucideIconName"
}

Return JSON array. Return [] if all icons match.
PROMPT

# Run for each section pair
python3 agents/shared/gemini.py --prompt-file /tmp/icon-prompt.txt \
  --image /tmp/figma-icon-sidebar.png --image /tmp/rendered-icon-sidebar.png \
  --json > /tmp/icon-audit-sidebar.json

python3 agents/shared/gemini.py --prompt-file /tmp/icon-prompt.txt \
  --image /tmp/figma-icon-quick-actions.png --image /tmp/rendered-icon-quick-actions.png \
  --json > /tmp/icon-audit-quick-actions.json

# ... repeat for each section
```

### Step D — Apply icon fixes
For each mismatch found: update the icon import and assignment in the source file.
Verify the lucide icon name exists before applying:
```bash
node -e "const l=require('./node_modules/lucide-react'); console.log(!!l.{IconName})"
```

### Step E — Confirm fixes with a second Gemini pass
Re-screenshot and re-compare the fixed sections. Only proceed to the pixel loop once
all icon audits return [].

---

## Step 1 — Full-Page Screenshot

```bash
python3 agents/shared/playwright_screenshot.py {route} /tmp/rendered-{task_id}.png 1440 1332
```

**Why 1440×1332?** The Figma canvas exports at @2x (2880×2664 pixels). At @1x that is 1440×1332.
Matching the viewport height to the Figma @1x height aligns the two images so pixel comparison is valid.

If the page content fits in less than 1332px, the extra space is empty white — that's fine,
pixelmatch will score it as matching (white = white).

---

## Step 1b — Element-Level Screenshots (when Y-mismatch detected)

All major dashboard sections have `data-component` attributes set on their root element.
Use element-level screenshots for components where full-page Y-alignment is suspect:

```bash
# Screenshot a specific component by its data-component attribute
python3 agents/shared/playwright_screenshot.py {route} /tmp/comp-school-health.png \
  --selector "[data-component='school-health']"

python3 agents/shared/playwright_screenshot.py {route} /tmp/comp-user-distribution.png \
  --selector "[data-component='user-distribution']"
```

Available `data-component` values on the dashboard:
- `navbar` — top navigation bar
- `sidebar` — left sidebar
- `quick-actions` — top action buttons row
- `stat-cards` — 4 metric cards row
- `school-health` — school health index panel
- `intelligence-insights` — AI insights panel
- `status-cards` — status indicator cards
- `absentees-table` — absentee data table
- `user-distribution` — user distribution bar chart

**When to use element screenshots:** If the diff PNG shows red scattered across the page
in a positional pattern (whole sections shifted), switch to element-level screenshots
for those components and compare them against the equivalent Figma node crop.

**Getting the Figma node crop to compare against:**
```bash
# Get exact measurements from Figma for a named node
python3 agents/shared/figma_lookup.py --node-name "School Health Index" \
  --output /tmp/figma-node-school-health.json
```
Then use the `node_id` to export just that frame via the Figma API:
```bash
source .env
curl -s "https://api.figma.com/v1/images/$FIGMA_FILE_ID?ids={node_id}&format=png&scale=2" \
  -H "X-Figma-Token: $FIGMA_API_TOKEN" \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print(list(d['images'].values())[0])"
# Then curl -sL that URL to /tmp/figma-comp-school-health.png
```

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

## Step 3 — Gemini Reads the Diff PNG

**Use Gemini 2.5 Pro for this step** — superior at identifying specific pixel differences
in diff images compared to Claude Vision.

Write the prompt and call Gemini:

```bash
cat > /tmp/diff-prompt-{task_id}.txt << PROMPT
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

If you are uncertain about exact values (px, hex colors), say so — set needs_figma_lookup: true.

Output as a JSON array only (no markdown, no explanation):
[
  {
    "component": "SchoolHealthProgressBar",
    "what_is_wrong": "segments are rounded pills, Figma shows square blocks",
    "file": "apps/web/src/components/dashboard/DashboardBody.tsx",
    "fix": "change rounded-full to rounded-[2px] on segment divs",
    "needs_figma_lookup": false
  },
  {
    "component": "UserDistributionChart",
    "what_is_wrong": "Y-axis labels missing, bar colors uncertain",
    "file": "apps/web/src/components/dashboard/DashboardBody.tsx",
    "fix": "add Y-axis labels; verify bar colors",
    "needs_figma_lookup": true,
    "figma_node_name": "User Distribution"
  }
]

If there are no red regions (only grey/yellow), return: { "status": "PASSED" }
PROMPT

python3 agents/shared/gemini.py \
  --prompt-file /tmp/diff-prompt-{task_id}.txt \
  --image /tmp/diff-{task_id}.png \
  --json \
  > /tmp/diff-analysis-{task_id}.json
```

Parse `/tmp/diff-analysis-{task_id}.json`. If it contains `{ "status": "PASSED" }` → exit loop with PASSED.

**Fallback:** If `gemini.py` exits with code 1, fall back to reading the diff PNG directly
with Claude Vision using the same prompt. Log the fallback.

---

## Step 4 — Get Authoritative Measurements (when needs_figma_lookup = true)

For any fix where Vision is uncertain about exact values:

```bash
python3 agents/shared/figma_lookup.py --node-name "{figma_node_name}" \
  --output /tmp/figma-lookup-{component}.json
```

Read the output JSON. It provides:
- `size` — exact width/height in px
- `fills` — exact hex colors
- `corner_radius` — exact border radius
- `gap` — item spacing
- `padding` — exact padding values
- `font` — family, size, weight
- `children_summary` — repeated child sizes/colors (e.g. 30 progress segments)

Use these authoritative values in your fix instead of Vision's guess.

---

## Step 5 — Apply Fixes

For each fix from Vision (enriched with Figma lookup data where needed):

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
- If Figma lookup gives a hex color → use that exact value, not a Tailwind approximation

---

## Step 6 — HMR Wait

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

**Fix strategy:** Switch to element-level screenshots (Step 1b) for affected components.
Export the matching Figma frame crop and compare component-to-component.
The `data-component` attributes on all dashboard sections make this easy.

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
| `figma_lookup.py` fails | Use Vision estimate, log warning |
| Vision returns invalid JSON | Retry once with stricter prompt |
| Score < 90 after loop 2 | Halt, post diff report + region scores to ClickUp |
