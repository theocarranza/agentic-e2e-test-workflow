# MAestro E2E Agentic Workflow

## Project structure diagram

```text
agentic-orchestrator-pkg/
├── orchestrator/
│   ├── stream.py        (Reactive state machine)
│   └── reducers.py      (Pure functional transitions)
└── default_skills/
    ├── test_plan_author/
    │   ├── manifest.json
    │   └── instructions.md
    └── blueprint_architect/