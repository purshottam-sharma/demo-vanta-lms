#!/usr/bin/env python3
"""
Fetch exact measurements and design tokens from the Figma API for a named node.

Used by the Visual Diff Agent during fix loops to get authoritative px values,
hex colors, and font specs — replacing Vision guesses with real Figma data.

Usage:
    python3 agents/shared/figma_lookup.py --node-name "School Health Index"
    python3 agents/shared/figma_lookup.py --node-name "Progress Bar" --output /tmp/figma-node.json
    python3 agents/shared/figma_lookup.py --node-id "123:456"

Requires in environment (or .env file):
    FIGMA_API_TOKEN=...
    FIGMA_FILE_ID=...

Output (stdout, JSON):
    {
      "node_id": "123:456",
      "node_name": "School Health Index",
      "size": { "width": 502, "height": 157 },
      "fills": [{ "type": "SOLID", "color": "#22c55e", "opacity": 1.0 }],
      "strokes": [],
      "corner_radius": 2,
      "font": { "family": "Inter", "size": 14, "weight": 500 },
      "padding": { "top": 16, "right": 16, "bottom": 16, "left": 16 },
      "gap": 8,
      "children_summary": [
        { "name": "Segment", "count": 30, "width": 14, "height": 10, "corner_radius": 2, "fill": "#22c55e" }
      ]
    }
"""

import sys
import os
import json
import argparse
import urllib.request
import urllib.parse


def load_env() -> dict:
    """Load FIGMA_API_TOKEN and FIGMA_FILE_ID from environment or .env file."""
    env = {}
    # Try .env in project root (two levels up from agents/shared/)
    env_path = os.path.join(os.path.dirname(__file__), "..", "..", ".env")
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, _, val = line.partition("=")
                    env[key.strip()] = val.strip().strip('"').strip("'")

    token = os.environ.get("FIGMA_API_TOKEN") or env.get("FIGMA_API_TOKEN")
    file_id = os.environ.get("FIGMA_FILE_ID") or env.get("FIGMA_FILE_ID")
    return {"token": token, "file_id": file_id}


def figma_get(token: str, path: str) -> dict:
    url = f"https://api.figma.com/v1{path}"
    req = urllib.request.Request(url, headers={"X-Figma-Token": token})
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read())


def rgba_to_hex(color: dict) -> str:
    """Convert Figma RGBA (0-1 floats) to hex string."""
    r = round(color.get("r", 0) * 255)
    g = round(color.get("g", 0) * 255)
    b = round(color.get("b", 0) * 255)
    return f"#{r:02x}{g:02x}{b:02x}"


def extract_fills(node: dict) -> list:
    fills = []
    for fill in node.get("fills", []):
        if fill.get("type") == "SOLID":
            fills.append({
                "type": "SOLID",
                "color": rgba_to_hex(fill["color"]),
                "opacity": round(fill.get("opacity", 1.0), 3),
            })
        elif fill.get("type") in ("GRADIENT_LINEAR", "GRADIENT_RADIAL"):
            stops = [
                {"color": rgba_to_hex(s["color"]), "position": round(s["position"], 3)}
                for s in fill.get("gradientStops", [])
            ]
            fills.append({"type": fill["type"], "stops": stops})
    return fills


def extract_font(node: dict) -> dict | None:
    style = node.get("style") or {}
    if not style:
        return None
    return {
        "family": style.get("fontFamily"),
        "size": style.get("fontSize"),
        "weight": style.get("fontWeight"),
        "line_height": style.get("lineHeightPx"),
        "letter_spacing": style.get("letterSpacing"),
    }


def extract_children_summary(node: dict) -> list:
    """Summarise repeated children (e.g. 30 identical segments)."""
    children = node.get("children", [])
    if not children:
        return []

    # Group by name
    groups: dict[str, list] = {}
    for child in children:
        name = child.get("name", "unnamed")
        groups.setdefault(name, []).append(child)

    summary = []
    for name, items in groups.items():
        first = items[0]
        bbox = first.get("absoluteBoundingBox") or first.get("size") or {}
        entry: dict = {
            "name": name,
            "count": len(items),
            "width": round(bbox.get("width", 0)),
            "height": round(bbox.get("height", 0)),
        }
        if "cornerRadius" in first:
            entry["corner_radius"] = first["cornerRadius"]
        fills = extract_fills(first)
        if fills:
            entry["fill"] = fills[0]["color"] if fills[0]["type"] == "SOLID" else fills
        summary.append(entry)
    return summary


def find_node_by_name(node: dict, name_lower: str) -> dict | None:
    """DFS search for first node whose name matches (case-insensitive)."""
    if node.get("name", "").lower() == name_lower:
        return node
    for child in node.get("children", []):
        result = find_node_by_name(child, name_lower)
        if result:
            return result
    return None


def extract_node_info(node: dict) -> dict:
    bbox = node.get("absoluteBoundingBox") or {}
    size = {
        "width": round(bbox.get("width", 0)),
        "height": round(bbox.get("height", 0)),
    }
    padding = {}
    if "paddingTop" in node:
        padding = {
            "top": node.get("paddingTop", 0),
            "right": node.get("paddingRight", 0),
            "bottom": node.get("paddingBottom", 0),
            "left": node.get("paddingLeft", 0),
        }
    result: dict = {
        "node_id": node.get("id"),
        "node_name": node.get("name"),
        "type": node.get("type"),
        "size": size,
        "fills": extract_fills(node),
        "strokes": [
            {"color": rgba_to_hex(s["color"]), "weight": s.get("strokeWeight", 1)}
            for s in node.get("strokes", [])
            if s.get("color")
        ],
    }
    if "cornerRadius" in node:
        result["corner_radius"] = node["cornerRadius"]
    if "itemSpacing" in node:
        result["gap"] = node["itemSpacing"]
    if padding:
        result["padding"] = padding
    font = extract_font(node)
    if font:
        result["font"] = font
    children_summary = extract_children_summary(node)
    if children_summary:
        result["children_summary"] = children_summary
    return result


def lookup(node_name: str | None = None, node_id: str | None = None) -> dict:
    env = load_env()
    if not env["token"]:
        raise ValueError("FIGMA_API_TOKEN not set. Add it to .env or environment.")
    if not env["file_id"]:
        raise ValueError("FIGMA_FILE_ID not set. Add it to .env or environment.")

    token = env["token"]
    file_id = env["file_id"]

    if node_id:
        # Fetch specific node directly
        resp = figma_get(token, f"/files/{file_id}/nodes?ids={urllib.parse.quote(node_id)}")
        nodes = resp.get("nodes", {})
        node = next(iter(nodes.values()), {}).get("document") if nodes else None
        if not node:
            raise ValueError(f"Node ID '{node_id}' not found in Figma file")
        return extract_node_info(node)

    if node_name:
        # Search the full file tree
        print(f"Fetching Figma file {file_id} to search for '{node_name}'...", flush=True)
        resp = figma_get(token, f"/files/{file_id}")
        doc = resp.get("document", {})
        found = find_node_by_name(doc, node_name.lower())
        if not found:
            raise ValueError(f"Node named '{node_name}' not found in Figma file")
        return extract_node_info(found)

    raise ValueError("Either --node-name or --node-id is required")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fetch exact measurements from Figma for a named node")
    parser.add_argument("--node-name", help="Node name to search for (case-insensitive)")
    parser.add_argument("--node-id", help="Exact Figma node ID (e.g. '123:456')")
    parser.add_argument("--output", help="Write JSON to this file path instead of stdout")
    args = parser.parse_args()

    if not args.node_name and not args.node_id:
        parser.print_help()
        sys.exit(1)

    try:
        result = lookup(node_name=args.node_name, node_id=args.node_id)
        output = json.dumps(result, indent=2)
        if args.output:
            os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
            with open(args.output, "w") as f:
                f.write(output)
            print(f"Written to {args.output}", flush=True)
        else:
            print(output)
    except Exception as e:
        print(json.dumps({"error": str(e)}))
        sys.exit(1)
