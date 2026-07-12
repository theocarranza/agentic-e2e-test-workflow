---
type: spec
kind: implementation-plan
ticket: multi-model-adapters-plugin-port
status: accepted
---

# Implementation Plan: Multi-model Adapters Plugin Port

## Scope

In scope:

- Port multi-model adapter support into `maestro-e2e-plugin/`.
- Keep the plugin package as the canonical runtime.
- Add tests and example package coverage for the new adapter modules.
- Resolve F5 by assigning QC to stage 4 and execution/healing to stage 5.
- Document the F5 decision in the vault.

Out of scope:

- Reviving the root `orchestrator_core/` as a second runtime.
- Building a full static AST quality-control engine.
- Committing, pushing, or releasing the branch as part of ticket resolution.
- Running live device, Firebase, or Maestro E2E flows for this ticket closure.

## Milestones

1. Port the adapter foundation into the plugin runtime.
2. Add test coverage for adapter foundation modules.
3. Wire MCP skill discovery and invalid input behavior.
4. Implement F5 stage split in routing, adapter prompt mapping, evaluator behavior, and command handling.
5. Add QC and stage 5 tests.
6. Record the F5 decision and branch verification evidence in the vault.
7. Close the ticket with a resolution report after critic acceptance.

## Tasks

- [x] Add `skill_package.py`, `dialects.py`, `tool_binding.py`, `protocol.py`, `persistence.py`, `events.py`, and `meta_agent.py` under `maestro-e2e-plugin/orchestrator_core/`.
- [x] Add `maestro-e2e-plugin/skills/example_echo/` as a concrete skill package fixture.
- [x] Update reducers for per-task retry behavior.
- [x] Update MCP server behavior for skill package discovery and invalid input reporting.
- [x] Rewrite `4-e2e-quality-control.prompt.md` for single-flow QC.
- [x] Relabel execution and healing prompt expectations to stage 5.
- [x] Update router behavior so stage 4 QC gates stage 5 execution.
- [x] Update adapters and main command handling for `stage_4` and `stage_5`.
- [x] Update evaluator behavior for QC reports and execution reports.
- [x] Add tests for adapter modules, skill discovery, persistence, events, protocol normalization, tool binding, QC routing, and stage 4/stage 5 evaluation.
- [x] Record the accepted F5 decision in `Architecture/ADR/2026-07-11-f5-qc-stage4-execution-stage5.md`.
- [x] Produce the ticket resolution report and archive the ledger after critic acceptance.

## Dependencies

- Existing branch `feature/multi-model-adapters-plugin-port`.
- Existing source branch context from `feature/multi-model-agentic-adapters`.
- Plugin package directory `maestro-e2e-plugin/`.
- Vault directory `AI_Codex_AgenticE2eTestWorkflow/`.
- Python test runner available as `python3.12`.

No database migration, remote service flag, or external deployment dependency is required for ticket closure.

## Validation

- The adapter port checkpoint is accepted by the recorded run `python3.12 -m pytest maestro-e2e-plugin/tests/`, with 57 passed.
- The F5 checkpoint is accepted by the recorded run `python3.12 -m pytest maestro-e2e-plugin/tests/`, with 67 passed.
- The adapter port checkpoint also records `py_compile` clean, MCP tools/list exposing `example_echo`, and initialize OK.
- Ticket closure validation MUST include checking the resolution report for required headings, spec coverage, implementation evidence, verification narrative, and absence of placeholder markers.

## Rollback

If this ticket must be reopened after resolution, move the ledger back from `Tickets/Resolved/` to `Tickets/Active/`, mark `status: active`, and add a new section describing the failed acceptance evidence. If implementation rollback is required, revert the branch changes in source control and leave the resolution report as historical evidence only when the rollback happens after acceptance.
