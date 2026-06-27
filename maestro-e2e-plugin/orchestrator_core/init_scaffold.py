import os
import shutil
from pathlib import Path

def scaffold_workspace(workspace_dir: Path, plugin_root: Path):
    """
    Scaffolds the e2e_test directory in the target project.
    Copies scripts and prompt templates from the plugin bundle to the project.
    """
    e2e_dir = workspace_dir / "e2e_test"
    e2e_dir.mkdir(parents=True, exist_ok=True)
    
    # Scaffold scripts
    project_scripts = e2e_dir / "scripts" / "e2e"
    plugin_scripts = plugin_root / "scripts" / "e2e"
    
    if not project_scripts.exists() and plugin_scripts.exists():
        print(f"[*] Scaffolding E2E Scripts to {project_scripts}...")
        # create parent if needed
        (e2e_dir / "scripts").mkdir(exist_ok=True)
        shutil.copytree(plugin_scripts, project_scripts)
        
    # Scaffold prompts
    project_prompts = e2e_dir / "prompts"
    plugin_prompts = plugin_root / "orchestrator_core" / "prompts"
    
    if not project_prompts.exists() and plugin_prompts.exists():
        print(f"[*] Scaffolding Prompt Templates to {project_prompts}...")
        shutil.copytree(plugin_prompts, project_prompts)
        
    # Scaffold common subflows
    common_subflows = e2e_dir / "common" / "subflows"
    common_subflows.mkdir(parents=True, exist_ok=True)
    
    launch_clean = common_subflows / "launch_clean.subflow.yaml"
    if not launch_clean.exists():
        print(f"[*] Scaffolding default launch_clean subflow...")
        launch_clean.write_text("appId: ${APP_ID}\n---\n- clearState\n- launchApp\n")
        
    print("[*] E2E scaffolding complete!")
    print("    - Scripts are in e2e_test/scripts/")
    print("    - Prompts are in e2e_test/prompts/ (Customize them for this specific project!)")
