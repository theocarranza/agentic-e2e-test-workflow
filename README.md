# Maestro E2E Orchestrator Plugin

An autonomous, multi-agent orchestrator for generating, validating, and executing End-to-End UI tests using Maestro and Flutter. This tool bridges the gap between LLM agents (Antigravity, Claude Code, AI Codex) and the physical Android/iOS test harness.

## Canonical engine location

The orchestration runtime lives only at `maestro-e2e-plugin/orchestrator_core/`. There is no separate root-level `orchestrator_core/` copy.

## Features

- **Harness-Agnostic**: Can be run by any major local AI agent through a simple mailbox (`.agentic/e2e_prompts/`) filesystem interface.
- **5-Stage Pipeline**:
  1. **Domain Discovery**: Analyzes Dart source code to document business logic (with Adversarial focus).
  2. **Test Plan Author**: Writes BDD/Gherkin scenarios.
  3. **Widget Blueprint**: Extracts rigorous UI selectors and semantics from the codebase.
  4. **Maestro Implementer**: Writes the final `.flow.yaml` and `.subflow.yaml` files.
  5. **Execution & Self-Healing**: Runs the flows on a real device, uses `maestro hierarchy` to debug failures, auto-corrects the code, and catalogs learnings into `common-pitfalls.md`.
- **Self-Healing Resume Loop**: If Maestro physical execution or static linting fails, the orchestrator catches the stack trace and dispatches the task back to the agent in `correcao` mode for automatic remediation.
- **Hermetic Scaffolding**: Provides an `/e2e init` command to eject portable bash scripts, emulators, and prompt templates directly into your project's repository for CI/CD compatibility.

## Installation

Install the plugin globally for your local AI harness:

```bash
cd maestro-e2e-plugin
python3 bootstrap.py --target all-agents
```

## Usage

### 1. Initialize a Project
Run this once per Flutter repository to scaffold the hermetic test environment:
```bash
maestro-e2e --init
```
This ejects the bash scripts into `e2e_test/scripts/e2e` and the customizable LLM prompt templates into `e2e_test/prompts/`.

### 2. Run the Orchestrator
Trigger the orchestrator against a specific module and business flow:
```bash
maestro-e2e --module <your_module> --flow "<business_flow_name>"
```

### 3. Evaluate Artifacts Manually (Optional)
To test the Quality Gate on a specific artifact and trigger the self-healing error log:
```bash
maestro-e2e evaluate --stage stage_3 --file "e2e_test/modules/.../Happy Path.flow.yaml"
```

## Architecture

The Orchestrator follows a stateless, event-driven pattern. 
1. `router.py` analyzes the `e2e_test/` directory to detect drift or missing artifacts.
2. If an artifact is missing, it compiles a massive context prompt using `adapters.py`.
3. It writes the prompt to `.agentic/e2e_prompts/stage_X.prompt.md` for the AI harness to pick up.
4. If a stage fails the Quality Gate (`evaluator.py`), it drops an `.error.log` into the mailbox, triggering a self-healing iteration on the next run.
