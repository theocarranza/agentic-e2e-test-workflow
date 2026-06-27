# Changelog

All notable changes to this project will be documented in this file.

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
