# Maestro E2E Orchestrator Plugin

[![Release](https://img.shields.io/github/v/release/theocarranza/agentic-e2e-test-workflow?display_name=tag&sort=semver)](https://github.com/theocarranza/agentic-e2e-test-workflow/releases/latest)
[![Python](https://img.shields.io/badge/python-3-blue?logo=python&logoColor=white)](https://www.python.org/)
[![Maestro](https://img.shields.io/badge/Maestro-E2E-00B4AB)](https://maestro.mobile.dev/)
[![Flutter](https://img.shields.io/badge/Flutter-compatible-02569B?logo=flutter&logoColor=white)](https://flutter.dev/)

Autonomous, multi-agent orchestration for generating, validating, and running Flutter UI E2E tests with [Maestro](https://maestro.mobile.dev/). The plugin connects local LLM harnesses (Claude Code, AI Codex, Antigravity) to a physical Android/iOS test stack through a filesystem mailbox.

Package name: `maestro-e2e-workflow`.

## Features

- **Harness-agnostic** — any local AI agent can drive the loop via `.agentic/e2e_prompts/`
- **Five-stage pipeline**
  1. **Domain discovery** — document business logic from Dart sources (adversarial focus)
  2. **Test plan** — BDD/Gherkin scenarios
  3. **Widget blueprint** — UI selectors and semantics from the codebase
  4. **Maestro implementer** — `.flow.yaml` / `.subflow.yaml` artifacts
  5. **Execution & self-healing** — run on device, debug with `maestro hierarchy`, auto-correct, and record learnings in `common-pitfalls.md`
- **Self-healing resume** — on Maestro or lint failure, the orchestrator captures the stack trace and redispatches in *correcao* (remediation) mode
- **Hermetic scaffolding** — `/e2e init` ejects portable bash scripts, emulator helpers, and prompt templates into your repo for CI use

## Requirements

- Python 3
- A Flutter project target
- [Maestro](https://maestro.mobile.dev/) CLI
- Android emulator / iOS simulator (or a connected device) for stage 5

## Installation

Install the plugin for your local AI harnesses:

```bash
cd maestro-e2e-plugin
python3 bootstrap.py --target all-agents
```

Re-run bootstrap after upgrades so the global `maestro-e2e` wrapper stays in sync.

## Usage

### 1. Initialize a project

Run once per Flutter repository to scaffold the hermetic test environment:

```bash
maestro-e2e --init
```

This ejects scripts into `e2e_test/scripts/e2e` and LLM prompt templates into `e2e_test/prompts/`.

### 2. Run the orchestrator

Point the orchestrator at a module and business flow:

```bash
maestro-e2e --module <your_module> --flow "<business_flow_name>"
```

### 3. Evaluate an artifact (optional)

Run the quality gate on a single artifact and, on failure, write the self-healing error log:

```bash
maestro-e2e evaluate --stage stage_3 --file "e2e_test/modules/.../Happy Path.flow.yaml"
```

## Architecture

The orchestrator is a stateless, mailbox-driven loop:

1. `router.py` inspects `e2e_test/` for missing or drifted artifacts.
2. For the next incomplete stage, `adapters.py` compiles context and writes `.agentic/e2e_prompts/stage_X.prompt.md`.
3. The AI harness picks up the prompt, produces the artifact, and returns control.
4. `evaluator.py` runs the quality gate; on failure it drops `.error.log` into the mailbox so the next run enters remediation. On PASS, the stage error log is cleared.

Canonical engine path: `maestro-e2e-plugin/orchestrator_core/` (no root-level duplicate).
