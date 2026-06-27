import os
from pathlib import Path
from typing import Dict, Any, Optional
from .state import WorkflowTarget
from .router import get_artifact_path

def load_file_content(path: Path) -> str:
    """Safely loads file content if it exists, else returns an empty string."""
    if not path.exists():
        return ""
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def get_stage_prompt_file(stage_id: str, prompts_dir: Path) -> Path:
    """Maps a stage_id to its corresponding prompt file."""
    mapping = {
        "stage_0": "0-domain-discovery.prompt.md",
        "stage_1": "1-test-plan-author.prompt.md",
        "stage_2": "2-widget-blueprint.prompt.md",
        "stage_3": "3-maestro-implementer.prompt.md"
    }
    if stage_id not in mapping:
        raise ValueError(f"Unknown stage: {stage_id}")
    return prompts_dir / mapping[stage_id]

def build_stage_context(target: WorkflowTarget, stage_id: str, mode: str, prompts_dir: Path, workspace_dir: str = "e2e_test") -> str:
    """
    Constructs the final prompt string for the LLM by combining the system prompt
    with the necessary upstream artifacts and source code based on the stage.
    """
    prompt_file = get_stage_prompt_file(stage_id, prompts_dir)
    system_prompt = load_file_content(prompt_file)
    
    context_blocks = [
        f"--- CONTEXT: EXECUTION MODE ---",
        f"Mode: {mode}",
        f"Target Module: {target.module}",
        f"Target Flow: {target.flow if target.flow else 'N/A'}",
        ""
    ]
    
    # Inject inputs based on the stage dependencies defined in orchestrator.prompt.md
    if stage_id == "stage_0":
        # Needs module code + golden seed. 
        # (In a real implementation, we would glob the lib/ directory here)
        context_blocks.append("--- INPUT: MODULE SOURCE CODE ---")
        context_blocks.append("[Source code placeholder]")
        
    elif stage_id == "stage_1":
        # Needs domain.md + business flow
        domain_path = get_artifact_path(target, "stage_0", workspace_dir)
        context_blocks.append("--- INPUT: DOMAIN DISCOVERY (domain.md) ---")
        context_blocks.append(load_file_content(domain_path))
        
    elif stage_id == "stage_2":
        # Needs test-plan.md + widget tree
        test_plan_path = get_artifact_path(target, "stage_1", workspace_dir)
        context_blocks.append("--- INPUT: TEST PLAN (test-plan.md) ---")
        context_blocks.append(load_file_content(test_plan_path))
        context_blocks.append("--- INPUT: WIDGET TREE ---")
        context_blocks.append("[Widget tree diagnostic placeholder]")
        
    elif stage_id == "stage_3":
        # Needs test-plan.md + blueprint.md
        test_plan_path = get_artifact_path(target, "stage_1", workspace_dir)
        blueprint_path = get_artifact_path(target, "stage_2", workspace_dir)
        context_blocks.append("--- INPUT: TEST PLAN (test-plan.md) ---")
        context_blocks.append(load_file_content(test_plan_path))
        context_blocks.append("--- INPUT: WIDGET BLUEPRINT (blueprint.md) ---")
        context_blocks.append(load_file_content(blueprint_path))

    # Combine into a final prompt payload
    final_prompt = (
        f"<system_instructions>\n{system_prompt}\n</system_instructions>\n\n"
        f"<execution_context>\n{chr(10).join(context_blocks)}\n</execution_context>\n"
    )
    
    return final_prompt
