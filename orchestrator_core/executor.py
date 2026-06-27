import time
from typing import Optional
from .state import QueueState, Event
from .adapters import build_stage_context
from .evaluator import evaluate_artifact
from pathlib import Path

def mock_llm_call(prompt: str, stage_id: str) -> str:
    """A mock LLM implementation for testing the workflow without incurring token costs."""
    # Simulate processing time
    time.sleep(1)
    
    if stage_id == "stage_0":
        return (
            "# Module: Attendance\n\n"
            "## 1. Domain Overview\nMock overview.\n\n"
            "## 2. Exhaustive Data Model\nMock table.\n\n"
            "## 3. Lifecycle and Relevant States\nMock states.\n\n"
            "## 4. Functional Areas and Business Logic\nMock logic.\n"
        )
    elif stage_id == "stage_1":
        return (
            "# Test Plan: Create Attendance\n\n"
            "## Implementation Notes\nMock notes.\n\n"
            "```gherkin\nFeature: Attendance\nScenario: Happy Path\n```\n"
        )
    elif stage_id == "stage_2":
        return (
            "# Blueprint: Create Attendance\n\n"
            "| Element | Widget | Type | Current Selector | Gap |\n"
            "|---|---|---|---|---|\n"
            "## Consolidated Semantics to Add\nMock semantics.\n"
        )
    elif stage_id == "stage_3":
        return (
            "appId: life.mock.app\n"
            "---\n"
            "- runFlow: ../common/subflows/launch_clean.subflow.yaml\n"
            "- tapOn: { id: 'mock' }\n"
        )
    return "Unknown output"

def handle_task_execution(state: QueueState, event: Event, stream, prompts_dir: Path, workspace_dir: str):
    """Executes a task when a TaskSpawnedEvent is detected."""
    task_id = event.payload.get("task_id")
    mode = event.payload.get("mode")
    
    print(f"\n[Executor] Starting execution for {task_id} in mode: {mode}")
    
    # 1. Build Prompt
    prompt = build_stage_context(state.target, task_id, mode, prompts_dir, workspace_dir)
    print(f"[Executor] Compiled prompt ({len(prompt)} chars). Invoking Agent...")
    
    # 2. Call LLM
    output_content = mock_llm_call(prompt, task_id)
    print(f"[Executor] Agent produced artifact ({len(output_content)} chars).")
    
    # 3. Validate
    critiques = evaluate_artifact(task_id, output_content)
    
    if critiques:
        print(f"[Executor] Validation FAILED! Critiques: {critiques}")
        # Dispatch failure
        stream.dispatch(Event("TaskFailedEvent", {"task_id": task_id, "critique": critiques[0]}))
    else:
        print(f"[Executor] Validation PASSED!")
        # Write to disk!
        # from .router import get_artifact_path
        # out_path = get_artifact_path(state.target, task_id, workspace_dir)
        # out_path.parent.mkdir(parents=True, exist_ok=True)
        # out_path.write_text(output_content)
        
        # Dispatch completion
        stream.dispatch(Event("TaskCompletedEvent", {"task_id": task_id, "output": output_content}))

def executor_hook(state: QueueState, event: Event, stream, prompts_dir: Path, workspace_dir: str):
    """Subscribes to the stream and executes tasks asynchronously."""
    if event.type == "TaskSpawnedEvent":
        # In a real app, this would be an async background task to not block the stream
        handle_task_execution(state, event, stream, prompts_dir, workspace_dir)
