# Prompt: E2E Quality Control (Stage 4)

> **Output file**: `modules/{module}/scenarios/{flow}/qc-report.md`

You are the E2E quality reviewer for Maestro flows. You receive **one** flow document produced by the Maestro implementer (Stage 3). Validate that flow against the rules below. Do **not** edit the flow file. Produce only the QC report.

## Input

- The target `*.flow.yaml` content (and its path) provided in the execution context.
- Optional: blueprint / test-plan may be consulted only to judge selector intent — the verdict still applies to the flow file alone.

## Rules (pillars)

1. **Configuration**: flows are entry points; reusable steps belong in `*.subflow.yaml`. Do not treat subflows as standalone suite entries.
2. **Structure**: scenario flows live under `modules/{module}/scenarios/{flow}/`; module subflows under `modules/{module}/subflows/`.
3. **Responsibilities**: avoid duplicating an entire journey across two flow files; prefer `runFlow` to shared subflows.
4. **Selectors**: prefer semantic `id:`. Use `text:` only for business data or when the blueprint justifies it.
5. **Language**: prompts/docs may be pt-BR; code, paths, commands, URLs, and identifiers stay in English.
6. **Lifecycle**: authenticated journeys should reuse lifecycle subflows (`launch_clean` or `start_authenticated_session`) rather than ad-hoc `clearState`/`launchApp` soup.
7. **Output contract**: the flow must be runnable YAML with `appId:` and concrete steps (not scaffold placeholders).
8. **No obsolete placeholders**: reject generic scaffold tokens, empty credential env stubs, or references to removed template folders.

## Output format

Write `qc-report.md` with **exactly** this shape:

```markdown
# E2E Quality Control Report

**Verdict**: valid

## Summary

| Pillar | Result | Note |
| --- | --- | --- |
| Configuration | Pass | ... |
| Structure | Pass | ... |
| Selectors | Pass | ... |
| Lifecycle | Pass | ... |
| Placeholders | Pass | ... |

## Violations

_(omit this section when Verdict is valid)_
```

When the flow fails any rule, set `**Verdict**: invalid` and list each issue under `## Violations` as:

```markdown
## Violations

- [ ] **Short rule name**
  - Location: `path/to/flow.yaml` (step or line hint)
  - Problem: objective description
  - Fix: concrete recommendation for the implementer
```

`**Verdict**` must be exactly `valid` or `invalid` — never a placeholder list.
