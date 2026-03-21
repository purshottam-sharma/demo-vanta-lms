#!/usr/bin/env python3
"""
figma_traverse.py — Full Figma node tree traversal with component instance resolution.

Walks EVERY node in a Figma frame recursively, resolves component instances to their
exact library names, and emits structured JSON descriptors for every node. This replaces
the lossy UISpec/Vision approach with direct Figma-node-to-JSX data, the way Figma Make works.

Usage:
    python3 agents/shared/figma_traverse.py \\
      --file-key 8WV7cXkdYM65uT2vlfTQs5 \\
      --node-id 1:10517 \\
      --output /tmp/nodes-86d2c0nmj.json

    python3 agents/shared/figma_traverse.py \\
      --file-key 8WV7cXkdYM65uT2vlfTQs5 \\
      --node-id 1:10517 \\
      --icons-only

    python3 agents/shared/figma_traverse.py \\
      --file-key 8WV7cXkdYM65uT2vlfTQs5 \\
      --node-id 1:10517 \\
      --tree \\
      --depth 4

Requires in .env:
    FIGMA_API_TOKEN=...
    FIGMA_FILE_ID=...     (used as default if --file-key not provided)
"""

import sys
import os
import json
import argparse
import urllib.request
import urllib.parse
import time
import re
from typing import Optional

# ─── Environment ──────────────────────────────────────────────────────────────

def load_env() -> dict:
    """Load FIGMA_API_TOKEN and FIGMA_FILE_ID from environment or .env file."""
    env: dict = {}
    env_path = os.path.join(os.path.dirname(__file__), "..", "..", ".env")
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, _, val = line.partition("=")
                    env[key.strip()] = val.strip().strip('"').strip("'")
    token   = os.environ.get("FIGMA_API_TOKEN") or env.get("FIGMA_API_TOKEN", "")
    file_id = os.environ.get("FIGMA_FILE_ID")   or env.get("FIGMA_FILE_ID", "")
    return {"token": token, "file_id": file_id}


# ─── Figma REST helpers ────────────────────────────────────────────────────────

def figma_get(token: str, path: str) -> dict:
    url = f"https://api.figma.com/v1{path}"
    req = urllib.request.Request(url, headers={"X-Figma-Token": token})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read())


# ─── Color helpers ────────────────────────────────────────────────────────────

def rgba_to_hex(color: dict) -> str:
    """Convert Figma RGBA (0-1 floats) to #rrggbb hex string."""
    r = round(color.get("r", 0) * 255)
    g = round(color.get("g", 0) * 255)
    b = round(color.get("b", 0) * 255)
    return f"#{r:02x}{g:02x}{b:02x}"


def extract_first_solid_fill(node: dict) -> Optional[str]:
    """Return the hex color of the first SOLID fill, or None."""
    for fill in node.get("fills", []):
        if fill.get("visible", True) is False:
            continue
        if fill.get("type") == "SOLID":
            color = fill.get("color")
            if color:
                return rgba_to_hex(color)
    return None


def extract_stroke_css(node: dict) -> Optional[str]:
    """Return a CSS border string like '1px solid #e3e8ef', or None."""
    strokes = node.get("strokes", [])
    if not strokes:
        return None
    first = strokes[0]
    color = first.get("color")
    if not color:
        return None
    weight = node.get("strokeWeight", 1)
    hex_color = rgba_to_hex(color)
    return f"{weight}px solid {hex_color}"


def extract_effects(node: dict) -> list:
    """Summarize effects (shadows, blurs) into structured dicts."""
    results = []
    for effect in node.get("effects", []):
        if not effect.get("visible", True):
            continue
        etype = effect.get("type", "")
        if etype in ("DROP_SHADOW", "INNER_SHADOW"):
            color = effect.get("color", {})
            results.append({
                "type": etype,
                "offsetX": effect.get("offset", {}).get("x", 0),
                "offsetY": effect.get("offset", {}).get("y", 0),
                "blur": effect.get("radius", 0),
                "spread": effect.get("spread", 0),
                "color": rgba_to_hex(color) if color else None,
                "opacity": round(color.get("a", 1.0), 3) if color else 1.0,
            })
        elif etype in ("LAYER_BLUR", "BACKGROUND_BLUR"):
            results.append({
                "type": etype,
                "blur": effect.get("radius", 0),
            })
    return results


# ─── Icon name resolution ─────────────────────────────────────────────────────

def kebab_to_pascal(name: str) -> str:
    """Convert kebab-case, snake_case, or space-separated words to PascalCase.
    'arrow-right' → 'ArrowRight', 'icons8_hint 1' → 'Icons8Hint 1' (preserves digits).
    """
    # Split on hyphens and underscores only; preserve spaces as-is for readability
    parts = re.split(r"[-_]", name)
    return "".join(word.capitalize() for word in parts if word)


def extract_lucide_name(component_name: str) -> Optional[str]:
    """
    Given a Figma component name, extract the icon leaf name in PascalCase.

    Handles standard Lucide/icon library naming:
      - 'Icons/Lucide/Building2'           → 'Building2'
      - 'icon/arrow-right'                 → 'ArrowRight'
      - 'mdi:shield-check'                 → 'ShieldCheck'
      - 'Iconoir / add-circle'             → 'AddCircle'
      - 'System Icons / bell-notification' → 'BellNotification'

    Also handles custom icon naming (used in this project):
      - 'icon=dashinactive'                → 'Dashinactive' (custom — use semantic map)
      - 'icon=department_outline'          → 'DepartmentOutline'
      - 'isActive=True, IsOpen=False'      → None (variant property, not an icon name)
      - 'role=Admin'                       → None (variant property)

    Returns the PascalCase name, or None if not recognizable as an icon name.
    """
    if not component_name:
        return None

    name = component_name.strip()

    # Skip variant property strings (contain commas — these are component set variants)
    if "," in name:
        return None

    # Handle "key=value" custom naming: 'icon=dashinactive' → 'dashinactive'
    if "=" in name and "/" not in name and ":" not in name:
        key, _, val = name.partition("=")
        key = key.strip().lower()
        val = val.strip()
        # Only treat as icon name if the key suggests it's an icon
        if key in ("icon", "icons", "ic", "i"):
            return kebab_to_pascal(val) if val else None
        # Other key=value pairs (role=Admin, isActive=True) are not icon names
        return None

    # Pattern: "Namespace/IconName" or "Namespace / IconName"
    # Take the last segment after the final slash (or colon for mdi: style)
    for sep in ("/", ":", "\\"):
        if sep in name:
            parts = [p.strip() for p in name.split(sep)]
            name = parts[-1]
            break

    # Strip trailing variant notation like " (20)" or " [outline]"
    name = re.sub(r"\s*[\(\[].*$", "", name).strip()

    # Convert to PascalCase
    return kebab_to_pascal(name) if name else None


# ─── Semantic icon mapping (custom Figma icons → best Lucide equivalent) ──────

# When Figma uses custom-named SVG icons (not Lucide), this table maps the
# extracted name to the closest Lucide semantic equivalent.
# Key: PascalCase from extract_lucide_name(); Value: Lucide component name.
CUSTOM_ICON_TO_LUCIDE: dict = {
    # Sidebar navigation icons
    "Dashinactive":          "LayoutDashboard",
    "CourseInactove":        "BookOpen",         # typo in Figma: "inactove"
    "Schedule":              "CalendarClock",
    "Teacher":               "GraduationCap",
    "Class":                 "BookOpen",
    "Students":              "Users",
    "Attendance":            "UserCheck",
    "Analytics":             "BarChart2",
    "Policy":                "Shield",
    "Chat":                  "MessageCircle",
    "Feedback":              "Mail",
    "Icons8Hint1":           "Lightbulb",        # icons8_hint 1 (underscore, no space)
    "Icons8Hint 1":          "Lightbulb",        # icons8_hint 1 (with space from Figma)
    "Rolesdisactive":        "Users",
    "Usermanagedisactive":   "Users",
    "DepartmentOutline":     "Building2",
    "Settings":              "Settings",
    # Main frame / Navbar icons
    "Dashboard":             "Menu",             # Navbar hamburger/menu icon (named 'icon=dashboard' in Figma)
    "Navbar":                None,               # The Navbar component itself — not a single icon
    "DepartmentFilled":      "Building2",
    "CourseActive":          "BookOpen",
    "SortColumn":            "ArrowUpDown",
    # Stat card icons (same icon reused)
    "Risk":                  "AlertTriangle",
    # Avatar / user profile
    "User":                  "User",
}


# ─── Layout extraction ────────────────────────────────────────────────────────

_LAYOUT_MODE_MAP = {
    "HORIZONTAL": "HORIZONTAL",
    "VERTICAL": "VERTICAL",
    "NONE": "NONE",
}

def extract_layout(node: dict) -> dict:
    bbox = node.get("absoluteBoundingBox") or {}
    layout: dict = {
        "mode": _LAYOUT_MODE_MAP.get(node.get("layoutMode", ""), "NONE"),
        "x": round(bbox.get("x", 0)),
        "y": round(bbox.get("y", 0)),
        "width": round(bbox.get("width", 0)),
        "height": round(bbox.get("height", 0)),
    }

    if node.get("layoutMode") in ("HORIZONTAL", "VERTICAL"):
        layout["primary_align"]   = node.get("primaryAxisAlignItems", "MIN")
        layout["counter_align"]   = node.get("counterAxisAlignItems", "MIN")
        layout["sizing_h"]        = node.get("primaryAxisSizingMode",  "FIXED") if node.get("layoutMode") == "HORIZONTAL" else node.get("counterAxisSizingMode", "FIXED")
        layout["sizing_v"]        = node.get("counterAxisSizingMode",  "FIXED") if node.get("layoutMode") == "HORIZONTAL" else node.get("primaryAxisSizingMode", "FIXED")
        layout["padding_top"]     = node.get("paddingTop", 0)
        layout["padding_bottom"]  = node.get("paddingBottom", 0)
        layout["padding_left"]    = node.get("paddingLeft", 0)
        layout["padding_right"]   = node.get("paddingRight", 0)
        layout["gap"]             = node.get("itemSpacing", 0)
        layout["clip_content"]    = node.get("clipsContent", False)

    return layout


# ─── Text extraction ──────────────────────────────────────────────────────────

def extract_text(node: dict, token_map: dict) -> Optional[dict]:
    if node.get("type") != "TEXT":
        return None
    style = node.get("style", {})
    color_hex = None
    color_token = None
    for fill in node.get("fills", []):
        if fill.get("type") == "SOLID" and fill.get("visible", True):
            color_hex = rgba_to_hex(fill["color"])
            color_token = token_map.get(color_hex)
            break

    lh = style.get("lineHeightPx")
    lh_mode = style.get("lineHeightUnit", "")
    if lh_mode == "AUTO":
        lh = None

    return {
        "content":        node.get("characters", ""),
        "font_family":    style.get("fontFamily"),
        "font_size":      style.get("fontSize"),
        "font_weight":    style.get("fontWeight"),
        "line_height":    round(lh) if lh else None,
        "letter_spacing": style.get("letterSpacing", 0),
        "color":          color_hex,
        "color_token":    color_token,
        "align":          style.get("textAlignHorizontal", "LEFT"),
    }


# ─── Visual extraction ────────────────────────────────────────────────────────

def extract_visual(node: dict, token_map: dict) -> dict:
    bg = extract_first_solid_fill(node)
    border = extract_stroke_css(node)
    corner = node.get("cornerRadius")
    if corner is None:
        radii = node.get("rectangleCornerRadii")
        if radii and len(radii) == 4 and len(set(radii)) == 1:
            corner = radii[0]

    return {
        "bg":           bg,
        "bg_token":     token_map.get(bg) if bg else None,
        "border":       border,
        "border_token": token_map.get(border) if border else None,
        "corner_radius": corner,
        "opacity":      round(node.get("opacity", 1.0), 3),
        "effects":      extract_effects(node),
        "visible":      node.get("visible", True),
    }


# ─── Component instance extraction ───────────────────────────────────────────

def extract_component(node: dict, component_map: dict) -> Optional[dict]:
    # Figma REST API returns type="INSTANCE" for component instances.
    # Figma MCP / newer API may return "COMPONENT_INSTANCE".
    if node.get("type") not in ("COMPONENT_INSTANCE", "INSTANCE"):
        return None
    comp_id   = node.get("componentId", "")
    comp_name = component_map.get(comp_id, node.get("name", ""))

    # Parse variant properties from componentProperties
    variant_props: dict = {}
    for prop_name, prop_val in node.get("componentProperties", {}).items():
        # prop_name may contain "#NNNNNN" suffix — strip it
        clean_key = re.sub(r"#\w+$", "", prop_name).strip()
        variant_props[clean_key] = prop_val.get("value", "")

    # Infer set_name from the component name (first segment before "/")
    set_name = comp_name.split("/")[0].strip() if "/" in comp_name else comp_name

    raw_lucide = extract_lucide_name(comp_name)
    # Fall back to semantic map for custom icon names
    lucide_name = raw_lucide
    if raw_lucide and raw_lucide not in (
        # Filter out obviously-not-icon PascalCase names
        "True", "False", "Admin", "None"
    ):
        lucide_name = CUSTOM_ICON_TO_LUCIDE.get(raw_lucide, raw_lucide)
    else:
        lucide_name = None

    return {
        "component_id":   comp_id,
        "component_name": comp_name,
        "set_name":       set_name,
        "variant_props":  variant_props,
        "raw_icon_name":  raw_lucide,         # PascalCase from component name, pre-semantic-map
        "lucide_name":    lucide_name,        # Final Lucide component name (or closest equivalent)
    }


# ─── Tree walker ─────────────────────────────────────────────────────────────

def walk_tree(
    node: dict,
    component_map: dict,
    token_map: dict,
    depth: int = 0,
    parent_id: Optional[str] = None,
    max_depth: Optional[int] = None,
    flat_list: Optional[list] = None,
    tree_mode: bool = False,
) -> dict:
    """
    Recursively walk the Figma node tree.
    In flat mode (default): appends every node to flat_list and returns it.
    In tree mode (--tree): returns a nested dict.
    """
    if flat_list is None:
        flat_list = []

    node_type = node.get("type", "UNKNOWN")
    layout    = extract_layout(node)
    visual    = extract_visual(node, token_map)
    text      = extract_text(node, token_map)
    component = extract_component(node, component_map)

    descriptor: dict = {
        "id":        node.get("id", ""),
        "name":      node.get("name", ""),
        "type":      node_type,
        "depth":     depth,
        "parent_id": parent_id,
        "layout":    layout,
        "visual":    visual,
    }
    if text:
        descriptor["text"] = text
    if component:
        descriptor["component"] = component

    if tree_mode:
        descriptor["children"] = []

    flat_list.append(descriptor)

    # Recurse into children
    if max_depth is None or depth < max_depth:
        for child in node.get("children", []):
            child_desc = walk_tree(
                child,
                component_map,
                token_map,
                depth=depth + 1,
                parent_id=node.get("id"),
                max_depth=max_depth,
                flat_list=flat_list if not tree_mode else None,
                tree_mode=tree_mode,
            )
            if tree_mode:
                descriptor["children"].append(child_desc)

    return descriptor


# ─── Component map builder ────────────────────────────────────────────────────

def build_component_map(token: str, file_key: str) -> dict:
    """
    Fetch all components from the Figma file and return a dict:
        { component_id: component_full_name }
    """
    try:
        resp = figma_get(token, f"/files/{file_key}/components")
        components = resp.get("meta", {}).get("components", [])
        return {c["node_id"]: c["name"] for c in components if "node_id" in c and "name" in c}
    except Exception as e:
        print(f"[warn] Could not fetch components map: {e}", file=sys.stderr)
        return {}


# ─── Token map builder ────────────────────────────────────────────────────────

def build_token_map(token: str, file_key: str) -> dict:
    """
    Build a hex→token_name map from Figma local variables.
    Returns: { "#rrggbb": "color/text/primary", ... }
    """
    token_map: dict = {}
    try:
        resp = figma_get(token, f"/files/{file_key}/variables/local")
        variables = resp.get("meta", {}).get("variables", {})
        collections = resp.get("meta", {}).get("variableCollections", {})

        for var_id, var in variables.items():
            if var.get("resolvedType") != "COLOR":
                continue
            name = var.get("name", "")
            # Get the default mode value
            coll_id = var.get("variableCollectionId", "")
            coll = collections.get(coll_id, {})
            default_mode = coll.get("defaultModeId", "")
            value_by_mode = var.get("valuesByMode", {})
            value = value_by_mode.get(default_mode)
            if isinstance(value, dict) and "r" in value:
                hex_color = rgba_to_hex(value)
                token_map[hex_color] = name
    except Exception as e:
        print(f"[warn] Could not fetch variables: {e}", file=sys.stderr)
    return token_map


# ─── Cache helpers ────────────────────────────────────────────────────────────

CACHE_TTL_SECONDS = 3600  # 1 hour


def cache_path(file_key: str, node_id: str) -> str:
    safe_node = node_id.replace(":", "-").replace(",", "_")
    return f"/tmp/figma-traverse-{file_key[:8]}-{safe_node}.json"


def load_cache(file_key: str, node_id: str) -> Optional[dict]:
    path = cache_path(file_key, node_id)
    if not os.path.exists(path):
        return None
    age = time.time() - os.path.getmtime(path)
    if age > CACHE_TTL_SECONDS:
        return None
    with open(path) as f:
        return json.load(f)


def save_cache(file_key: str, node_id: str, data: dict) -> None:
    path = cache_path(file_key, node_id)
    with open(path, "w") as f:
        json.dump(data, f)


# ─── Main traversal entry point ───────────────────────────────────────────────

def traverse(
    file_key: str,
    node_id: str,
    token: str,
    max_depth: Optional[int] = None,
    icons_only: bool = False,
    tree_mode: bool = False,
    use_cache: bool = False,
) -> list:
    """
    Traverse the Figma node tree and return a flat list (or nested tree) of descriptors.
    """
    # Check cache first
    if use_cache:
        cached = load_cache(file_key, node_id)
        if cached is not None:
            print(f"[cache] Using cached traversal from /tmp", file=sys.stderr)
            nodes = cached
            if icons_only:
                return filter_icons(nodes if isinstance(nodes, list) else _flatten_tree(nodes))
            return nodes

    # Fetch node tree from Figma API
    print(f"[api] Fetching node tree for {node_id} from file {file_key}...", file=sys.stderr)
    api_node_id = urllib.parse.quote(node_id)
    resp = figma_get(token, f"/files/{file_key}/nodes?ids={api_node_id}&depth=8")
    nodes_data = resp.get("nodes", {})

    # Normalize node_id key (Figma returns the key with colon or URL-encoded)
    root_node = None
    for key, val in nodes_data.items():
        if val and "document" in val:
            root_node = val["document"]
            break

    if root_node is None:
        raise ValueError(f"Node '{node_id}' not found in Figma file '{file_key}'")

    # Build lookup maps
    print(f"[api] Fetching component map...", file=sys.stderr)
    component_map = build_component_map(token, file_key)
    print(f"[api] Found {len(component_map)} components.", file=sys.stderr)

    print(f"[api] Fetching design token map...", file=sys.stderr)
    token_map = build_token_map(token, file_key)
    print(f"[api] Found {len(token_map)} color tokens.", file=sys.stderr)

    # Walk the tree
    flat_list: list = []
    if tree_mode:
        tree = walk_tree(
            root_node,
            component_map,
            token_map,
            depth=0,
            parent_id=None,
            max_depth=max_depth,
            flat_list=None,
            tree_mode=True,
        )
        result = tree
    else:
        walk_tree(
            root_node,
            component_map,
            token_map,
            depth=0,
            parent_id=None,
            max_depth=max_depth,
            flat_list=flat_list,
            tree_mode=False,
        )
        result = flat_list

    # Cache raw result
    if use_cache:
        save_cache(file_key, node_id, result)

    if icons_only:
        flat = result if isinstance(result, list) else _flatten_tree(result)
        return filter_icons(flat)

    return result


def filter_icons(nodes: list) -> list:
    """Return only component instance nodes that look like icons."""
    icons = []
    for node in nodes:
        if node.get("type") not in ("COMPONENT_INSTANCE", "INSTANCE"):
            continue
        comp = node.get("component", {})
        if not comp:
            continue
        name_lower = (comp.get("component_name", "") + " " + node.get("name", "")).lower()
        if "icon" in name_lower or comp.get("lucide_name"):
            icons.append(node)
    return icons


def _flatten_tree(tree_node: dict) -> list:
    """Convert a nested tree dict back to a flat list (for cache + icons_only)."""
    result = [tree_node]
    for child in tree_node.get("children", []):
        result.extend(_flatten_tree(child))
    return result


# ─── CLI ──────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Walk a Figma node tree and emit structured JSON descriptors for every node."
    )
    parser.add_argument("--file-key",  help="Figma file key (overrides FIGMA_FILE_ID from .env)")
    parser.add_argument("--node-id",   required=True, help="Figma node ID, e.g. '1:10517'")
    parser.add_argument("--output",    help="Write JSON to this file path (default: stdout)")
    parser.add_argument("--depth",     type=int, default=None, help="Max tree depth to traverse (default: unlimited)")
    parser.add_argument("--icons-only", action="store_true", help="Only output COMPONENT_INSTANCE nodes that look like icons")
    parser.add_argument("--tree",      action="store_true", help="Output nested tree instead of flat array")
    parser.add_argument("--cache",     action="store_true", help="Use cached result if < 1 hour old")
    args = parser.parse_args()

    env = load_env()
    token    = env["token"]
    file_key = args.file_key or env["file_id"]

    if not token:
        print(json.dumps({"error": "FIGMA_API_TOKEN not set. Add it to .env or environment."}))
        sys.exit(1)
    if not file_key:
        print(json.dumps({"error": "Provide --file-key or set FIGMA_FILE_ID in .env"}))
        sys.exit(1)

    # Normalize node_id (URL uses dash, API uses colon)
    node_id = args.node_id.replace("-", ":")

    try:
        result = traverse(
            file_key=file_key,
            node_id=node_id,
            token=token,
            max_depth=args.depth,
            icons_only=args.icons_only,
            tree_mode=args.tree,
            use_cache=args.cache,
        )

        output_json = json.dumps(result, indent=2)

        if args.output:
            os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
            with open(args.output, "w") as f:
                f.write(output_json)
            print(f"[ok] Written {len(result) if isinstance(result, list) else 1} nodes to {args.output}", file=sys.stderr)
        else:
            print(output_json)

    except KeyboardInterrupt:
        sys.exit(0)
    except Exception as e:
        print(json.dumps({"error": str(e)}), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
