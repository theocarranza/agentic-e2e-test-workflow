> [!NOTE] Claude
> # Implementation Plan — Defect Cluster F1 · F10 · F11 · F2 (`maestro-e2e-workflow` v0.1.0 → v0.1.1)
> 
> > **Status:** EXECUTED — 2026-07-11 on branch `fix/v011-f1-f10-f11-f2` (token `IMPLEMENTATION APPROVED` received). **Scope source:** Spec v3.0 §10 Findings. F11 added in-plan (discovered during plan research; justification in §Scope). **Out of scope (explicit, anti-scope-creep):** F3 (duplicated bash libs), F4 (.pyc hygiene), F5 (QC prompt fate — blocked on your design decision), F6–F9. Each remains catalogued in spec v3 §10.
> 
> * * *
> 
> ### Codex Context
> 
> Per the Research Mandate, sources consulted before drafting:
> 
> | Anchor | Finding used |
> | --- | --- |
> | Spec v3.0 §5.2/§5.3 (mtime cascade, mailbox contract) | Router prioritizes error.log over freshness ⇒ F10 severity: permanent correcao loop |
> | Spec v3.0 §10 F1/F2/F10 | Defect definitions and AC-7/AC-8 mappings |
> | maestro-e2e-plugin/orchestrator_core/adapters.py (cloned @ master) | get_stage_prompt_file mapping ends at stage_3; build_stage_context has no stage_4 input branch |
> | router.py, executor.py, main.py, mcp_server.py | stage_4 is dispatched; executor compiles context for any dispatched stage; no evaluate subcommand exists anywhere (⇒ F11); nothing deletes error.log (⇒ F10 confirmed) |
> | diff orchestrator_core/ maestro-e2e-plugin/orchestrator_core/ | Root copy is a strict stale ancestor (pre-stage_4, pre-correcao, pre-ejection-override, old evaluator signature). No unique improvements detected to port. |
> | skills/e2e/SKILL.md Step 3 | Prescribes maestro-e2e evaluate --stage \<s\> --file \<f\> — the contract F11 must satisfy |
> | 4-execution-and-healing.prompt.md insumos | Stage-4 context inputs: target flow.yaml path, blueprint.md, test-plan.md (consultable on selector failure) |
> | Data Retention policy | Root-copy removal handled via git (history preserves it); this is repo code, not Codex vault content — CODEX DELETION AUTHORIZED not applicable, but flagged for your awareness |
> 
> ### Scope
> 
> Four changes, one theme: **make the routed pipeline actually completable.** F1 blocks stage-4 dispatch; F11 blocks the quality-gate step the SKILL prescribes; F10 makes any recovered failure loop forever; F2 removes the ambiguity about which engine is real. F11 is included (beyond the approved F1+F10+F2) because F10's only correct fix location is the `evaluate` command that F11 creates — implementing F10 without F11 would require inventing a second, redundant gate entry point.
> 
> * * *
> 
> ## Change 1 — F1: Stage-4 prompt mapping + context inputs (`adapters.py`)
> 
> **1a.** Extend the mapping in `get_stage_prompt_file`:
> 
> python
> 
> ```python
> mapping = {
>     "stage_0": "0-domain-discovery.prompt.md",
>     "stage_1": "1-test-plan-author.prompt.md",
>     "stage_2": "2-widget-blueprint.prompt.md",
>     "stage_3": "3-maestro-implementer.prompt.md",
>     "stage_4": "4-execution-and-healing.prompt.md",   # F1
> }
> ```
> 
> (`4-e2e-quality-control.prompt.md` stays unrouted — that's F5, explicitly deferred.)
> 
> **1b.** Add the stage-4 input branch in `build_stage_context`, mirroring the prompt's declared insumos (target flow path + consultable upstream artifacts):
> 
> python
> 
> ```python
> elif stage_id == "stage_4":
>     flow_path = get_artifact_path(target, "stage_3", workspace_dir)
>     context_blocks.append("--- INPUT: TARGET FLOW (path) ---")
>     context_blocks.append(str(flow_path))
>     context_blocks.append("--- INPUT: WIDGET BLUEPRINT (blueprint.md) ---")
>     context_blocks.append(load_file_content(get_artifact_path(target, "stage_2", workspace_dir)))
>     context_blocks.append("--- INPUT: TEST PLAN (test-plan.md) ---")
>     context_blocks.append(load_file_content(get_artifact_path(target, "stage_1", workspace_dir)))
> ```
> 
> Note: flow content is passed **by path**, not embedded — Stage 4 edits the file on disk during healing; embedding a snapshot would invite stale-content patches.
> 
> ## Change 2 — F11: `evaluate` subcommand (`main.py`)
> 
> Restructure argparse into subcommands while preserving the existing invocation surface (`--init`, `--module/--flow` remain valid on the default path). New command per SKILL.md's contract:
> 
> ```
> maestro-e2e evaluate --stage <stage_0..stage_4> --file <path/to/artifact>
> ```
> 
> Behavior (thin imperative shell around the pure evaluator, FP-conformant):
> 
> 1.  `critiques = evaluate_artifact(stage, read(file))`
> 2.  `critiques == []` ⇒ print PASS, **Change 3 hook runs (clear error log)**, exit 0.
> 3.  otherwise ⇒ print critiques, write them to `.agentic/e2e_prompts/{stage}.error.log` (creating the F10-consumable feedback the adapters already know how to embed), exit 1.
> 
> Exit codes make the gate scriptable from any harness — consistent with the mailbox philosophy.
> 
> ## Change 3 — F10: `error.log` lifecycle (`main.py` evaluate path)
> 
> On evaluator PASS: `Path(".agentic/e2e_prompts")/f"{stage}.error.log"` → `unlink(missing_ok=True)`. Engine-side by design: agent-side cleanup (SKILL instruction) would be unreliable across harnesses, and the router trusts the file's mere presence. Resulting invariant, appended to spec §5.3 after execution: *an `error.log` exists iff the most recent evaluation of that stage FAILED.*
> 
> ## Change 4 — F2: Canonicalize the engine (remove stale root copy)
> 
> 1.  **Verification gate first:** full `diff -r` (already sampled; plan requires the complete pass) confirming the root copy contains zero unique changes. Any unique hunk found ⇒ STOP, report, await instruction (per the uncertainty directive).
> 2.  `git rm -r orchestrator_core/` at repo root (+ `__pycache__` within). Git history preserves the copy — nothing is destroyed.
> 3.  Add repo-root `README.md` note: engine lives at `maestro-e2e-plugin/orchestrator_core/` (single canonical copy).
> 4.  Add `.gitignore` entry for `__pycache__/` *only as required to keep this change clean* — full F4 sweep stays out of scope.
> 
> ## Tests (TDD — authored before the fixes)
> 
> `maestro-e2e-plugin/tests/` (pytest):
> 
> -   `test_adapters_stage4.py` — `get_stage_prompt_file("stage_4")` resolves to the healing prompt; `build_stage_context(..., "stage_4", ...)` contains flow path + blueprint + test-plan blocks; ejection override honored for stage\_4. **(AC-7)**
> -   `test_router_error_priority.py` — regression: `error.log` + stale artifact ⇒ `correcao` wins. **(AC-3)**
> -   `test_evaluate_command.py` — PASS ⇒ exit 0 and `error.log` absent; FAIL ⇒ exit 1 and `error.log` contains critiques; PASS-after-FAIL ⇒ log removed (loop broken). **(F10/F11)**
> -   `test_single_engine_copy.py` — asserts `repo_root/orchestrator_core` does not exist. **(AC-8)**
> 
> ## Rollout & Versioning
> 
> -   One feature branch off `master`; commits ordered: tests → F1 → F11+F10 → F2 (each independently green).
> -   `CHANGELOG.md` `[0.1.1]` — Fixed: stage-4 dispatch (F1), evaluate command (F11), error-log lifecycle (F10); Removed: stale root engine copy (F2, history-preserved).
> -   Bump all three plugin manifests to 0.1.1 in the same commit (F9's generator is out of scope; manual sync this once).
> -   Re-run `bootstrap.py --target all-agents` post-merge so installed copies pick up the fix.
> 
> ## Risks
> 
> -   **F2 removal** is the only destructive-looking step; mitigated by the verification gate + git history. If you prefer maximal caution, alternative: replace root copy with a single `DEPRECATED.md` pointer instead of deletion — say the word and I'll amend the plan.
> -   **argparse restructure (F11)** touches the CLI entry; mitigated by keeping legacy flags on the default subcommand and covering both invocation forms in tests.
> 
> * * *
> 
> ✅ **Executed** on `fix/v011-f1-f10-f11-f2`. Validation: `pytest maestro-e2e-plugin/tests/` — 8 passed.

> [!NOTE] Claude
> E2E AGENTIC WORKFLOW - MAESTRO TESTING