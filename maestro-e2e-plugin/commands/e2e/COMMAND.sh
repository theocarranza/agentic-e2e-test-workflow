---
name: e2e
description: Kicks off the Maestro E2E test workflow.
arguments:
  - name: module
    description: "The specific module to test (e.g. 'authentication'). If omitted, runs the whole suite."
    required: false
---

# E2E Workflow Command

When the user runs `/e2e`, you must immediately initiate the Orchestrator-Worker pattern to run the tests.
Do NOT attempt to run bash commands yourself.

If a `module` argument is provided, pass `FLOW_FILTER=modules/{module}/...` to the worker.
Otherwise, instruct the worker to run the full suite.

1. Invoke the `maestro-worker` subagent.
2. Instruct it to use its MCP tools to run the tests and diagnose failures.
3. Wait for the worker to report the final exit code and summary.
4. Output the results to the user.
