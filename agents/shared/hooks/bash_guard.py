"""
PreToolUse hook: blocks dangerous bash commands.
Exit 0 = allow, exit 2 + print message = block.
Input: JSON on stdin with tool_name, tool_input
"""

import json
import re
import sys

BLOCKED_PATTERNS = [
    (r"rm\s+-rf\s+/", "rm -rf / is not allowed"),
    (r"rm\s+--no-preserve-root", "rm --no-preserve-root is not allowed"),
    (r"curl\s+.*\|\s*(bash|sh|zsh|python)", "curl pipe to shell is not allowed"),
    (r"wget\s+.*\|\s*(bash|sh|zsh|python)", "wget pipe to shell is not allowed"),
    (r"kill\s+-9\s+1\b", "kill -9 PID 1 is not allowed"),
    (r":\(\)\{.*\|.*:\&.*\}", "fork bomb pattern is not allowed"),
    (r"dd\s+if=/dev/zero\s+of=/dev/[sh]d", "dd to block device is not allowed"),
    (r"mkfs\.", "mkfs (format disk) is not allowed"),
    (r">\s*/dev/[sh]d[a-z]", "write to block device is not allowed"),
    (r"chmod\s+-R\s+777\s+/", "chmod 777 on root is not allowed"),
]

def main():
    try:
        raw = sys.stdin.read()
        if not raw.strip():
            sys.exit(0)

        data = json.loads(raw)
        tool_input = data.get("tool_input", {})
        command = tool_input.get("command", "")

        for pattern, reason in BLOCKED_PATTERNS:
            if re.search(pattern, command, re.IGNORECASE):
                print(f"BLOCKED by bash_guard: {reason}", file=sys.stderr)
                sys.exit(2)

    except Exception:
        pass

    sys.exit(0)

if __name__ == "__main__":
    main()
