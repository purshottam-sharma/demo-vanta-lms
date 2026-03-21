"""
retrospect.py — Tool usage analyzer for Vanta LMS agent runs.

Reads agents/logs/audit.jsonl (or a task-specific audit file), detects anti-patterns,
and outputs a structured JSON report.

Usage:
    python3 agents/shared/retrospect.py --task-id 86d2c0nmj
    python3 agents/shared/retrospect.py --log agents/logs/86d2c0nmj/audit.jsonl
    python3 agents/shared/retrospect.py --since 2026-03-20T02:00:00Z   # filter by time
"""

import argparse
import json
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path


# ─── Anti-pattern detectors ───────────────────────────────────────────────────

def detect_bash_file_reads(entries):
    """Bash used to read file content instead of Read tool (cat/head/tail/sed on non-system paths)."""
    hits = []
    system_prefixes = ('/proc/', '/sys/', '/dev/', 'journalctl', 'dmesg', 'ps aux', 'ss -')
    for i, e in enumerate(entries):
        if e['tool'] != 'Bash':
            continue
        cmd = e.get('input', {}).get('command', '')
        if any(s in cmd for s in system_prefixes):
            continue
        for bad_cmd in ('cat ', 'head ', 'tail -n', 'sed '):
            if bad_cmd in cmd and ('/' in cmd or '.' in cmd):
                # Exclude pipeline outputs being sent somewhere useful (e.g. | python3)
                # Flag only bare reads with no transformation value
                if '| python3' not in cmd and '| jq' not in cmd:
                    hits.append({
                        'index': i,
                        'command_snippet': cmd[:120],
                        'fix': 'Use Read tool instead of Bash cat/head/tail',
                    })
                    break
    return hits


def detect_polling_loops(entries):
    """3+ consecutive Bash calls probing the same URL, port, or checking the same condition."""
    hits = []
    window = 4  # look at N consecutive Bash calls
    bash_entries = [(i, e) for i, e in enumerate(entries) if e['tool'] == 'Bash']

    for j in range(len(bash_entries) - window + 1):
        window_cmds = [bash_entries[j + k][1].get('input', {}).get('command', '') for k in range(window)]
        # Check if all commands contain the same URL/port pattern
        urls = []
        for cmd in window_cmds:
            for token in cmd.split():
                if token.startswith('http') or ':' in token and any(c.isdigit() for c in token):
                    urls.append(token)
        url_counts = Counter(urls)
        for url, count in url_counts.items():
            if count >= 3:
                hits.append({
                    'index': bash_entries[j][0],
                    'repeated_target': url,
                    'repeat_count': count,
                    'fix': f"Use `ss -tlnp` or `lsof -i` once to find the port, not repeated curl probes.",
                })
                break

    return hits


def detect_verify_reads(entries):
    """Read called on same file path immediately after an Edit to that path."""
    hits = []
    for i in range(1, len(entries)):
        prev, curr = entries[i - 1], entries[i]
        if prev['tool'] != 'Edit' or curr['tool'] != 'Read':
            continue
        edited_path = prev.get('input', {}).get('file_path', '')
        read_path = curr.get('input', {}).get('file_path', '')
        if edited_path and edited_path == read_path:
            hits.append({
                'index': i,
                'file': read_path,
                'fix': 'Remove post-Edit verify reads. Trust the Edit tool — it confirms success.',
            })
    return hits


def detect_repeated_reads(entries):
    """Same file Read more than once in the session."""
    read_counts = defaultdict(list)
    for i, e in enumerate(entries):
        if e['tool'] == 'Read':
            path = e.get('input', {}).get('file_path', '')
            if path:
                read_counts[path].append(i)

    hits = []
    for path, indices in read_counts.items():
        if len(indices) > 1:
            hits.append({
                'file': path,
                'read_count': len(indices),
                'indices': indices,
                'fix': 'Read each file once per session. Store content in context — do not re-read.',
            })
    return hits


def detect_intermediate_image_reads(entries):
    """PNG/image file Read not at the very end of the session."""
    image_reads = [(i, e) for i, e in enumerate(entries)
                   if e['tool'] == 'Read' and
                   any(e.get('input', {}).get('file_path', '').endswith(ext)
                       for ext in ('.png', '.jpg', '.jpeg', '.gif', '.webp'))]

    if not image_reads:
        return []

    last_idx = len(entries) - 1
    hits = []
    for i, e in image_reads:
        # Flag if there are more than 5 tool calls after this image read (not at the end)
        if last_idx - i > 5:
            hits.append({
                'index': i,
                'file': e.get('input', {}).get('file_path', ''),
                'calls_after': last_idx - i,
                'fix': 'Only read final result images once, near the end of the run.',
            })
    return hits


def detect_temp_prompt_files(entries):
    """Bash writes a prompt to /tmp/*.txt then passes it to gemini.py via --prompt-file."""
    hits = []
    for i, e in enumerate(entries):
        if e['tool'] != 'Bash':
            continue
        cmd = e.get('input', {}).get('command', '')
        if ('prompt' in cmd.lower() and '/tmp/' in cmd and
                ('echo' in cmd or 'cat <<' in cmd or "heredoc" in cmd) and
                '.txt' in cmd):
            hits.append({
                'index': i,
                'command_snippet': cmd[:120],
                'fix': 'Pass prompt inline with --prompt "..." instead of writing to a temp file.',
            })
    return hits


def detect_subagent_for_cached_data(entries):
    """Agent tool spawned when the required input data already exists in /tmp (cache hit)."""
    # Look for Agent calls that are preceded by a Read of /tmp/figma_node_*.json
    # indicating data was already cached
    hits = []
    cached_files = set()
    for i, e in enumerate(entries):
        if e['tool'] == 'Read':
            path = e.get('input', {}).get('file_path', '')
            if '/tmp/' in path and any(x in path for x in ('figma', 'uispec', 'nodes', 'cache')):
                cached_files.add(path)
        if e['tool'] == 'Agent' and cached_files:
            prompt = e.get('input', {}).get('prompt', '')
            if any(keyword in prompt.lower() for keyword in ('figma', 'design agent', 'fetch')):
                hits.append({
                    'index': i,
                    'cached_files_available': list(cached_files),
                    'fix': 'Check /tmp/ for cached Figma data before spawning a subagent to fetch it again.',
                })
    return hits


# ─── Main analysis ─────────────────────────────────────────────────────────────

ANTI_PATTERN_REGISTRY = [
    {
        'id': 'bash_file_read',
        'name': 'Bash used to read files (should use Read tool)',
        'severity': 'medium',
        'skill_files': ['agents/visual-diff/SKILL.md', 'agents/design/SKILL.md'],
        'detect': detect_bash_file_reads,
        'budget_rule': 'prefer-read-over-bash',
    },
    {
        'id': 'polling_loop',
        'name': 'Repeated Bash probes for same URL/port (polling loop)',
        'severity': 'high',
        'skill_files': ['agents/visual-diff/SKILL.md'],
        'detect': detect_polling_loops,
        'budget_rule': 'no-polling',
    },
    {
        'id': 'verify_read_after_edit',
        'name': 'Read called immediately after Edit on same file (verify read)',
        'severity': 'medium',
        'skill_files': ['agents/visual-diff/SKILL.md'],
        'detect': detect_verify_reads,
        'budget_rule': 'trust-edit-no-verify',
    },
    {
        'id': 'repeated_file_read',
        'name': 'Same file read more than once',
        'severity': 'medium',
        'skill_files': ['agents/visual-diff/SKILL.md', 'agents/design/SKILL.md'],
        'detect': detect_repeated_reads,
        'budget_rule': 'read-once',
    },
    {
        'id': 'intermediate_image_read',
        'name': 'PNG/image read mid-session (not at end)',
        'severity': 'low',
        'skill_files': ['agents/visual-diff/SKILL.md'],
        'detect': detect_intermediate_image_reads,
        'budget_rule': 'images-at-end',
    },
    {
        'id': 'temp_prompt_file',
        'name': 'Prompt written to temp file instead of --prompt inline',
        'severity': 'low',
        'skill_files': ['agents/visual-diff/SKILL.md', 'agents/design/SKILL.md'],
        'detect': detect_temp_prompt_files,
        'budget_rule': 'inline-gemini-prompts',
    },
    {
        'id': 'subagent_for_cached_data',
        'name': 'Subagent spawned when cached input data already exists',
        'severity': 'high',
        'skill_files': ['agents/design/SKILL.md', '.claude/commands/build.md'],
        'detect': detect_subagent_for_cached_data,
        'budget_rule': 'check-cache-before-subagent',
    },
]

# Budget targets per agent type
BUDGET_TARGETS = {
    'orchestrator': 20,
    'design_agent': 15,
    'visual_diff_agent': 30,
    'frontend_agent': 20,
    'backend_agent': 20,
    'retrospect_agent': 10,
    'default': 25,
}


def load_entries(log_path: Path, since: str = None):
    if not log_path.exists():
        return []
    entries = []
    since_dt = datetime.fromisoformat(since.replace('Z', '+00:00')) if since else None
    with open(log_path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
                if since_dt:
                    ts = datetime.fromisoformat(entry['ts'].replace('Z', '+00:00'))
                    if ts < since_dt:
                        continue
                entries.append(entry)
            except (json.JSONDecodeError, KeyError):
                continue
    return entries


def analyze(entries, agent_type='default'):
    tool_counts = Counter(e['tool'] for e in entries)
    total = len(entries)
    target = BUDGET_TARGETS.get(agent_type, BUDGET_TARGETS['default'])

    anti_patterns_found = []
    total_waste = 0
    rules_violated = []

    for ap in ANTI_PATTERN_REGISTRY:
        hits = ap['detect'](entries)
        if hits:
            waste = max(0, len(hits) - 1)  # first occurrence may be necessary
            total_waste += waste
            anti_patterns_found.append({
                'id': ap['id'],
                'name': ap['name'],
                'severity': ap['severity'],
                'hit_count': len(hits),
                'estimated_waste': waste,
                'hits': hits[:5],  # cap at 5 examples
                'fix': hits[0].get('fix', '') if hits else '',
                'skill_files_to_patch': ap['skill_files'],
                'budget_rule': ap['budget_rule'],
            })
            rules_violated.append(ap['budget_rule'])

    # Severity score: 0-100 (100 = perfect, 0 = disaster)
    over_budget = max(0, total - target)
    efficiency_score = max(0, 100 - (over_budget * 3) - (total_waste * 2))

    return {
        'total_tool_calls': total,
        'target': target,
        'over_budget_by': over_budget,
        'efficiency_score': efficiency_score,
        'grade': 'A' if efficiency_score >= 90 else 'B' if efficiency_score >= 75 else 'C' if efficiency_score >= 60 else 'D',
        'tool_breakdown': dict(tool_counts.most_common()),
        'estimated_wasted_calls': total_waste,
        'anti_patterns': anti_patterns_found,
        'rules_violated': list(set(rules_violated)),
        'summary': _build_summary(total, target, anti_patterns_found, efficiency_score),
    }


def _build_summary(total, target, anti_patterns, score):
    lines = [f"Tool calls: {total} / target {target}"]
    if anti_patterns:
        high = [a for a in anti_patterns if a['severity'] == 'high']
        med = [a for a in anti_patterns if a['severity'] == 'medium']
        low = [a for a in anti_patterns if a['severity'] == 'low']
        if high:
            lines.append(f"HIGH severity: {', '.join(a['id'] for a in high)}")
        if med:
            lines.append(f"MED severity: {', '.join(a['id'] for a in med)}")
        if low:
            lines.append(f"LOW severity: {', '.join(a['id'] for a in low)}")
    lines.append(f"Efficiency score: {score}/100")
    return " | ".join(lines)


def main():
    parser = argparse.ArgumentParser(description='Analyze agent tool usage from audit log')
    parser.add_argument('--task-id', help='Task ID — reads agents/logs/{task_id}/audit.jsonl')
    parser.add_argument('--log', help='Path to audit JSONL file')
    parser.add_argument('--since', help='ISO datetime — only analyze entries after this time')
    parser.add_argument('--agent-type', default='default',
                        choices=list(BUDGET_TARGETS.keys()),
                        help='Agent type for budget target')
    parser.add_argument('--output', help='Write report JSON to this path')
    args = parser.parse_args()

    if args.task_id:
        log_path = Path(f'agents/logs/{args.task_id}/audit.jsonl')
        if not log_path.exists():
            # Fall back to global log
            log_path = Path('agents/logs/audit.jsonl')
    elif args.log:
        log_path = Path(args.log)
    else:
        log_path = Path('agents/logs/audit.jsonl')

    entries = load_entries(log_path, since=args.since)
    if not entries:
        result = {'error': f'No entries found in {log_path}', 'total_tool_calls': 0}
    else:
        result = analyze(entries, agent_type=args.agent_type)

    output = json.dumps(result, indent=2)
    print(output)

    if args.output:
        Path(args.output).write_text(output)


if __name__ == '__main__':
    main()
