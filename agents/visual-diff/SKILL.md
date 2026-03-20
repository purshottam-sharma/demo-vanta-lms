# Visual Diff Agent

## Role
Close the gap between the Figma design and the rendered frontend using a
**two-layer comparison**:
1. `pixelmatch.py` — real pixel-level diff (objective, per-region scores)
2. Claude Vision — reads the diff PNG to understand *what* is wrong and *how* to fix it

The agent applies CSS fixes **directly** using Read + Edit tools. It loops until
the pixelmatch full-page score ≥ 98% or max_loops reached.

**Run as Claude Opus 4.6 (`claude-opus-4-6`) for best reasoning per fix loop.**

## Tool Budget
Read `agents/shared/TOOL-BUDGET.md`. Target: **≤ 30 tool calls** for a typical 2-loop run.

| Step | Tools | Notes |
|---|---|---|
| Read SKILL.md + regions JSON | 2 | One-time |
| Find dev server port | 1 | `ss -tlnp \| grep node` — **not** curl polling |
| PRE-LOOP icon audit | 3 | 2 Bash (crops+screenshots) + 1 Gemini |
| Per loop: screenshot | 1 | |
| Per loop: pixelmatch | 1 | |
| Per loop: Gemini diff read | 1 | Inline --prompt, no temp file |
| Per loop: fixes (8 fixes, 2 files) | ~10 | 2 Reads + 8 Edits |
| Per loop: sleep | 1 | |
| Read final rendered PNG (once, at end) | 1 | User display only |
| **Total for 2 loops** | **~30** | |

**Anti-patterns that inflate tool count (avoid these):**
- Re-reading a file you already read this loop
- Re-reading after an Edit to "verify" — trust the Edit tool
- Writing prompt to a temp file when `--prompt` fits inline
- Taking element screenshots proactively — only when Y-mismatch is detected
- Running 4 separate Gemini calls for icon audit when 1 call handles all sections
- **Polling for dev server with curl** — use `ss -tlnp | grep node` once (saves 8-10 calls)
- **Reading rendered PNG mid-loop** to show the user — read it only once, at the very end
- **Chunked Bash reads of JSON files** — use `Read /tmp/uispec-{id}.json` (1 call, not 3)

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

### Step C — ONE Gemini call with all section pairs

Pass all Figma crops and rendered screenshots in a single Gemini call.
Order: figma-sidebar, rendered-sidebar, figma-quick-actions, rendered-quick-actions,
figma-stat-cards, rendered-stat-cards, figma-status-cards, rendered-status-cards.

```bash
python3 agents/shared/gemini.py \
  --prompt "Images are pairs: (1,2)=sidebar, (3,4)=quick-actions, (5,6)=stat-cards, (7,8)=status-cards. Odd=Figma, Even=Rendered. List ONLY icon mismatches across all sections. For each: {\"section\",\"label\",\"figma_icon\",\"rendered_icon\",\"lucide_fix\"}. Return JSON array, [] if none." \
  --image /tmp/figma-icon-sidebar.png \
  --image /tmp/rendered-icon-sidebar.png \
  --image /tmp/figma-icon-quick-actions.png \
  --image /tmp/rendered-icon-quick-actions.png \
  --image /tmp/figma-icon-stat-cards.png \
  --image /tmp/rendered-icon-stat-cards.png \
  --image /tmp/figma-icon-status-cards.png \
  --image /tmp/rendered-icon-status-cards.png \
  --json > /tmp/icon-audit.json
```

**1 Gemini call total** (not 4 separate calls).

### Step D — Apply icon fixes
For each mismatch: update the import and assignment in the source file.
**Read each source file ONCE, apply ALL its icon fixes, then move to the next file.**
Verify the lucide icon name exists before applying:
```bash
node -e "const l=require('./node_modules/lucide-react'); console.log(!!l.{IconName})"
```

### Step E — Confirm with ONE re-screenshot + ONE Gemini call
Take one combined screenshot of all sections and run a single Gemini comparison.
Only proceed to the pixel loop once the audit returns [].

---

## Step 1 — Full-Page Screenshot

**Find the dev server port first (1 call, not 10):**
```bash
# Get port in one shot — never curl-poll in a loop
DEV_PORT=$(ss -tlnp | grep node | grep -oP ':\K[0-9]+' | head -1)
# If empty, the server isn't running — start it and wait once:
# npx nx serve web > /dev/null 2>&1 & sleep 12 && DEV_PORT=4200
```

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

Call Gemini with `--prompt` inline — **no temp file needed**:

```bash
python3 agents/shared/gemini.py \
  --prompt "Pixel diff image: grey=same, yellow=antialiasing(ignore), red=wrong. For every RED region: {\"component\",\"what_is_wrong\",\"file\",\"fix\",\"needs_figma_lookup\"}. Files are in apps/web/src/. Return JSON array. If no red regions: {\"status\":\"PASSED\"}" \
  --image /tmp/diff-{task_id}.png \
  --json \
  > /tmp/diff-analysis-{task_id}.json
```

**1 Bash call total** (no cat to write prompt file first).

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

## Step 5 — Apply Fixes (tool-efficient)

**Group fixes by file first. Read each file ONCE. Apply all its fixes. Move on.**
Never re-read a file you already read in this loop. Never re-read after an Edit to verify.

```
GROUP fixes by file:
  file_a: [fix1, fix2, fix3]
  file_b: [fix4]

FOR each file_group:
  Read file ONCE                        ← 1 Read tool call total per file
  FOR each fix in group:
    Edit with specific change            ← 1 Edit per fix, no re-read after
  DONE — move to next file
```

**Rules:**
- Read each file exactly once per loop — not once per fix
- **Never re-read a file after an Edit to verify** — trust the Edit tool
- Use surrounding context to scope edits when the same class appears multiple times
- One fix → one Edit call
- If Figma lookup gives a hex color → use that exact value, not a Tailwind approximation

**Target: ≤ 2 tool calls per fix** (1 Read amortized across fixes in same file + 1 Edit)

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
