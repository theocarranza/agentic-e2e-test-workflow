---
type: ticket
ticket: multi-model-adapters-plugin-port
status: resolved
opened: 2026-07-11T15:22:48Z
resolved: 2026-07-12
source_branch: feature/multi-model-adapters-plugin-port
---

# Ticket: Multi-model adapters plugin port

## Problem Recap

The branch carries the current plugin-port work for multi-model adapter support and the follow-on F5 stage decision. The work needed to port the earlier root-engine adapter design into `maestro-e2e-plugin/`, keep the root engine out of scope, and resolve the QC prompt ambiguity by making QC an explicit stage before execution and healing.

## Acceptance Criteria

- Multi-model adapter Tasks 1-10 are represented in the plugin package, excluding the already plugin-only Task 8.
- The plugin exposes reusable skill package loading, dialect transformation, tool binding, protocol normalization, persistence, events, and meta-agent support.
- Stage 4 is E2E Quality Control as an LLM worker that produces `qc-report.md`.
- Stage 5 is Execution & Self-Healing and remains backed by `4-execution-and-healing.prompt.md`.
- A rejected QC report routes correction back to stage 3 with violations context and uses a 3-strike `BLOCKED_REQUIRES_REVIEW` breaker.
- Verification evidence names the concrete tests and branch artifacts used to accept the work.

## Specs

- [[../../Specs/multi-model-adapters-plugin-port/tech-spec]]
- [[../../Specs/multi-model-adapters-plugin-port/implementation-plan]]

## Implementation Summary

- Added plugin modules for adapter and orchestration support: `maestro-e2e-plugin/orchestrator_core/skill_package.py`, `dialects.py`, `tool_binding.py`, `protocol.py`, `persistence.py`, `events.py`, and `meta_agent.py`.
- Updated orchestration behavior in `maestro-e2e-plugin/orchestrator_core/reducers.py`, `router.py`, `adapters.py`, `main.py`, `mcp_server.py`, and `evaluator.py`.
- Reworked prompt contracts in `maestro-e2e-plugin/orchestrator_core/prompts/4-e2e-quality-control.prompt.md` and `4-execution-and-healing.prompt.md`.
- Added the example skill package under `maestro-e2e-plugin/skills/example_echo/`.
- Added or updated tests for adapter packaging, dialects, tool binding, protocol normalization, persistence, events, MCP skill discovery, QC routing, and stage 4/stage 5 evaluation.
- Documented the F5 decision in `AI_Codex_AgenticE2eTestWorkflow/Architecture/ADR/2026-07-11-f5-qc-stage4-execution-stage5.md`.

## Verification

- Session checkpoint recorded `python3.12 -m pytest maestro-e2e-plugin/tests/` with 57 passed after the multi-model adapter port.
- Session checkpoint recorded `python3.12 -m pytest maestro-e2e-plugin/tests/` with 67 passed after the F5 stage 4/stage 5 work.
- Session checkpoint recorded `py_compile` clean, MCP tools/list returning `example_echo`, and initialize OK after the adapter port.

## Resolution

Accepted resolution report: [[../../Specs/multi-model-adapters-plugin-port/resolution-report]]

The resolve-ticket critic checks passed on the first round:

- Required headings are present.
- `tech-spec.md` and `implementation-plan.md` are both referenced in Spec Coverage.
- Implementation evidence names concrete plugin modules, prompts, tests, ADR, branch, and source context.
- Verification records the 57-pass adapter checkpoint, the 67-pass F5 checkpoint, `py_compile` clean, tools/list `example_echo`, and initialize OK.
- Current closure verification on 2026-07-12 ran `python3.12 -m pytest maestro-e2e-plugin/tests/` and passed all 67 collected tests.
- Placeholder scan found no unresolved template markers in the ticket specs or resolution report.
