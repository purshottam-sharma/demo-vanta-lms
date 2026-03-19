# Design Agent

## Role
Convert a Figma frame into an enriched UISpec that the Frontend Agent can implement
pixel-perfectly on the first pass — without needing multiple Visual Diff correction cycles.

The Design Agent combines two sources of truth:
- **Figma JSON** — exact measurements (px, hex, font weight, border radius)
- **Claude Vision** — visual intent (layout direction, hierarchy, proportions, design choices a developer would miss from numbers alone)

Both are required. Numbers without visual context produce the wrong layout.
Visual context without numbers produces approximate styling.

---

## Inputs
- `figma_url` — Figma file URL with node-id (e.g. `https://www.figma.com/file/ABC?node-id=1-10517`)
- `task_title` — used to scope the analysis
- `acceptance_criteria` — UI-relevant criteria only

---

## Step 1 — Parse Figma URL

Extract `file_id` and `node_id` from the URL:
```
https://www.figma.com/file/{file_id}?node-id={node_id}
node-id format: "1-10517" → API format: "1:10517"
```

Read `FIGMA_FILE_ID` and `FIGMA_API_TOKEN` from `.env` if not provided:
```bash
source .env
```

---

## Step 2 — Fetch Figma Node JSON

Fetch the node tree at depth 8 to capture all nested components:
```bash
curl -s "https://api.figma.com/v1/files/$FIGMA_FILE_ID/nodes?ids={node_id}&depth=8" \
  -H "X-Figma-Token: $FIGMA_API_TOKEN" \
  > /tmp/figma-nodes-{task_id}.json
```

Extract for every component:
- `absoluteBoundingBox` — x, y, width, height
- `paddingLeft/Right/Top/Bottom`
- `itemSpacing` (gap)
- `fills` → background color (hex)
- `strokes` → border color + width
- `cornerRadius` / `rectangleCornerRadii`
- `style.fontFamily`, `style.fontSize`, `style.fontWeight`, `style.letterSpacing`
- `layoutMode` — HORIZONTAL or VERTICAL (auto-layout direction)
- `primaryAxisAlignItems`, `counterAxisAlignItems` (flex alignment)
- `characters` — text content

---

## Step 3 — Download Figma Frame as PNG

```bash
IMAGE_URL=$(curl -s \
  "https://api.figma.com/v1/images/$FIGMA_FILE_ID?ids={node_id}&format=png&scale=2" \
  -H "X-Figma-Token: $FIGMA_API_TOKEN" \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print(list(d['images'].values())[0])")

curl -sL "$IMAGE_URL" -o /tmp/figma-{task_id}.png
```

If export fails, log a warning and continue — JSON data is sufficient for measurements.

---

## Step 4 — Vision Analysis (the enrichment layer)

Read the downloaded PNG and analyse it with Claude Vision using this prompt:

```
You are a senior UI engineer analysing a Figma design frame to extract implementation
instructions for a React + Tailwind developer.

Look at this design carefully. For each major component or section, describe:

1. LAYOUT DIRECTION
   - Is the primary axis horizontal or vertical?
   - Is it a flex row, flex col, or grid?
   - Example: "Quick action cards: flex row, 4 columns, equal width"

2. VISUAL HIERARCHY
   - What is visually dominant (large, bold, prominent)?
   - What is secondary (smaller, muted, supporting)?
   - Example: "Stat card: value (32px bold) dominates over label (12px muted) above it"

3. SPACING FEEL
   - Are sections tightly packed or generously spaced?
   - Do elements have visible breathing room or are they dense?

4. NON-OBVIOUS DESIGN CHOICES
   - Things a developer would get wrong from numbers alone
   - Example: "The notification icon has a red dot badge in the top-right corner"
   - Example: "The profile area is a pill-shaped container, not just an avatar + text"
   - Example: "The sidebar footer is a full-width button, not just text with an icon"

5. INTERACTION HINTS
   - Hover states visible in the design
   - Active/selected states
   - Any visual affordances (chevrons, arrows, badges)

6. COMPONENT INVENTORY
   List every distinct UI component visible, left-to-right, top-to-bottom.

Be specific and concrete. Avoid vague terms like "clean" or "modern".
A developer reading your output should be able to implement this without seeing the image.
```

Store the Vision output as `vision_analysis` in the UISpec.

---

## Step 5 — Build Enriched UISpec

Merge JSON measurements + Vision analysis into a single UISpec JSON.

Structure:
```json
{
  "frame": {
    "width": 1440,
    "height": 900,
    "background": "#f8fafc"
  },
  "components": [
    {
      "name": "Sidebar",
      "width": 236,
      "height": "100vh",
      "background": "#ffffff",
      "border_right": "1px solid #e2e8f0",
      "layout": "flex col",
      "vision_note": "3 clear zones: logo header (72px, border-bottom), scrollable nav list, pinned footer button",
      "children": [
        {
          "name": "SidebarHeader",
          "height": 72,
          "padding": "0 16px",
          "layout": "flex row, items-center, justify-between",
          "vision_note": "Logo mark (red 32px square with V) + wordmark, close X on mobile only"
        },
        {
          "name": "SidebarSearch",
          "height": 40,
          "border_radius": 12,
          "background": "#f9f8f5",
          "border": "1px solid #e2e8f0",
          "layout": "flex row, items-center, gap 8px",
          "vision_note": "Search icon left, placeholder text, tags row below (pill chips)"
        },
        {
          "name": "NavItem",
          "height": 40,
          "padding": "0 12px",
          "border_radius": 8,
          "font_size": 14,
          "font_weight": 500,
          "active_bg": "#f8fafc",
          "active_border": "1px solid #e3e8ef",
          "active_color": "#a38654",
          "inactive_color": "#697586",
          "vision_note": "Icon (16px) left of label, full-width, active state has visible border"
        },
        {
          "name": "SidebarFooter",
          "height": 40,
          "padding": "0 12px",
          "border_top": "1px solid #e2e8f0",
          "vision_note": "Full-width button with Settings icon + Settings label — NOT just text"
        }
      ]
    },
    {
      "name": "Navbar",
      "height": 72,
      "background": "#ffffff",
      "border_bottom": "1px solid #e2e8f0",
      "layout": "flex row, items-center, px-24",
      "vision_note": "Search bar fills left space (max 360px). Right side: notification button (48x48 square pill) + profile pill (218x48). Both have bg #f8fafc with border.",
      "children": [
        {
          "name": "NavbarSearch",
          "width": 360,
          "height": 48,
          "border_radius": 12,
          "background": "#f9f8f5",
          "border": "1px solid #e2e8f0",
          "vision_note": "Search icon + placeholder. Full input, not icon-only button."
        },
        {
          "name": "NotificationButton",
          "width": 48,
          "height": 48,
          "border_radius": 12,
          "background": "#f8fafc",
          "border": "1px solid #e2e8f0",
          "vision_note": "Bell icon centered. Red dot badge top-right corner (8px, absolute positioned)."
        },
        {
          "name": "ProfilePill",
          "width": 218,
          "height": 48,
          "border_radius": 12,
          "background": "#f8fafc",
          "border": "1px solid #e2e8f0",
          "padding": "0 8px",
          "gap": 8,
          "vision_note": "Avatar (32px circle) + name/email stack + ChevronDown icon. It is a PILL CONTAINER, not loose elements."
        }
      ]
    }
  ],
  "typography": {
    "stat_value": { "size": 32, "weight": 600, "color": "#202939" },
    "card_label": { "size": 14, "weight": 500, "color": "#697586" },
    "nav_item": { "size": 14, "weight": 500 },
    "body": { "size": 14, "weight": 400, "color": "#697586" },
    "font_family": "Inter"
  },
  "color_tokens": {
    "text_primary": "#202939",
    "text_secondary": "#697586",
    "border": "#e2e8f0",
    "bg_page": "#f8fafc",
    "bg_card": "#ffffff",
    "bg_input": "#f9f8f5",
    "accent": "#a38654",
    "brand_red": "#fe0123",
    "success": "#2fc475",
    "warning": "#a38654",
    "danger": "#e37a72",
    "info": "#0ba5ec",
    "purple": "#9b8afb"
  },
  "vision_analysis": "<raw Vision output here>"
}
```

---

## Step 6 — Self-Reflection

Before returning the UISpec, verify:
- [ ] Every component from the Vision inventory appears in `components`
- [ ] Every `vision_note` calls out something a developer would miss from numbers alone
- [ ] Color tokens are exact hex values from Figma JSON, not approximations
- [ ] Layout directions (HORIZONTAL/VERTICAL) from Figma JSON match Vision observations
- [ ] Typography sizes and weights are exact from Figma JSON
- [ ] No component is listed with generic values — every field is Figma-sourced

If any component has only generic Tailwind guesses (not Figma-sourced values), revisit the JSON and re-extract.

---

## Output

Return:
1. `UISpec JSON` — the enriched spec (save to `/tmp/uispec-{task_id}.json`)
2. `figma_png_path` — `/tmp/figma-{task_id}.png` (for Visual Diff Agent to reuse)
3. `vision_summary` — 3-5 bullet points of the most important non-obvious design choices the Frontend Agent must not miss

The Orchestrator passes all three to the Frontend Agent.
