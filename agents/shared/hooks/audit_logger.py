"""
PostToolUse hook: logs every tool call as a JSON line.

Writes to:
  1. agents/logs/audit.jsonl          (global, always)
  2. agents/logs/{task_id}/audit.jsonl (task-specific, if active task can be inferred)

Task ID is inferred by checking for the most recently modified workorder.json
under agents/logs/. This is best-effort — logging never blocks tool execution.
"""

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path


def _find_active_task_id() -> str | None:
    """Find the task_id of the most recently updated workorder.json."""
    log_dir = Path("agents/logs")
    if not log_dir.exists():
        return None
    try:
        workorders = sorted(
            log_dir.glob("*/workorder.json"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
        if workorders:
            data = json.loads(workorders[0].read_text())
            return data.get("task_id")
    except Exception:
        pass
    return None


def main():
    try:
        raw = sys.stdin.read()
        if not raw.strip():
            sys.exit(0)

        data = json.loads(raw)

        entry = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "tool": data.get("tool_name", "unknown"),
            "input": data.get("tool_input", {}),
            "response_snippet": str(data.get("tool_response", ""))[:300],
        }

        log_dir = Path("agents/logs")
        log_dir.mkdir(parents=True, exist_ok=True)

        # 1. Always write to global log
        with open(log_dir / "audit.jsonl", "a") as f:
            f.write(json.dumps(entry) + "\n")

        # 2. Also write to task-specific log if we can identify the active task
        task_id = _find_active_task_id()
        if task_id:
            task_log_dir = log_dir / task_id
            task_log_dir.mkdir(parents=True, exist_ok=True)
            with open(task_log_dir / "audit.jsonl", "a") as f:
                f.write(json.dumps(entry) + "\n")

    except Exception:
        # Never block tool execution due to logging errors
        pass

    sys.exit(0)


if __name__ == "__main__":
    main()
