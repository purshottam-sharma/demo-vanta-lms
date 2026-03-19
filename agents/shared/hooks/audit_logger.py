"""
PostToolUse hook: logs every tool call as a JSON line to agents/logs/audit.jsonl
Input: JSON on stdin with tool_name, tool_input, tool_response
"""

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

def main():
    try:
        raw = sys.stdin.read()
        if not raw.strip():
            sys.exit(0)

        data = json.loads(raw)

        log_dir = Path("agents/logs")
        log_dir.mkdir(parents=True, exist_ok=True)

        entry = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "tool": data.get("tool_name", "unknown"),
            "input": data.get("tool_input", {}),
            "response_snippet": str(data.get("tool_response", ""))[:300],
        }

        with open(log_dir / "audit.jsonl", "a") as f:
            f.write(json.dumps(entry) + "\n")

    except Exception:
        # Never block tool execution due to logging errors
        pass

    sys.exit(0)

if __name__ == "__main__":
    main()
