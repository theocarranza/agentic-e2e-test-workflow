---
name: e2e
description: "Generates E2E Maestro tests. Uses an Orchestrator-Worker sub-agent pattern to traverse the 4-stage pipeline (Domain, Plan, Blueprint, Implementation)."
---

# E2E Maestro Test Generation Workflow (Orchestrator-Worker Pattern)

You are the **Orchestrator Agent**. Your job is to manage the E2E Maestro test generation pipeline by delegating the actual creation of artifacts to **Worker Sub-agents**, evaluating their work, and advancing the state machine.

## Supported Commands

- `/e2e start --module <module_name>`: Kicks off or resumes the E2E workflow for the specified module.
- `/e2e resume`: Re-runs the router to check the workspace state and pick up where you left off.

## The Orchestrator-Worker Loop

When the user invokes this skill, execute the following loop:

### Step 1: Route and Prepare (The Orchestrator)
1. Run the local engine to determine the next missing artifact and compile the prompt context:
   ```bash
   maestro-e2e --module <module_name>
   ```
2. The engine will analyze the workspace, detect the missing stage (e.g., `stage_0`), and compile the full system prompt (context + checklists) into the `.agentic/e2e_prompts/` directory (or output it directly).

### Step 2: Delegate to Worker (The Sub-Agent)
1. Do **NOT** generate the artifact yourself.
2. Read the compiled prompt.
3. Use the `invoke_subagent` tool to spawn a **Worker Sub-agent** (e.g., "Domain Analyst" for stage_0, "Maestro Implementer" for stage_3). 
4. Pass the compiled prompt as the sub-agent's instruction. Tell the sub-agent to strictly follow the prompt, save the output file to the exact path specified, and report back when finished.

### Step 3: Evaluate and Cascade (The Quality Gate)
1. When the sub-agent reports completion, evaluate the artifact using the local evaluator:
   ```bash
   maestro-e2e evaluate --stage <stage_name> --file <path/to/artifact.md>
   ```
2. If the evaluator returns critiques (FAIL):
   - Use `send_message` to send the critiques back to the sub-agent, instructing it to fix the file and resubmit.
3. If the evaluator returns an empty list (PASS):
   - The stage is complete! 
   - Terminate the sub-agent.
   - Go back to **Step 1** (`/e2e resume`) to let the Python engine route to the next stage in the pipeline!

## Rules for the Orchestrator
- Maintain strict discipline. You are the manager. Do not write Gherkin or Maestro YAML yourself.
- If the sub-agent gets stuck or fails the evaluator gate 3 times, stop the loop and ask the human user for help.
