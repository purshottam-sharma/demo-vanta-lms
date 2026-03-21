#!/usr/bin/env python3
"""
icon_audit_v2.py — Cross-reference Figma icon components vs current source code.

Runs figma_traverse.py --icons-only to get all icon component instances in a frame,
maps each Figma component name to a Lucide icon name, then cross-references the
source files to find mismatches.

Usage:
    python3 agents/shared/icon_audit_v2.py \\
      --file-key 8WV7cXkdYM65uT2vlfTQs5 \\
      --node-id 1:10517 \\
      --source-files apps/web/src/components/dashboard/DashboardBody.tsx \\
                     apps/web/src/components/dashboard/Sidebar.tsx \\
      --output /tmp/icon-audit-86d2c0nmj.json

Output JSON:
    {
      "total_icons": 24,
      "mismatches": [...],
      "matches": [...],
      "unresolved": [...]  // Figma icons with no Lucide mapping
    }
"""

import sys
import os
import json
import argparse
import re
import subprocess
from typing import Optional

# ─── Environment ──────────────────────────────────────────────────────────────

def load_env() -> dict:
    env: dict = {}
    env_path = os.path.join(os.path.dirname(__file__), "..", "..", ".env")
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, _, val = line.partition("=")
                    env[key.strip()] = val.strip().strip('"').strip("'")
    return {
        "token":   os.environ.get("FIGMA_API_TOKEN") or env.get("FIGMA_API_TOKEN", ""),
        "file_id": os.environ.get("FIGMA_FILE_ID")   or env.get("FIGMA_FILE_ID", ""),
    }


# ─── Source file analysis ──────────────────────────────────────────────────────

def parse_lucide_imports(source_path: str) -> dict:
    """
    Parse a TSX/JSX/TS file and extract all lucide-react imports.
    Returns: { "Building2": { "source_file": "...", "line": 3 }, ... }
    """
    if not os.path.exists(source_path):
        return {}

    with open(source_path) as f:
        content = f.read()

    imports: dict = {}
    # Match: import { A, B, C } from 'lucide-react'
    pattern = re.compile(
        r"import\s*\{([^}]+)\}\s*from\s*['\"]lucide-react['\"]",
        re.MULTILINE,
    )
    for match in pattern.finditer(content):
        block = match.group(1)
        # Count the line number of the start of the import
        line_num = content[: match.start()].count("\n") + 1
        for name in re.split(r"[,\n]", block):
            name = name.strip()
            if name:
                # Handle aliased imports: { Building2 as BldIcon }
                actual = re.split(r"\s+as\s+", name, maxsplit=1)[0].strip()
                if actual:
                    imports[actual] = {
                        "source_file": source_path,
                        "line": line_num,
                    }
    return imports


def find_icon_usage_context(source_path: str, icon_name: str) -> Optional[str]:
    """
    Find the label/text closest to where `icon_name` is used in the source file.
    Returns a short context hint string.
    """
    if not os.path.exists(source_path):
        return None

    with open(source_path) as f:
        lines = f.readlines()

    # Find all lines where the icon name appears as a component or value
    pattern = re.compile(rf"\b{re.escape(icon_name)}\b")
    for i, line in enumerate(lines):
        if pattern.search(line):
            # Look ±5 lines for a label string
            context_range = lines[max(0, i - 5): min(len(lines), i + 6)]
            label_match = re.search(r"['\"`]([A-Z][A-Za-z\s]{2,30})['\"`]", "".join(context_range))
            if label_match:
                return f"Near label: '{label_match.group(1)}' (line {i + 1})"
            return f"Line {i + 1}: {line.strip()[:80]}"
    return None


def build_source_icon_map(source_files: list) -> dict:
    """
    Build a combined map of all Lucide icons imported across all source files.
    Returns: { "Building2": { "source_file": "...", "line": 3 }, ... }
    """
    combined: dict = {}
    for path in source_files:
        imports = parse_lucide_imports(path)
        combined.update(imports)
    return combined


# ─── Icon fetching via figma_traverse.py ──────────────────────────────────────

def fetch_figma_icons(file_key: str, node_id: str, use_cache: bool = True) -> list:
    """
    Run figma_traverse.py --icons-only and return the parsed JSON list.
    Uses subprocess so we reuse the existing traversal + caching logic.
    """
    script = os.path.join(os.path.dirname(__file__), "figma_traverse.py")
    cmd = [
        sys.executable, script,
        "--file-key", file_key,
        "--node-id", node_id,
        "--icons-only",
    ]
    if use_cache:
        cmd.append("--cache")

    print(f"[traverse] Running figma_traverse.py --icons-only...", file=sys.stderr)
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        raise RuntimeError(
            f"figma_traverse.py failed:\n{result.stderr}\n{result.stdout}"
        )

    # stderr is informational; stdout is the JSON
    if result.stderr:
        print(result.stderr, end="", file=sys.stderr)

    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"figma_traverse.py returned invalid JSON: {e}\n{result.stdout[:500]}")


# ─── Audit logic ──────────────────────────────────────────────────────────────

def build_location_hint(node: dict) -> str:
    """Build a human-readable location string for an icon node."""
    parts = []
    if node.get("parent_id"):
        parts.append(f"parent:{node['parent_id']}")
    name = node.get("name", "")
    if name:
        parts.append(name)
    layout = node.get("layout", {})
    if layout.get("x") is not None and layout.get("y") is not None:
        parts.append(f"@({layout['x']},{layout['y']})")
    return " / ".join(parts) if parts else node.get("id", "unknown")


def audit_icons(
    figma_icons: list,
    source_icon_map: dict,
    source_files: list,
) -> dict:
    """
    Cross-reference Figma icon nodes vs source code imports.
    Returns the full audit report dict.
    """
    mismatches = []
    matches = []
    unresolved = []

    # Deduplicate by lucide_name to avoid reporting the same icon type N times
    # but DO track all locations
    seen_pairs: set = set()

    for node in figma_icons:
        comp = node.get("component") or {}
        figma_component = comp.get("component_name", node.get("name", ""))
        lucide_name = comp.get("lucide_name")

        location = build_location_hint(node)

        if not lucide_name:
            unresolved.append({
                "location": location,
                "figma_component": figma_component,
                "node_id": node.get("id"),
                "note": "Could not map to a Lucide icon name",
            })
            continue

        # Check if this Lucide name is in the source
        source_entry = source_icon_map.get(lucide_name)
        pair_key = (figma_component, lucide_name)

        if source_entry:
            # Icon name matches — record as match
            if pair_key not in seen_pairs:
                seen_pairs.add(pair_key)
                context = find_icon_usage_context(source_entry["source_file"], lucide_name)
                matches.append({
                    "location": location,
                    "figma_component": figma_component,
                    "figma_icon_name": lucide_name,
                    "current_code_icon": lucide_name,
                    "source_file": source_entry["source_file"],
                    "context_hint": context,
                })
        else:
            # Icon not found in source — check if a different name is used nearby
            # Look for icons that could be "close" (same stem, different suffix)
            close_matches = [
                k for k in source_icon_map
                if lucide_name.lower() in k.lower() or k.lower() in lucide_name.lower()
            ]
            current_code_icon = close_matches[0] if close_matches else None

            if pair_key not in seen_pairs:
                seen_pairs.add(pair_key)
                context_hint = None
                if current_code_icon:
                    entry = source_icon_map[current_code_icon]
                    context_hint = find_icon_usage_context(entry["source_file"], current_code_icon)

                mismatches.append({
                    "location": location,
                    "figma_component": figma_component,
                    "figma_icon_name": lucide_name,
                    "current_code_icon": current_code_icon,
                    "source_file": source_icon_map.get(current_code_icon, {}).get("source_file") if current_code_icon else None,
                    "context_hint": context_hint or f"Search source files for icon near '{node.get('name', '')}' element",
                })

    return {
        "total_icons": len(figma_icons),
        "unique_icon_types": len(seen_pairs) + len(unresolved),
        "mismatch_count": len(mismatches),
        "match_count": len(matches),
        "unresolved_count": len(unresolved),
        "mismatches": mismatches,
        "matches": matches,
        "unresolved": unresolved,
        "source_files_scanned": source_files,
        "all_source_icons": sorted(source_icon_map.keys()),
    }


# ─── CLI ──────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Cross-reference Figma icon components vs current TSX/JSX source code."
    )
    parser.add_argument("--file-key",     help="Figma file key (overrides FIGMA_FILE_ID in .env)")
    parser.add_argument("--node-id",      required=True, help="Figma node ID, e.g. '1:10517'")
    parser.add_argument("--source-files", nargs="+", default=[], help="TSX/JSX files to scan for lucide-react imports")
    parser.add_argument("--output",       help="Write JSON report to this path (default: stdout)")
    parser.add_argument("--no-cache",     action="store_true", help="Skip cache, force fresh Figma API fetch")
    args = parser.parse_args()

    env = load_env()
    file_key = args.file_key or env["file_id"]

    if not env["token"]:
        print(json.dumps({"error": "FIGMA_API_TOKEN not set. Add it to .env or environment."}))
        sys.exit(1)
    if not file_key:
        print(json.dumps({"error": "Provide --file-key or set FIGMA_FILE_ID in .env"}))
        sys.exit(1)

    node_id = args.node_id.replace("-", ":")

    # Resolve source file paths relative to project root
    project_root = os.path.join(os.path.dirname(__file__), "..", "..")
    resolved_sources = []
    for sf in args.source_files:
        if os.path.isabs(sf):
            resolved_sources.append(sf)
        else:
            resolved_sources.append(os.path.normpath(os.path.join(project_root, sf)))

    try:
        # 1. Get Figma icons via figma_traverse.py
        figma_icons = fetch_figma_icons(
            file_key=file_key,
            node_id=node_id,
            use_cache=not args.no_cache,
        )
        print(f"[audit] Found {len(figma_icons)} icon nodes in Figma.", file=sys.stderr)

        # 2. Parse source files for lucide-react imports
        source_icon_map = build_source_icon_map(resolved_sources)
        print(f"[audit] Found {len(source_icon_map)} Lucide icons in source files.", file=sys.stderr)

        # 3. Cross-reference
        report = audit_icons(figma_icons, source_icon_map, resolved_sources)

        output_json = json.dumps(report, indent=2)

        if args.output:
            os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
            with open(args.output, "w") as f:
                f.write(output_json)
            print(f"[ok] Report written to {args.output}", file=sys.stderr)
            # Print summary to stdout
            print(f"\n=== Icon Audit Summary ===")
            print(f"Total Figma icons: {report['total_icons']}")
            print(f"Unique icon types: {report['unique_icon_types']}")
            print(f"Matches:           {report['match_count']}")
            print(f"Mismatches:        {report['mismatch_count']}")
            print(f"Unresolved:        {report['unresolved_count']}")
            if report["mismatches"]:
                print(f"\nMismatches:")
                for m in report["mismatches"]:
                    code_icon = m.get("current_code_icon") or "(not found in code)"
                    print(f"  Figma: {m['figma_icon_name']:25s}  Code: {code_icon:25s}  @ {m['location']}")
        else:
            print(output_json)

    except KeyboardInterrupt:
        sys.exit(0)
    except Exception as e:
        print(json.dumps({"error": str(e)}), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
