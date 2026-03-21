#  Agentic Dev Flow

> **Better way to view this:** GitHub renders Mermaid diagrams natively.
> Open this file on GitHub or in VS Code (with the Markdown Preview Mermaid Support extension) to see it rendered.
> For a static image, see [`agentic-flow.svg`](./agentic-flow.svg).

---

## Flow Diagram

```mermaid
flowchart TD
    Dev(["👨‍💻 Developer\ntriggers slash commands"])

    Dev --> PM_CMD["/pm CU-{id}"]

    subgraph PM_PHASE["📋  PM Phase"]
        PM_CMD --> PM_AGENT["PM Agent  #0\nGrooms task · fills ClickUp fields\nSelf-reflection loop"]
        PM_AGENT --> CP0{{"✅ Checkpoint 0\nagent_task_approved"}}
    end

    CP0 -->|"approved by human"| BUILD_CMD["/build CU-{id}"]

    subgraph BUILD_PHASE["⚙️  Build Phase"]
        BUILD_CMD --> ORCH["🎯 Orchestrator  #1\nCoordinates all sub-agents"]

        ORCH --> DA["🎨 Design Agent  #2\nFigma → UISpec JSON"]
        ORCH --> BA["🔧 Backend Agent  #3\nFastAPI + SQL"]
        ORCH --> FA["⚛️ Frontend Agent  #4\nReact + shadcn/ui"]

        DA & BA & FA --> REF["🔗 Reflector Agent  #5\nBackend ↔ Frontend Contract Check"]
        REF --> TEST["🧪 Testing Agent  #6\npytest + vitest + Playwright"]
        TEST --> REV["📊 Review Agent  #7\nScore 0–100  ·  ≥ 80 = pass"]

        REV -->|"Score < 80  —  retry loop"| ORCH
        REV -->|"Score ≥ 80"| CP1

        CP1{{"✅ Checkpoint 1\nagent_code_approved"}}
        CP1 -->|"approved by human"| CP2
        CP2{{"✅ Checkpoint 2\nagent_pr_approved"}}
        CP2 -->|"approved by human"| GHA
        GHA["🐙 GitHub Agent  #8\nBranch + Commit + PR"]
    end

    GHA --> PR[["🚀 GitHub PR\nfeature/CU-{id}-{slug}"]]
    PR -->|"merged"| DONE(["✅ Status: complete"])

    subgraph MCP["🔌  MCP Integrations"]
        CU["🔵 ClickUp MCP\nTasks · Fields · Status"]
        GH["🟢 GitHub MCP\nBranches · PRs · Labels"]
        FIG["🟣 Figma MCP\nDesign Files · Frames"]
        PG["🟡 PostgreSQL MCP\nRead-only Schema"]
    end

    PM_AGENT -. "read/write" .-> CU
    ORCH     -. "status updates" .-> CU
    DA       -. "fetch designs" .-> FIG
    BA       -. "inspect schema" .-> PG
    GHA      -. "branch + PR" .-> GH

    style Dev        fill:#6366f1,color:white,stroke:#4338ca
    style PM_PHASE   fill:#faf5ff,stroke:#7c3aed,color:#1e1b4b
    style BUILD_PHASE fill:#eff6ff,stroke:#2563eb,color:#1e3a5f
    style MCP        fill:#f0fdf4,stroke:#16a34a,color:#14532d
    style ORCH       fill:#1d4ed8,color:white,stroke:#1e40af
    style CP0        fill:#16a34a,color:white,stroke:#15803d
    style CP1        fill:#16a34a,color:white,stroke:#15803d
    style CP2        fill:#16a34a,color:white,stroke:#15803d
    style PR         fill:#1f2937,color:white,stroke:#111827
    style DONE       fill:#16a34a,color:white,stroke:#15803d
```

---

## Mind Map

```mermaid
mindmap
  root((Vanta LMS\nAgentic Dev Flow))
    Developer Workflow
      /pm CU-{id}
      /build CU-{id}
      /status CU-{id}
      /retry CU-{id}
      /cancel CU-{id}
    Agents
      PM Agent #0
        Grooms ClickUp task
        Self-reflection loop
      Orchestrator #1
        Coordinates sub-agents
        Manages checkpoints
      Design Agent #2
        Reads Figma designs
        Outputs UISpec JSON
      Backend Agent #3
        FastAPI endpoints
        SQL migrations
      Frontend Agent #4
        React components
        shadcn/ui
      Reflector Agent #5
        Contract validation
        Backend ↔ Frontend
      Testing Agent #6
        pytest
        vitest
        Playwright
      Review Agent #7
        Score 0–100
        Pass threshold ≥ 80
      GitHub Agent #8
        Creates branch
        Commits code
        Opens PR
    Human Checkpoints
      CP0 agent_task_approved
      CP0.5 agent_requirements_approved
      CP1 agent_code_approved
      CP2 agent_pr_approved
    MCP Integrations
      ClickUp MCP
      GitHub MCP
      Figma MCP
      PostgreSQL MCP read-only
    Safety Guardrails
      bash_guard
      postgres_guard
      github_guard
      audit_logger
    Stack
      Backend FastAPI + PostgreSQL
      Frontend React + Tailwind + shadcn
      Monorepo Nx
      DB Neon PostgreSQL
```

---

## ClickUp Status Flow

```mermaid
stateDiagram-v2
    [*] --> to_do
    to_do --> ready : PM Agent grooms task
    ready --> in_progress : /build triggered
    in_progress --> blocked : ambiguity / needs PM review
    blocked --> in_progress : human resolves
    in_progress --> in_review : GitHub Agent opens PR
    in_review --> complete : PR merged
    in_progress --> cancelled : /cancel command
    blocked --> cancelled : /cancel command
```
