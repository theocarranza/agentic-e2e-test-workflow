import time
from typing import Optional
from .state import QueueState, Event
from .adapters import build_stage_context
from .evaluator import evaluate_artifact
from pathlib import Path

def handle_task_execution(state: QueueState, event: Event, stream, prompts_dir: Path, workspace_dir: str):
    """Executes a task when a TaskSpawnedEvent is detected."""
    task_id = event.payload.get("task_id")
    mode = event.payload.get("mode")
    
    print(f"\n[Executor] Starting execution for {task_id} in mode: {mode}")
    
    # 1. Build Prompt
    prompt = build_stage_context(state.target, task_id, mode, prompts_dir, workspace_dir)
    print(f"[Executor] Compiled prompt ({len(prompt)} chars).")
    
    # 2. Drop the Prompt for the Orchestrator Agent
    prompt_out = Path(".agentic/e2e_prompts") / f"{task_id}.prompt.md"
    prompt_out.parent.mkdir(parents=True, exist_ok=True)
    prompt_out.write_text(prompt)
    
    print(f"==================================================")
    print(f"[ATTENTION ORCHESTRATOR AGENT]")
    print(f"The System Prompt for {task_id} has been written to:")
    print(f"-> {prompt_out.absolute()}")
    print(f"Action Required: Use `invoke_subagent` to spawn a Worker sub-agent.")
    print(f"Pass the contents of that file as the Worker's `Prompt`.")
    print(f"Wait for the Worker to finish before proceeding.")
    print(f"==================================================")

def executor_hook(state: QueueState, event: Event, stream, prompts_dir: Path, workspace_dir: str):
    """Subscribes to the stream and executes tasks asynchronously."""
    if event.type == "TaskSpawnedEvent":
        # In a real app, this would be an async background task to not block the stream
        handle_task_execution(state, event, stream, prompts_dir, workspace_dir)
