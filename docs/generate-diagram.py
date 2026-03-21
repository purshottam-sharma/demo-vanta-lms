#!/usr/bin/env python3
"""Generate Vanta LMS Agentic Flow Diagram as SVG."""

W, H = 900, 1090

def r(x, y, w, h, fill, stroke='#cbd5e1', rx=8, sw=1.5, dash=None):
    da = f' stroke-dasharray="{dash}"' if dash else ''
    return f'  <rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"{da}/>\n'

def t(x, y, s, anchor='middle', size=12, weight='normal', fill='#1e293b', italic=False):
    sty = ' font-style="italic"' if italic else ''
    return f'  <text x="{x}" y="{y}" text-anchor="{anchor}" font-size="{size}" font-weight="{weight}" fill="{fill}"{sty}>{s}</text>\n'

def ln(x1, y1, x2, y2, stroke='#94a3b8', sw=2, dash=None, marker=None):
    d = f' stroke-dasharray="{dash}"' if dash else ''
    m = f' marker-end="url(#{marker})"' if marker else ''
    return f'  <line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{stroke}" stroke-width="{sw}"{d}{m}/>\n'

out = []

# ── Header ──────────────────────────────────────────────────────────────────
out.append(f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}"
     viewBox="0 0 {W} {H}" font-family="ui-sans-serif, system-ui, sans-serif">
  <defs>
    <marker id="a"  markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto"><polygon points="0 0,8 3,0 6" fill="#64748b"/></marker>
    <marker id="ag" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto"><polygon points="0 0,8 3,0 6" fill="#16a34a"/></marker>
    <marker id="ab" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto"><polygon points="0 0,8 3,0 6" fill="#2563eb"/></marker>
    <marker id="ac" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto"><polygon points="0 0,8 3,0 6" fill="#0891b2"/></marker>
    <marker id="ao" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto"><polygon points="0 0,8 3,0 6" fill="#d97706"/></marker>
  </defs>
''')

# Background
out.append(r(0, 0, W, H, '#f8fafc', '#e2e8f0', rx=0))

# Title
out.append(t(W//2, 30, 'Agentic Dev Flow', size=18, weight='700', fill='#0f172a'))
out.append(t(W//2, 47, 'Claude Code native &#183; no separate Anthropic API calls needed', size=10, fill='#64748b', italic=True))

# ── Coordinates ─────────────────────────────────────────────────────────────
CX   = 390   # main column center x
BW   = 200   # standard box width
BX   = CX - BW // 2  # = 290

DA_CX = 148  # Design agent center
BA_CX = 390  # Backend agent center (= CX)
FA_CX = 632  # Frontend agent center
SAW   = 165  # sub-agent box width

# ── Developer ───────────────────────────────────────────────────────────────
out.append(r(CX-110, 58, 220, 42, '#6366f1', '#4338ca', rx=21, sw=2))
out.append(t(CX, 74, '&#x1F9D1;&#x200D;&#x1F4BB;  Developer', size=13, weight='700', fill='white'))
out.append(t(CX, 90, 'triggers slash commands', size=10, fill='#c7d2fe'))
out.append(ln(CX, 100, CX, 116, '#64748b', 2, marker='a'))

# ── /pm command ─────────────────────────────────────────────────────────────
out.append(r(BX, 119, BW, 38, '#7c3aed', '#6d28d9', rx=8))
out.append(t(CX, 134, '/pm CU-{id}', size=12, weight='600', fill='white'))
out.append(t(CX, 149, 'PM slash command', size=10, fill='#e9d5ff'))
out.append(ln(CX, 157, CX, 172, '#7c3aed', 2, marker='a'))

# ── PM Agent #0 ─────────────────────────────────────────────────────────────
out.append(r(BX, 175, BW, 50, '#8b5cf6', '#7c3aed', rx=8))
out.append(t(CX, 195, 'PM Agent  #0', size=12, weight='600', fill='white'))
out.append(t(CX, 212, 'Grooms task &#183; fills ClickUp fields', size=10, fill='#ede9fe'))
out.append(ln(CX, 225, CX, 241, '#16a34a', 2, marker='ag'))

# ── Checkpoint 0 ────────────────────────────────────────────────────────────
out.append(r(BX, 244, BW, 46, '#16a34a', '#15803d', rx=23, sw=2))
out.append(t(CX, 262, '&#x2705;  Checkpoint 0', size=12, weight='700', fill='white'))
out.append(t(CX, 279, 'agent_task_approved', size=10, fill='#dcfce7'))
out.append(t(CX+115, 264, '&#8592; human', size=9, fill='#16a34a', anchor='start'))
out.append(ln(CX, 290, CX, 306, '#16a34a', 2, marker='ag'))
out.append(t(CX+5, 301, 'approved', size=9, fill='#16a34a', anchor='start'))

# ── /build command ──────────────────────────────────────────────────────────
out.append(r(BX, 309, BW, 38, '#2563eb', '#1d4ed8', rx=8))
out.append(t(CX, 324, '/build CU-{id}', size=12, weight='600', fill='white'))
out.append(t(CX, 339, 'Build slash command', size=10, fill='#bfdbfe'))
out.append(ln(CX, 347, CX, 362, '#2563eb', 2, marker='ab'))

# ── Orchestrator #1 ─────────────────────────────────────────────────────────
out.append(r(BX, 365, BW, 50, '#1d4ed8', '#1e40af', rx=10, sw=2))
out.append(t(CX, 384, 'Orchestrator  #1', size=13, weight='700', fill='white'))
out.append(t(CX, 401, 'Coordinates all sub-agents', size=10, fill='#bfdbfe'))

# Fork: Orchestrator → 3 sub-agents
ORCH_B = 415
SUB_Y  = 438
JOIN_Y = SUB_Y + 56  # = 494

out.append(ln(CX, ORCH_B, CX, ORCH_B+10, '#2563eb', 2))                                    # down
out.append(ln(DA_CX, ORCH_B+10, FA_CX, ORCH_B+10, '#2563eb', 2))                           # horizontal bar
out.append(ln(DA_CX, ORCH_B+10, DA_CX, SUB_Y-2, '#2563eb', 2, marker='ab'))                # to Design
out.append(ln(BA_CX, ORCH_B+10, BA_CX, SUB_Y-2, '#2563eb', 2, marker='ab'))                # to Backend
out.append(ln(FA_CX, ORCH_B+10, FA_CX, SUB_Y-2, '#2563eb', 2, marker='ab'))                # to Frontend

# ── Sub-agents row ──────────────────────────────────────────────────────────
# Design #2
out.append(r(DA_CX-SAW//2, SUB_Y, SAW, 56, '#0891b2', '#0e7490', rx=8))
out.append(t(DA_CX, SUB_Y+19, 'Design  #2', size=11, weight='600', fill='white'))
out.append(t(DA_CX, SUB_Y+34, 'Figma &#8594; UISpec JSON', size=9, fill='#cffafe'))

# Backend #3
out.append(r(BA_CX-SAW//2, SUB_Y, SAW, 56, '#0891b2', '#0e7490', rx=8))
out.append(t(BA_CX, SUB_Y+19, 'Backend  #3', size=11, weight='600', fill='white'))
out.append(t(BA_CX, SUB_Y+34, 'FastAPI + SQL', size=9, fill='#cffafe'))

# Frontend #4
out.append(r(FA_CX-SAW//2, SUB_Y, SAW, 56, '#0891b2', '#0e7490', rx=8))
out.append(t(FA_CX, SUB_Y+19, 'Frontend  #4', size=11, weight='600', fill='white'))
out.append(t(FA_CX, SUB_Y+34, 'React + shadcn/ui', size=9, fill='#cffafe'))

# Join sub-agents → Reflector
out.append(ln(DA_CX, JOIN_Y, DA_CX, JOIN_Y+10, '#0891b2', 2))
out.append(ln(BA_CX, JOIN_Y, BA_CX, JOIN_Y+10, '#0891b2', 2))
out.append(ln(FA_CX, JOIN_Y, FA_CX, JOIN_Y+10, '#0891b2', 2))
out.append(ln(DA_CX, JOIN_Y+10, FA_CX, JOIN_Y+10, '#0891b2', 2))
REF_Y = 516
out.append(ln(CX, JOIN_Y+10, CX, REF_Y-2, '#0891b2', 2, marker='a'))

# ── Reflector #5 ────────────────────────────────────────────────────────────
out.append(r(BX, REF_Y, BW, 44, '#0d9488', '#0f766e', rx=8))
out.append(t(CX, REF_Y+17, 'Reflector Agent  #5', size=11, weight='600', fill='white'))
out.append(t(CX, REF_Y+33, 'Backend &#8596; Frontend Contract', size=10, fill='#99f6e4'))
TEST_Y = REF_Y + 56
out.append(ln(CX, REF_Y+44, CX, TEST_Y-2, '#0d9488', 2, marker='a'))

# ── Testing #6 ──────────────────────────────────────────────────────────────
out.append(r(BX, TEST_Y, BW, 44, '#059669', '#047857', rx=8))
out.append(t(CX, TEST_Y+17, 'Testing Agent  #6', size=11, weight='600', fill='white'))
out.append(t(CX, TEST_Y+33, 'pytest + vitest + Playwright', size=10, fill='#a7f3d0'))
REV_Y = TEST_Y + 56
out.append(ln(CX, TEST_Y+44, CX, REV_Y-2, '#059669', 2, marker='a'))

# ── Review #7 ───────────────────────────────────────────────────────────────
out.append(r(BX, REV_Y, BW, 58, '#d97706', '#b45309', rx=8))
out.append(t(CX, REV_Y+19, 'Review Agent  #7', size=11, weight='600', fill='white'))
out.append(t(CX, REV_Y+35, 'Score 0&#8211;100', size=10, fill='#fef3c7'))
out.append(t(CX, REV_Y+50, '&#8805; 80 = pass  &#183;  &lt; 80 = retry', size=10, fill='#fef3c7'))

# Loop: < 80 back to Orchestrator (left side)
LX = BX - 42  # = 248
out.append(ln(BX, REV_Y+29, LX, REV_Y+29, '#d97706', 1.5))
out.append(ln(LX, REV_Y+29, LX, 390, '#d97706', 1.5))
out.append(ln(LX, 390, BX-2, 390, '#d97706', 1.5, marker='ao'))
mid_loop_y = (REV_Y+29 + 390) // 2
out.append(t(LX-5, mid_loop_y-6, '&lt; 80', size=9, fill='#d97706', anchor='end'))
out.append(t(LX-5, mid_loop_y+7, 'retry', size=9, fill='#d97706', anchor='end'))

# ≥80 arrow down
CP1_Y = REV_Y + 74
out.append(ln(CX, REV_Y+58, CX, CP1_Y-2, '#16a34a', 2, marker='ag'))
out.append(t(CX+5, REV_Y+70, '&#8805; 80', size=9, fill='#16a34a', anchor='start'))

# ── Checkpoint 1 ────────────────────────────────────────────────────────────
out.append(r(BX, CP1_Y, BW, 44, '#16a34a', '#15803d', rx=22, sw=2))
out.append(t(CX, CP1_Y+17, '&#x2705;  Checkpoint 1', size=12, weight='700', fill='white'))
out.append(t(CX, CP1_Y+33, 'agent_code_approved', size=10, fill='#dcfce7'))
out.append(t(CX+115, CP1_Y+24, '&#8592; human', size=9, fill='#16a34a', anchor='start'))
CP2_Y = CP1_Y + 60
out.append(ln(CX, CP1_Y+44, CX, CP2_Y-2, '#16a34a', 2, marker='ag'))
out.append(t(CX+5, CP1_Y+55, 'approved', size=9, fill='#16a34a', anchor='start'))

# ── Checkpoint 2 ────────────────────────────────────────────────────────────
out.append(r(BX, CP2_Y, BW, 44, '#16a34a', '#15803d', rx=22, sw=2))
out.append(t(CX, CP2_Y+17, '&#x2705;  Checkpoint 2', size=12, weight='700', fill='white'))
out.append(t(CX, CP2_Y+33, 'agent_pr_approved', size=10, fill='#dcfce7'))
out.append(t(CX+115, CP2_Y+24, '&#8592; human', size=9, fill='#16a34a', anchor='start'))
GHA_Y = CP2_Y + 60
out.append(ln(CX, CP2_Y+44, CX, GHA_Y-2, '#16a34a', 2, marker='ag'))
out.append(t(CX+5, CP2_Y+55, 'approved', size=9, fill='#16a34a', anchor='start'))

# ── GitHub Agent #8 ─────────────────────────────────────────────────────────
out.append(r(BX, GHA_Y, BW, 44, '#1f2937', '#111827', rx=8, sw=2))
out.append(t(CX, GHA_Y+17, 'GitHub Agent  #8', size=12, weight='600', fill='white'))
out.append(t(CX, GHA_Y+33, 'Branch + Commit + Pull Request', size=10, fill='#9ca3af'))
PR_Y = GHA_Y + 58
out.append(ln(CX, GHA_Y+44, CX, PR_Y-2, '#64748b', 2, marker='a'))

# ── GitHub PR ───────────────────────────────────────────────────────────────
out.append(r(BX-20, PR_Y, BW+40, 44, '#111827', '#000', rx=8, sw=2))
out.append(t(CX, PR_Y+18, 'GitHub PR Created', size=13, weight='700', fill='white'))
out.append(t(CX, PR_Y+35, 'feature/CU-{id}-{slug}  &#8594;  review  &#8594;  merge', size=9, fill='#9ca3af'))

# ── MCP Integrations strip ──────────────────────────────────────────────────
MCP_Y = PR_Y + 58
out.append(r(18, MCP_Y, W-36, 76, '#f0fdf4', '#16a34a', rx=8, sw=1.5))
out.append(t(30, MCP_Y+14, 'MCP Integrations', size=10, weight='600', fill='#15803d', anchor='start'))

MCP_ITEMS = [
    ('#dbeafe', '#3b82f6', '#1e40af', 'ClickUp MCP',    'Tasks &#183; Fields &#183; Status'),
    ('#dcfce7', '#16a34a', '#14532d', 'GitHub MCP',     'Branches &#183; PRs &#183; Labels'),
    ('#f3e8ff', '#8b5cf6', '#4c1d95', 'Figma MCP',      'Designs &#183; Frames'),
    ('#fef3c7', '#f59e0b', '#78350f', 'PostgreSQL MCP',  'Read-only Schema'),
]
MBW = 190  # MCP box width
MGX = 28
for fill, stroke, tc, title, sub in MCP_ITEMS:
    out.append(r(MGX, MCP_Y+20, MBW, 48, fill, stroke, rx=6))
    out.append(t(MGX+MBW//2, MCP_Y+39, title, size=10, weight='600', fill=tc))
    out.append(t(MGX+MBW//2, MCP_Y+55, sub, size=9, fill='#475569'))
    MGX += MBW + 8

# ── Safety guardrails footer ────────────────────────────────────────────────
GUARD_Y = MCP_Y + 104
out.append(r(18, GUARD_Y, W-36, 34, '#fefce8', '#fbbf24', rx=6))
out.append(t(28, GUARD_Y+13, 'Safety:', size=9, weight='600', fill='#78350f', anchor='start'))
guards = ['bash_guard', 'postgres_guard', 'github_guard', 'audit_logger']
gx = 80
for g in guards:
    out.append(r(gx, GUARD_Y+5, 108, 22, '#fef3c7', '#f59e0b', rx=11))
    out.append(t(gx+54, GUARD_Y+20, g, size=9, fill='#78350f'))
    gx += 118
out.append(t(W//2, H-5, 'ClickUp Status: to do &#8594; ready &#8594; in progress &#8594; in review &#8594; complete', size=8, fill='#94a3b8', italic=True))

out.append('</svg>')

import os
os.makedirs('docs', exist_ok=True)
with open('docs/agentic-flow.svg', 'w', encoding='utf-8') as f:
    f.write(''.join(out))
print('Generated: docs/agentic-flow.svg')
