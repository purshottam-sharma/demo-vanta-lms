# Tool Budget — Shared Rules for All Agents

Every agent in the pipeline must stay within its tool call budget.
Violating these rules is the **single biggest cause of slow, expensive runs**.

## Budget Targets

| Agent | Target | Hard Limit |
|---|---|---|
| Orchestrator | 20 | 35 |
| Design Agent | 15 | 25 |
| Visual Diff Agent (full 2-loop run) | 30 | 50 |
| Frontend / Backend Agent | 20 | 35 |
| Retrospect Agent | 10 | 15 |

---

## The Rules

### 1. Use Read, not Bash, for file content
```
# WRONG — 1 Bash call wasted + output truncated
cat /tmp/uispec.json | head -400

# RIGHT — 1 Read call, full file, correct tool
Read /tmp/uispec.json
```
Reserve Bash for: system commands, running scripts, network calls, git.

---

### 2. Find the dev server port once — never poll
```
# WRONG — 10 Bash calls to discover port
sleep 8 && curl :4200 → 404
sleep 10 && curl :4200 → 404
... (8 more times)

# RIGHT — 1 Bash call
ss -tlnp | grep node   → gives you the exact port immediately
```
Then pass that port directly to playwright_screenshot.py.

---

### 3. Check for cached data before spawning a subagent
```
# WRONG — spawns a 25-call Design Agent when data exists
ls /tmp/figma_node_86d2c0nmj.json  # exists, 605KB
→ Agent tool: Design Agent (25 calls to re-fetch the same data)

# RIGHT — 2 calls total
Read /tmp/figma_node_86d2c0nmj.json   (already exists)
python3 agents/shared/figma_lookup.py --node-name "..."
```
Before spawning a subagent to fetch data, check `/tmp/` for a cached version.

---

### 4. Read each file exactly once per session
```
# WRONG — 4 calls to read the same UISpec
cat uispec.json | head -400         # call 1
cat uispec.json | tail -n +400      # call 2
cat uispec.json | tail -n +800      # call 3
Read truncated-output.txt           # call 4

# RIGHT — 1 call
Read /tmp/uispec-86d2c0nmj.json     # gets all 960 lines at once
```
If a file is too large for one Read, use `limit` and `offset` — still 1-2 calls max.

---

### 5. Never re-read a file after editing it
```
# WRONG — Edit + verify Read = 2 calls, should be 1
Edit apps/web/src/components/Sidebar.tsx  (changes applied)
Read apps/web/src/components/Sidebar.tsx  (checking it worked)

# RIGHT — 1 call
Edit apps/web/src/components/Sidebar.tsx
```
The Edit tool reports success. Trust it.

---

### 6. Group all edits to a file — read once, edit many
```
# WRONG — 3 Reads + 3 Edits for fixes in the same file
Read DashboardBody.tsx
Edit DashboardBody.tsx  (fix 1)
Read DashboardBody.tsx  (re-read for fix 2!)
Edit DashboardBody.tsx  (fix 2)

# RIGHT — 1 Read + N Edits
Read DashboardBody.tsx        (once)
Edit DashboardBody.tsx        (fix 1)
Edit DashboardBody.tsx        (fix 2)
Edit DashboardBody.tsx        (fix 3)
```

---

### 7. Inline Gemini prompts — never write to a temp file first
```
# WRONG — 2 calls (write file + run gemini)
Bash: echo "Analyse this design..." > /tmp/prompt.txt
Bash: python3 gemini.py --prompt-file /tmp/prompt.txt ...

# RIGHT — 1 call
Bash: python3 gemini.py --prompt "Analyse this design..." ...
```

---

### 8. Read images only at the end, only once
```
# WRONG — 3 intermediate image reads
Read /tmp/rendered.png    (after loop 1, just to show user)
Run pixelmatch
Read /tmp/diff.png
Edit source files
Read /tmp/rendered.png    (again, unnecessarily)
Run pixelmatch
Read /tmp/rendered.png    (final)

# RIGHT — 2 reads at the end
Run pixelmatch
Read /tmp/diff.png        (understand what's wrong)
Edit source files
Run pixelmatch
Read /tmp/rendered.png    (final result for user)
```

---

## Anti-Pattern Detection

Run `python3 agents/shared/retrospect.py --task-id {id}` to auto-detect violations.

The following patterns are automatically detected:

| Pattern ID | What It Catches | Typical Waste |
|---|---|---|
| `bash_file_read` | cat/head/tail on non-system paths | 2-4 calls |
| `polling_loop` | 3+ curl/ss probes to same URL | 8-10 calls |
| `verify_read_after_edit` | Read immediately after Edit same file | 1-3 calls |
| `repeated_file_read` | Same file Read > 1 time | 1-5 calls |
| `intermediate_image_read` | PNG read mid-session | 1-2 calls |
| `temp_prompt_file` | echo to /tmp then gemini --prompt-file | 1 per call |
| `subagent_for_cached_data` | Agent spawned when /tmp data exists | 20-25 calls |

---

## What This Means for Subagents

When you are spawned as a subagent:
1. **Immediately check** what input data already exists in `/tmp/` before fetching anything
2. **Read your SKILL.md once** — not multiple times
3. **Keep a running mental budget** — if you're past 15 tool calls and not done, stop and reconsider your approach
4. **Batch your writes** — one Write or multiple Edits per file, never interleaved reads
