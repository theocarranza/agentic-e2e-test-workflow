---
type: design
status: executed
tags: [f5, qc, stage-4, stage-5]
created: 2026-07-11
---

# Design: F5 — QC stage 4, Execution stage 5

## Decision

- **Stage 4** = E2E Quality Control (**LLM worker**).
- **Stage 5** = Execution & Self-Healing (former stage 4).
- QC mode: **LLM** (confirmed 2026-07-11). Static `evaluate` only validates the QC artifact contract.

## Pipeline

| Stage | Skill | Input | Artifact |
| --- | --- | --- | --- |
| 0–2 | unchanged | … | … |
| 3 | Maestro implementer | blueprint + plan | `{flow}.flow.yaml` |
| 4 | E2E QC (LLM) | that one flow YAML | `qc-report.md` |
| 5 | Execution & healing | validated flow | `execution-report.md` |

## Stage 4 contract

- Prompt: `4-e2e-quality-control.prompt.md` rewritten for one flow (no Aplicatudo/PR-diff framing); pillars remain the declared rules.
- Artifact path: `e2e_test/modules/{m}/scenarios/{f}/qc-report.md`
- Required fields:
  - `**Verdict**: valid` or `**Verdict**: invalid`
  - If invalid: `## Violations` list (location, rule, fix hint)
- `maestro-e2e evaluate --stage stage_4`: PASS only when verdict is exactly `valid`.

## Implementer ↔ QC loop

1. Stage 3 writes/updates the flow.
2. Router spawns stage 4 when QC missing/stale vs flow.
3. LLM QC writes `qc-report.md`.
4. Evaluate PASS → unlock stage 5.
5. Evaluate FAIL / invalid → `stage_4.error.log`; router re-spawns **stage 3** in `correcao` with violations context (not QC alone).
6. Same flow rejected **3 times in a row** → `BLOCKED_REQUIRES_REVIEW` + user interrupt; counter clears on `valid`.

## Stage 5

- Prompt map: `stage_5` → `4-execution-and-healing.prompt.md` (filename may stay; stage id is 5).
- Artifact: `execution-report.md` (moved from former stage_4 path).
- Evaluator: former `evaluate_stage_4` → `evaluate_stage_5`.
- Depends on validated stage 4, not raw stage 3.

## Scope

- One `WorkflowTarget` (module+flow) per engine run; multi-flow = sequential outer runs.
- Out of scope: committing multi-model port; full static AST QC.

## Approval gate

Implementation starts only after user token: `IMPLEMENTATION APPROVED`.


## Implementation

Token received 2026-07-11T20:40:56Z. Executing on branch feature/multi-model-adapters-plugin-port.


## Checkpoint - 2026-07-11T20:42:40Z

Runtime wired; 67 plugin tests passed.
