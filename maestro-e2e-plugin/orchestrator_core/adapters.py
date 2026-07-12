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
        "stage_3": "3-maestro-implementer.prompt.md",
        "stage_4": "4-e2e-quality-control.prompt.md",  # F5: LLM QC
        "stage_5": "4-execution-and-healing.prompt.md",  # F5: was stage_4
    }
    if stage_id not in mapping:
        raise ValueError(f"Unknown stage: {stage_id}")
        
    file_name = mapping[stage_id]
    
    # Check if the user ejected the prompts into their project
    project_prompt = Path.cwd() / "e2e_test" / "prompts" / file_name
    if project_prompt.exists():
        return project_prompt
        
    return prompts_dir / file_name

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
    
    if mode == "correcao":
        # Load the failed artifact depending on stage
        failed_artifact_path = get_artifact_path(target, stage_id, workspace_dir)
        if failed_artifact_path.exists():
            context_blocks.append("--- INPUT: PREVIOUS FAILED ARTIFACT ---")
            context_blocks.append(f"```\n{load_file_content(failed_artifact_path)}\n```")
            
        error_log = Path.cwd() / ".agentic" / "e2e_prompts" / f"{stage_id}.error.log"
        if error_log.exists():
            context_blocks.append("--- INPUT: QUALITY GATE FEEDBACK (RESUME LOOP) ---")
            context_blocks.append(f"The previous execution of this stage failed the automated Quality Gate. Fix the artifact according to the error below:")
            context_blocks.append(f"```text\n{error_log.read_text()}\n```")
    
    # Inject inputs based on the stage dependencies defined in orchestrator.prompt.md
    if stage_id == "stage_0":
        context_blocks.append("--- INPUT: MODULE SOURCE CODE ---")
        
        lib_path = Path.cwd() / "lib"
        # Search for any directory matching the module name
        target_dirs = [d for d in lib_path.rglob(f"*{target.module}*") if d.is_dir()]
        
        dart_files = []
        if not target_dirs:
            print(f"[!] Warning: Could not find directory matching '{target.module}'. Sweeping entire lib/")
            dart_files = list(lib_path.rglob("*.dart"))
        else:
            for d in target_dirs:
                dart_files.extend(d.rglob("*.dart"))
                
        # Deduplicate files just in case of nested matches
        dart_files = list(set(dart_files))
        
        if not dart_files:
            context_blocks.append(f"[No Dart source code found for module '{target.module}']")
        else:
            for dart_file in dart_files:
                try:
                    code = load_file_content(dart_file)
                    rel_path = dart_file.relative_to(Path.cwd())
                    context_blocks.append(f"// File: {rel_path}\n```dart\n{code}\n```\n")
                except Exception:
                    pass
        
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
        # Needs test-plan.md + blueprint.md; QC feedback when resubmitting after invalid.
        test_plan_path = get_artifact_path(target, "stage_1", workspace_dir)
        blueprint_path = get_artifact_path(target, "stage_2", workspace_dir)
        context_blocks.append("--- INPUT: TEST PLAN (test-plan.md) ---")
        context_blocks.append(load_file_content(test_plan_path))
        context_blocks.append("--- INPUT: WIDGET BLUEPRINT (blueprint.md) ---")
        context_blocks.append(load_file_content(blueprint_path))
        qc_path = get_artifact_path(target, "stage_4", workspace_dir)
        if mode == "correcao" and qc_path.exists():
            context_blocks.append("--- INPUT: QC REPORT (qc-report.md) ---")
            context_blocks.append(load_file_content(qc_path))
        qc_error = Path.cwd() / ".agentic" / "e2e_prompts" / "stage_4.error.log"
        if mode == "correcao" and qc_error.exists():
            context_blocks.append("--- INPUT: QC QUALITY GATE FEEDBACK ---")
            context_blocks.append(f"```text\n{qc_error.read_text(encoding='utf-8')}\n```")

    elif stage_id == "stage_4":
        # LLM QC reviews one flow document against declared structural rules.
        flow_path = get_artifact_path(target, "stage_3", workspace_dir)
        context_blocks.append("--- INPUT: TARGET FLOW ---")
        context_blocks.append(f"Path: {flow_path}")
        context_blocks.append(f"```yaml\n{load_file_content(flow_path)}\n```")

    elif stage_id == "stage_5":
        # Flow by path (Stage 5 edits on disk during healing); upstream artifacts consultable.
        flow_path = get_artifact_path(target, "stage_3", workspace_dir)
        context_blocks.append("--- INPUT: TARGET FLOW (path) ---")
        context_blocks.append(str(flow_path))
        context_blocks.append("--- INPUT: QC REPORT (qc-report.md) ---")
        context_blocks.append(load_file_content(get_artifact_path(target, "stage_4", workspace_dir)))
        context_blocks.append("--- INPUT: WIDGET BLUEPRINT (blueprint.md) ---")
        context_blocks.append(load_file_content(get_artifact_path(target, "stage_2", workspace_dir)))
        context_blocks.append("--- INPUT: TEST PLAN (test-plan.md) ---")
        context_blocks.append(load_file_content(get_artifact_path(target, "stage_1", workspace_dir)))

    # Combine into a final prompt payload
    final_prompt = (
        f"<system_instructions>\n{system_prompt}\n</system_instructions>\n\n"
        f"<execution_context>\n{chr(10).join(context_blocks)}\n</execution_context>\n"
    )
    
    return final_prompt
