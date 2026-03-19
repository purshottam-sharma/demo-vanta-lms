"""
PreToolUse hook: blocks dangerous GitHub MCP operations.
Exit 0 = allow, exit 2 + print message = block.
Input: JSON on stdin with tool_name, tool_input
"""

import json
import sys

PROTECTED_BRANCHES = {"main", "develop", "master", "production"}

def main():
    try:
        raw = sys.stdin.read()
        if not raw.strip():
            sys.exit(0)

        data = json.loads(raw)
        tool_name = data.get("tool_name", "")
        tool_input = data.get("tool_input", {})

        # Block push/merge directly to protected branches
        if tool_name in ("mcp__github__push_files", "mcp__github__create_or_update_file"):
            branch = tool_input.get("branch", "")
            if branch in PROTECTED_BRANCHES:
                print(f"BLOCKED by github_guard: direct push to '{branch}' is not allowed. Use a feature branch.", file=sys.stderr)
                sys.exit(2)

        # Block merging into protected branches (allow pipeline-controlled merges only)
        if tool_name == "mcp__github__merge_pull_request":
            print("BLOCKED by github_guard: agents cannot merge PRs — merging is a manual human step.", file=sys.stderr)
            sys.exit(2)

        # Block branch deletion of protected branches
        if tool_name == "mcp__github__delete_branch":
            branch = tool_input.get("branch", "")
            if branch in PROTECTED_BRANCHES:
                print(f"BLOCKED by github_guard: deletion of protected branch '{branch}' is not allowed.", file=sys.stderr)
                sys.exit(2)

        # Block repository deletion
        if tool_name == "mcp__github__delete_repository":
            print("BLOCKED by github_guard: repository deletion is not allowed.", file=sys.stderr)
            sys.exit(2)

    except Exception:
        pass

    sys.exit(0)

if __name__ == "__main__":
    main()
