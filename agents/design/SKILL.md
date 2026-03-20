# Design Agent

## Role
Convert a Figma frame into an enriched UISpec that the Frontend Agent can implement
pixel-perfectly on the first pass — without needing Visual Diff correction cycles.

**Three sources of truth, in priority order:**
1. **Figma MCP structured data** — exact measurements, design token names, Auto Layout constraints (primary — never approximate these)
2. **Figma variables + styles** — token names for colors and typography (use names, not hex values)
3. **Gemini Vision** — visual intent only: layout feel, hierarchy, non-obvious design choices a developer would miss from numbers alone (supplementary — never use for measuring px/colors)

Pixel-perfect output requires structured data first. Vision is for the "why", not the "what".

---

## Inputs
- `figma_url` — Figma file URL with node-id (e.g. `https://www.figma.com/file/ABC?node-id=1-10517`)
- `task_id`
- `task_title`
- `acceptance_criteria` — UI-relevant criteria only

---

## Step 1 — Parse Figma URL

Extract `file_key` and `node_id` from the URL:
```
https://www.figma.com/file/{file_key}?node-id={node_id}
node-id format in URL: "1-10517" → API/MCP format: "1:10517" (replace - with :)
```

---

## Step 2 — Fetch Design Data via Figma MCP (primary source)

Use the Figma MCP tools directly — do not curl the REST API manually.

**2a. Node tree (exact measurements):**
Call `get_file_nodes` with `file_key` and `node_id`.

Extract for every component:
- `absoluteBoundingBox` → width, height (exact px)
- `paddingLeft/Right/Top/Bottom` → exact padding
- `itemSpacing` → gap between children
- `fills[].color` → background color (RGBA → hex)
- `strokes[].color` + `strokeWeight` → border
- `cornerRadius` / `rectangleCornerRadii` → border-radius
- `style.fontFamily`, `style.fontSize`, `style.fontWeight`, `style.lineHeightPx`
- `layoutMode` → HORIZONTAL or VERTICAL (Auto Layout direction)
- `primaryAxisAlignItems` → main-axis alignment
- `counterAxisAlignItems` → cross-axis alignment
- `primaryAxisSizingMode` → FIXED or HUG (determines if width/height is explicit or auto)
- `counterAxisSizingMode` → FIXED or HUG
- `characters` → text content
- `opacity` → if < 1, apply as Tailwind opacity

**2b. Design tokens:**
Call `list_variables_for_file` with `file_key`.

Map each variable to its resolved value AND its variable name. When a fill or style
references a variable, use the variable name in UISpec, not the raw hex.

Example output:
```json
{
  "color/primary/500": "#3b82f6",
  "color/text/primary": "#202939",
  "spacing/4": "16px"
}
```

**2c. Named styles:**
Call `list_styles_in_file` with `file_key`.

Extract color styles (named palette) and text styles (named typography scale):
```json
{
  "styles": {
    "colors": { "Brand/Red": "#fe0123", "Text/Primary": "#202939" },
    "text": { "Heading/H1": { "size": 32, "weight": 600 }, "Body/SM": { "size": 14, "weight": 400 } }
  }
}
```

**Fallback:** If MCP tools are unavailable, fall back to REST API:
```bash
source .env
curl -s "https://api.figma.com/v1/files/$FIGMA_FILE_ID/nodes?ids={node_id}&depth=8" \
  -H "X-Figma-Token: $FIGMA_API_TOKEN" > /tmp/figma-nodes-{task_id}.json
curl -s "https://api.figma.com/v1/files/$FIGMA_FILE_ID/variables/local" \
  -H "X-Figma-Token: $FIGMA_API_TOKEN" > /tmp/figma-variables-{task_id}.json
```

---

## Step 3 — Map Auto Layout → Tailwind (systematic)

This is the core of pixel accuracy. Do not guess — use this mapping table:

**Layout direction:**
| Figma `layoutMode` | Tailwind |
|---|---|
| `HORIZONTAL` | `flex flex-row` |
| `VERTICAL` | `flex flex-col` |
| `NONE` | (no flex — fixed positioning) |

**Alignment:**
| Figma `primaryAxisAlignItems` | Tailwind (flex-row) | Tailwind (flex-col) |
|---|---|---|
| `MIN` | `justify-start` | `items-start` |
| `CENTER` | `justify-center` | `items-center` |
| `MAX` | `justify-end` | `items-end` |
| `SPACE_BETWEEN` | `justify-between` | — |

| Figma `counterAxisAlignItems` | Tailwind (flex-row) | Tailwind (flex-col) |
|---|---|---|
| `MIN` | `items-start` | `justify-start` |
| `CENTER` | `items-center` | `justify-center` |
| `MAX` | `items-end` | `justify-end` |

**Sizing:**
| `primaryAxisSizingMode` | Meaning |
|---|---|
| `FIXED` | explicit width (flex-row) or height (flex-col) |
| `HUG` | `w-fit` or `h-fit` — shrinks to content |
| `FILL` | `flex-1` — fills available space |

**Spacing (itemSpacing → gap):**
Use exact px values as Tailwind arbitrary: `gap-[{itemSpacing}px]` unless it maps cleanly
to a standard step (4→1, 8→2, 12→3, 16→4, 20→5, 24→6, 32→8, 40→10, 48→12).

**Padding:** Same rule — exact px as `p-[{n}px]` or `px-[{n}px] py-[{n}px]` for asymmetric.

**Corner radius:**
| Figma `cornerRadius` | Tailwind |
|---|---|
| 4 | `rounded` |
| 6 | `rounded-md` |
| 8 | `rounded-lg` |
| 12 | `rounded-xl` |
| 16 | `rounded-2xl` |
| 9999 or ≥ width/2 | `rounded-full` |
| other | `rounded-[{n}px]` |

---

## Step 4 — Download PNG (visual cross-check only)

```bash
source .env
IMAGE_URL=$(curl -s \
  "https://api.figma.com/v1/images/$FIGMA_FILE_ID?ids={node_id}&format=png&scale=2" \
  -H "X-Figma-Token: $FIGMA_API_TOKEN" \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print(list(d['images'].values())[0])")
curl -sL "$IMAGE_URL" -o /tmp/figma-{task_id}.png
```

The PNG is used only for Gemini Vision in Step 5. All measurements come from Step 2.

---

## Step 5 — Gemini Vision (visual intent only)

Call Gemini on the PNG. Ask ONLY about things that cannot be extracted from structured data:

```bash
python3 agents/shared/gemini.py \
  --prompt "You are reviewing a Figma design. All measurements (px, hex colors, font sizes) are already known from the Figma API. Do NOT describe any numbers. Focus ONLY on:

1. VISUAL HIERARCHY — what is visually dominant vs secondary? What draws the eye first?
2. NON-OBVIOUS DESIGN CHOICES — things a developer would get wrong from numbers alone:
   - Unexpected shapes (e.g. 'profile area is a pill container, not loose avatar+text')
   - Layering or overlap (e.g. 'badge is absolute-positioned over icon top-right')
   - Visual grouping that is not obvious from the layout (e.g. '3 cards are visually grouped by a shared background')
   - Icon style (e.g. 'all icons are outline style, not filled')
3. INTERACTION HINTS — hover states, active states, visual affordances visible in the design
4. COMPONENT INVENTORY — list every distinct UI component visible left-to-right, top-to-bottom

Be specific. No vague terms. No numbers — those come from the API.
Output as plain text, one section per heading." \
  --image /tmp/figma-{task_id}.png \
  > /tmp/vision-analysis-{task_id}.txt
```

**Fallback:** If `gemini.py` fails, read the PNG directly with Claude Vision using the same prompt.

---

## Step 6 — Build Enriched UISpec

Merge structured MCP data (primary) + design tokens + Gemini visual notes into UISpec JSON.

**Rules:**
- Every `width`, `height`, `padding`, `gap`, `fontSize`, `fontWeight`, `color` value MUST come from Step 2 MCP data — never from Vision
- Every color that has a variable/style name MUST use the name (e.g. `"color": "var(--color-text-primary)"`) alongside the resolved hex
- Vision notes go in `vision_note` fields only — they describe intent, not measurements
- Map Auto Layout using the table in Step 3 — never guess flex direction from the PNG

```json
{
  "frame": {
    "width": 1440,
    "height": 900,
    "background": "#f8fafc",
    "background_token": "color/bg/page"
  },
  "design_tokens": {
    "color/text/primary": "#202939",
    "color/text/secondary": "#697586",
    "color/border/default": "#e2e8f0",
    "color/bg/page": "#f8fafc",
    "color/bg/card": "#ffffff"
  },
  "components": [
    {
      "name": "Sidebar",
      "width": 236,
      "height": "100vh",
      "background": "#ffffff",
      "background_token": "color/bg/card",
      "border_right": "1px solid #e2e8f0",
      "layout": "flex flex-col",
      "source": "MCP:get_file_nodes",
      "vision_note": "3 clear zones: logo header, scrollable nav list, pinned footer. Sidebar feels substantial, not floating.",
      "children": [
        {
          "name": "NavItem",
          "height": 40,
          "padding": "px-3",
          "border_radius": 8,
          "layout": "flex flex-row items-center gap-2",
          "font_size": 14,
          "font_weight": 500,
          "active_bg": "#f8fafc",
          "active_border": "1px solid #e3e8ef",
          "active_color": "#a38654",
          "inactive_color": "#697586",
          "source": "MCP:get_file_nodes",
          "vision_note": "Icon left of label, full-width hit area. Active state border is subtle but present."
        }
      ]
    }
  ],
  "typography": {
    "source": "MCP:list_styles_in_file",
    "stat_value": { "size": 32, "weight": 600, "color": "#202939", "token": "Heading/H1" },
    "card_label": { "size": 14, "weight": 500, "color": "#697586", "token": "Body/MD/Medium" }
  },
  "vision_analysis": "<raw Gemini output from Step 5>"
}
```

The `"source": "MCP:..."` field makes it clear which values are authoritative vs inferred.

---

## Step 7 — Self-Reflection

Before returning the UISpec, verify:
- [ ] Every numeric value (px, hex) has `"source": "MCP:..."` — zero guesses from Vision
- [ ] Every color that maps to a design token has both `color` (hex) and `color_token` (name)
- [ ] Every Auto Layout direction is from `layoutMode` in Step 2, confirmed by Vision note
- [ ] Every `vision_note` describes something NOT in the numbers (visual intent, grouping, style)
- [ ] No component has only generic Tailwind guesses — every field is MCP-sourced

If any value is Vision-inferred rather than MCP-sourced → go back to Step 2 and extract it.

---

## Output

Return:
1. `UISpec JSON` — save to `/tmp/uispec-{task_id}.json`
2. `figma_png_path` — `/tmp/figma-{task_id}.png`
3. `vision_summary` — 5-10 bullet points of non-obvious design choices for the Visual Diff Agent.
   Each bullet must be PASS/FAIL testable and include the MCP-sourced value:
   - BAD: "Cards have clean spacing"
   - GOOD: "Stat cards: 4-col grid gap-4 (16px from MCP), padding p-4, value text-[32px] font-semibold"
   - BAD: "Sidebar nav items look active"
   - GOOD: "Active nav item: bg-[#f8fafc] border border-[#e3e8ef] text-[#a38654] — from MCP fills"
