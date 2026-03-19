"""
PreToolUse hook: blocks destructive SQL operations.
Exit 0 = allow, exit 2 + print message = block.
Input: JSON on stdin with tool_name, tool_input
"""

import json
import re
import sys

BLOCKED_PATTERNS = [
    (r"\bDROP\s+(TABLE|DATABASE|SCHEMA|INDEX)\b", "DROP TABLE/DATABASE is not allowed"),
    (r"\bTRUNCATE\b", "TRUNCATE is not allowed"),
    (r"\bDELETE\s+FROM\b(?!.*\bWHERE\b)", "DELETE without WHERE is not allowed"),
    (r"\bALTER\s+TABLE\b.*\bDROP\s+COLUMN\b", "DROP COLUMN is not allowed"),
    (r"\bDROP\s+COLUMN\b", "DROP COLUMN is not allowed"),
]

def main():
    try:
        raw = sys.stdin.read()
        if not raw.strip():
            sys.exit(0)

        data = json.loads(raw)
        tool_input = data.get("tool_input", {})

        # Check query field (varies by MCP server)
        query = tool_input.get("query", tool_input.get("sql", tool_input.get("statement", "")))

        for pattern, reason in BLOCKED_PATTERNS:
            if re.search(pattern, query, re.IGNORECASE | re.DOTALL):
                print(f"BLOCKED by postgres_guard: {reason}", file=sys.stderr)
                sys.exit(2)

    except Exception:
        pass

    sys.exit(0)

if __name__ == "__main__":
    main()
