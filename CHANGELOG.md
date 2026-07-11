# Changelog

All notable changes to this project will be documented in this file.

## [0.1.1] - 2026-07-11

### Fixed
- Stage-4 dispatch prompt mapping and context inputs (F1).
- `maestro-e2e evaluate` quality-gate subcommand (F11).
- `error.log` lifecycle: cleared on PASS so correcao loops can complete (F10).

### Removed
- Stale root `orchestrator_core/` copy; canonical engine is `maestro-e2e-plugin/orchestrator_core/` (F2, history-preserved).

## [0.1.0] - 2026-06-27

### Added
- **Core Orchestrator**: Implemented the Python-based state machine for routing E2E generation tasks.
- **Stage 0-3 Pipeline**: Complete workflow for Domain Discovery, Test Plan Authoring, Widget Blueprinting, and Maestro Implementation.
- **Dynamic Globbing**: `adapters.py` now recursively searches for Dart source code (`lib/modules/**/<target>/**/*.dart`) to handle flexible repository architectures.
- **Multi-Harness Installer**: Added `bootstrap.py` to seamlessly install the plugin into Antigravity, Claude Code, and AI Codex.
- **Scaffold Command**: Added `--init` command to eject hermetic E2E bash scripts and customizable prompt templates to target repositories.
- **Self-Healing Resume Loop**: Wired `evaluator.py` to catch physical execution errors (e.g., Maestro stack traces), dump them to `.agentic/e2e_prompts/*.error.log`, and trigger the `correcao` mode for autonomous LLM remediation.

### Changed
- Moved AI context compilation from generic CLI parameters to a robust, file-based ephemeral mailbox (`.agentic/e2e_prompts/`) to bypass CLI character limits across different AI harnesses.
