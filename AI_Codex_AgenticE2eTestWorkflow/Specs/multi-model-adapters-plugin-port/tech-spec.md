---
type: spec
kind: tech-spec
ticket: multi-model-adapters-plugin-port
status: accepted
---

# Tech Spec: Multi-model Adapters Plugin Port

## Overview

This ticket ports the multi-model adapter design into the canonical `maestro-e2e-plugin/` package and resolves the F5 quality-control stage decision. The plugin MUST keep the root engine revival out of scope, MUST expose adapter behavior from the plugin runtime, and MUST make QC an explicit stage before live execution and self-healing.

The accepted implementation has two connected outcomes:

- Multi-model adapter support lives inside `maestro-e2e-plugin/orchestrator_core/` through skill package loading, dialect transformation, tool binding, protocol normalization, persistence, events, and meta-agent summary support.
- The E2E pipeline treats stage 4 as LLM quality control and stage 5 as execution and healing.

## Data Model

- `SkillPackage` MUST load a skill directory containing a manifest, instructions, and optional portable tools.
- Dialect transformations MUST be pure functions from model-neutral instruction text to target-specific prompt text.
- Tool bindings MUST map manifest tool schemas into target harness tool-call schemas without mutating the manifest source.
- Protocol normalization MUST convert target model tool-call outputs into the universal command representation consumed by the plugin.
- Event records and queue state MUST remain immutable at the runtime boundary; reducer behavior SHOULD continue to return copied state instead of mutating existing state.
- Project persistence MUST store plugin-local project state under `maestro-e2e-plugin/projects/`, which is ignored by git.
- Stage 4 QC artifacts MUST be stored as `e2e_test/modules/{module}/scenarios/{flow}/qc-report.md`.
- Stage 5 execution artifacts MUST remain `e2e_test/modules/{module}/scenarios/{flow}/execution-report.md`.

## API

- The MCP server MUST discover plugin skill packages and expose valid skills through its tool listing path.
- Invalid MCP inputs MUST return `-32602` style invalid-params behavior instead of accepting malformed requests.
- Stage prompt mapping MUST route `stage_4` to `4-e2e-quality-control.prompt.md`.
- Stage prompt mapping MUST route `stage_5` to `4-execution-and-healing.prompt.md`, even though the prompt filename retains the historical stage 4 prefix.
- `maestro-e2e evaluate --stage stage_4` MUST pass only when the QC artifact contains the exact valid verdict required by the F5 contract.
- `maestro-e2e evaluate --stage stage_5` MUST validate the execution report contract formerly associated with stage 4.

## Implementation Plan

1. Port adapter support into `maestro-e2e-plugin/orchestrator_core/` rather than reviving the root engine.
2. Add tests that exercise skill package discovery, dialect transforms, tool bindings, protocol normalization, persistence, events, and meta-agent behavior.
3. Update MCP behavior so skill discovery and invalid input handling are covered by tests.
4. Rewrite the QC prompt for a single-flow quality-control worker.
5. Update router, adapters, main command handling, evaluator behavior, and reducers so QC is stage 4 and execution/healing is stage 5.
6. Add tests for stage 4 evaluation, stage 5 evaluation, adapter prompt mapping, and router QC correction behavior.
7. Document the F5 decision in the vault ADR and reconcile the root workflow spec note from unresolved to resolved.

## Testing Strategy

- Unit tests MUST cover each new adapter module and each modified runtime contract.
- Router tests MUST prove QC becomes stale when the flow changes and that invalid QC routes correction back to stage 3.
- Evaluator tests MUST prove stage 4 accepts only the QC valid verdict and stage 5 accepts execution report statuses.
- MCP tests MUST prove skill package discovery exposes `example_echo` and invalid input returns the expected invalid-params behavior.
- The full plugin test suite SHOULD be run with `python3.12 -m pytest maestro-e2e-plugin/tests/` before accepting the ticket.

## Rollback

Rollback SHOULD restore the branch to the last accepted master commit before this feature branch and remove only the plugin-port changes. The vault resolution artifacts can remain as historical evidence if the branch is reverted after acceptance; if rollback happens before acceptance, the active ledger SHOULD be reopened and marked blocked rather than left in `Tickets/Resolved/`.

## Requirements (RFC 2119)

- The implementation MUST keep new adapter runtime files under `maestro-e2e-plugin/orchestrator_core/`.
- The implementation MUST NOT reintroduce root-engine execution as the canonical runtime path.
- The implementation MUST make stage 4 the LLM QC stage.
- The implementation MUST make stage 5 the execution and healing stage.
- The implementation MUST preserve the implementer-to-QC correction loop with a 3-strike breaker.
- The implementation MUST include tests for every new public behavior added by the adapter port and F5 stage split.
- The implementation SHOULD leave unrelated branch changes untouched during ticket resolution.
