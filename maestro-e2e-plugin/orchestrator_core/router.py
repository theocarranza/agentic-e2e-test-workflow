import os
from pathlib import Path
from .state import QueueState, WorkflowTarget, Event, StageMode

def get_artifact_path(target: WorkflowTarget, stage_id: str, base_dir: str = "e2e_test") -> Path:
    """Resolves the canonical path for a given stage's artifact."""
    m = target.module
    f = target.flow or "default"
    
    base = Path(base_dir) / "modules" / m
    
    if stage_id == "stage_0":
        return base / "domain.md"
    elif stage_id == "stage_1":
        return base / "scenarios" / f / "test-plan.md"
    elif stage_id == "stage_2":
        return base / "scenarios" / f / "blueprint.md"
    elif stage_id == "stage_3":
        return base / "scenarios" / f / f"{f}.flow.yaml"
    
    raise ValueError(f"Unknown stage_id: {stage_id}")

def get_mtime(path: Path) -> float:
    """Returns the modification time of the file, or 0 if it does not exist."""
    return path.stat().st_mtime if path.exists() else 0.0

def resolve_routing(state: QueueState, base_dir: str = "e2e_test") -> Event:
    """
    Evaluates the artifact drift based on the orchestrator logic:
    1. Check for artifact existence in order 0 -> 3.
    2. Dispatch TaskSpawnedEvent for the first missing artifact (mode: NOVO).
    3. Or dispatch for the first outdated artifact (mode: ATUALIZACAO).
    """
    target = state.target
    
    paths = {
        "stage_0": get_artifact_path(target, "stage_0", base_dir),
        "stage_1": get_artifact_path(target, "stage_1", base_dir),
        "stage_2": get_artifact_path(target, "stage_2", base_dir),
        "stage_3": get_artifact_path(target, "stage_3", base_dir),
    }
    
    mtimes = {stage: get_mtime(path) for stage, path in paths.items()}
    
    # ---------------------------------------------------------
    # Stage 0: Domain Discovery (domain.md)
    # ---------------------------------------------------------
    if mtimes["stage_0"] == 0:
        return Event(type="TaskSpawnedEvent", payload={"task_id": "stage_0", "mode": StageMode.NOVO.value})
    if (Path.cwd() / ".agentic" / "e2e_prompts" / "stage_0.error.log").exists():
        return Event(type="TaskSpawnedEvent", payload={"task_id": "stage_0", "mode": "correcao"})
        
    # If no flow specified, the orchestrator pauses after Stage 0 to ask the user.
    if not target.flow:
        return Event(type="RequireFlowSelectionEvent", payload={"module": target.module})

    # ---------------------------------------------------------
    # Stage 1: Test Plan Author (test-plan.md)
    # ---------------------------------------------------------
    if mtimes["stage_1"] == 0:
        return Event(type="TaskSpawnedEvent", payload={"task_id": "stage_1", "mode": StageMode.NOVO.value})
    if (Path.cwd() / ".agentic" / "e2e_prompts" / "stage_1.error.log").exists():
        return Event(type="TaskSpawnedEvent", payload={"task_id": "stage_1", "mode": "correcao"})
    if mtimes["stage_1"] < mtimes["stage_0"]:
        return Event(type="TaskSpawnedEvent", payload={"task_id": "stage_1", "mode": StageMode.ATUALIZACAO.value})

    # ---------------------------------------------------------
    # Stage 2: Widget Blueprint (blueprint.md)
    # ---------------------------------------------------------
    if mtimes["stage_2"] == 0:
        return Event(type="TaskSpawnedEvent", payload={"task_id": "stage_2", "mode": StageMode.NOVO.value})
    if (Path.cwd() / ".agentic" / "e2e_prompts" / "stage_2.error.log").exists():
        return Event(type="TaskSpawnedEvent", payload={"task_id": "stage_2", "mode": "correcao"})
    if mtimes["stage_2"] < mtimes["stage_1"]:
        return Event(type="TaskSpawnedEvent", payload={"task_id": "stage_2", "mode": StageMode.ATUALIZACAO.value})
        
    # ---------------------------------------------------------
    # Stage 3: Maestro Implementer (.flow.yaml)
    # ---------------------------------------------------------
    if mtimes["stage_3"] == 0:
        return Event(type="TaskSpawnedEvent", payload={"task_id": "stage_3", "mode": StageMode.NOVO.value})
    if (Path.cwd() / ".agentic" / "e2e_prompts" / "stage_3.error.log").exists():
        return Event(type="TaskSpawnedEvent", payload={"task_id": "stage_3", "mode": "correcao"})
    if mtimes["stage_3"] < mtimes["stage_2"]:
        return Event(type="TaskSpawnedEvent", payload={"task_id": "stage_3", "mode": StageMode.ATUALIZACAO.value})
        
    # If everything is up to date, the pipeline is ready for E2E validation execution!
    return Event(type="PipelineUpToDateEvent", payload={"module": target.module, "flow": target.flow})
