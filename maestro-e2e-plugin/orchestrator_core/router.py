import re
from pathlib import Path

from .state import QueueState, WorkflowTarget, Event, StageMode

QC_REJECTION_LIMIT = 3


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
    elif stage_id == "stage_4":
        return base / "scenarios" / f / "qc-report.md"
    elif stage_id == "stage_5":
        return base / "scenarios" / f / "execution-report.md"

    raise ValueError(f"Unknown stage_id: {stage_id}")


def get_mtime(path: Path) -> float:
    """Returns the modification time of the file, or 0 if it does not exist."""
    return path.stat().st_mtime if path.exists() else 0.0


def _mailbox_dir() -> Path:
    return Path.cwd() / ".agentic" / "e2e_prompts"


def _error_log(stage_id: str) -> Path:
    return _mailbox_dir() / f"{stage_id}.error.log"


def _qc_rejection_count_path() -> Path:
    return _mailbox_dir() / "stage_4.rejection_count"


def read_qc_rejection_count() -> int:
    path = _qc_rejection_count_path()
    if not path.exists():
        return 0
    try:
        return max(0, int(path.read_text(encoding="utf-8").strip() or "0"))
    except ValueError:
        return 0


def _qc_verdict_is_invalid(report_path: Path) -> bool:
    if not report_path.exists():
        return False
    text = report_path.read_text(encoding="utf-8")
    match = re.search(r"\*\*Verdict\*\*:\s*(\S+)", text, re.IGNORECASE)
    if not match:
        return False
    return match.group(1).strip().lower().strip("[]") == "invalid"


def _qc_needs_implementer_resubmit(qc_path: Path) -> bool:
    return _error_log("stage_4").exists() or _qc_verdict_is_invalid(qc_path)


def resolve_routing(state: QueueState, base_dir: str = "e2e_test") -> Event:
    """
    Evaluates the artifact drift based on the orchestrator logic:
    1. Check for artifact existence in order 0 -> 5.
    2. QC (stage_4) invalid / error.log re-routes to implementer (stage_3) correcao.
    3. After 3 consecutive QC rejections, trip the circuit breaker for the user.
    """
    target = state.target

    paths = {
        "stage_0": get_artifact_path(target, "stage_0", base_dir),
        "stage_1": get_artifact_path(target, "stage_1", base_dir),
        "stage_2": get_artifact_path(target, "stage_2", base_dir),
        "stage_3": get_artifact_path(target, "stage_3", base_dir),
        "stage_4": get_artifact_path(target, "stage_4", base_dir),
        "stage_5": get_artifact_path(target, "stage_5", base_dir),
    }

    mtimes = {stage: get_mtime(path) for stage, path in paths.items()}

    # ---------------------------------------------------------
    # Stage 0: Domain Discovery (domain.md)
    # ---------------------------------------------------------
    if mtimes["stage_0"] == 0:
        return Event(type="TaskSpawnedEvent", payload={"task_id": "stage_0", "mode": StageMode.NOVO.value})
    if _error_log("stage_0").exists():
        return Event(type="TaskSpawnedEvent", payload={"task_id": "stage_0", "mode": "correcao"})

    if not target.flow:
        return Event(type="RequireFlowSelectionEvent", payload={"module": target.module})

    # ---------------------------------------------------------
    # Stage 1: Test Plan Author (test-plan.md)
    # ---------------------------------------------------------
    if mtimes["stage_1"] == 0:
        return Event(type="TaskSpawnedEvent", payload={"task_id": "stage_1", "mode": StageMode.NOVO.value})
    if _error_log("stage_1").exists():
        return Event(type="TaskSpawnedEvent", payload={"task_id": "stage_1", "mode": "correcao"})
    if mtimes["stage_1"] < mtimes["stage_0"]:
        return Event(type="TaskSpawnedEvent", payload={"task_id": "stage_1", "mode": StageMode.ATUALIZACAO.value})

    # ---------------------------------------------------------
    # Stage 2: Widget Blueprint (blueprint.md)
    # ---------------------------------------------------------
    if mtimes["stage_2"] == 0:
        return Event(type="TaskSpawnedEvent", payload={"task_id": "stage_2", "mode": StageMode.NOVO.value})
    if _error_log("stage_2").exists():
        return Event(type="TaskSpawnedEvent", payload={"task_id": "stage_2", "mode": "correcao"})
    if mtimes["stage_2"] < mtimes["stage_1"]:
        return Event(type="TaskSpawnedEvent", payload={"task_id": "stage_2", "mode": StageMode.ATUALIZACAO.value})

    # ---------------------------------------------------------
    # Stage 3: Maestro Implementer (.flow.yaml)
    # ---------------------------------------------------------
    if mtimes["stage_3"] == 0:
        return Event(type="TaskSpawnedEvent", payload={"task_id": "stage_3", "mode": StageMode.NOVO.value})
    if _error_log("stage_3").exists():
        return Event(type="TaskSpawnedEvent", payload={"task_id": "stage_3", "mode": "correcao"})
    if mtimes["stage_3"] < mtimes["stage_2"]:
        return Event(type="TaskSpawnedEvent", payload={"task_id": "stage_3", "mode": StageMode.ATUALIZACAO.value})

    # ---------------------------------------------------------
    # Stage 4: E2E Quality Control (qc-report.md)
    # ---------------------------------------------------------
    if _qc_needs_implementer_resubmit(paths["stage_4"]):
        rejection_count = read_qc_rejection_count()
        if rejection_count >= QC_REJECTION_LIMIT:
            return Event(
                type="CircuitBreakerTrippedEvent",
                payload={
                    "task_id": "stage_4",
                    "rejection_count": rejection_count,
                    "message": (
                        f"Flow rejected by QC {rejection_count} times in a row. "
                        "Orchestrator interrupted — human review required."
                    ),
                },
            )
        return Event(
            type="TaskSpawnedEvent",
            payload={"task_id": "stage_3", "mode": "correcao", "reason": "qc_invalid"},
        )

    if mtimes["stage_4"] == 0:
        return Event(type="TaskSpawnedEvent", payload={"task_id": "stage_4", "mode": StageMode.NOVO.value})
    if mtimes["stage_4"] < mtimes["stage_3"]:
        return Event(type="TaskSpawnedEvent", payload={"task_id": "stage_4", "mode": StageMode.ATUALIZACAO.value})

    # ---------------------------------------------------------
    # Stage 5: Execution & Self-Healing
    # ---------------------------------------------------------
    if mtimes["stage_5"] == 0:
        return Event(type="TaskSpawnedEvent", payload={"task_id": "stage_5", "mode": StageMode.NOVO.value})
    if _error_log("stage_5").exists():
        return Event(type="TaskSpawnedEvent", payload={"task_id": "stage_5", "mode": "correcao"})
    if mtimes["stage_5"] < mtimes["stage_4"]:
        return Event(type="TaskSpawnedEvent", payload={"task_id": "stage_5", "mode": StageMode.ATUALIZACAO.value})

    return Event(type="PipelineUpToDateEvent", payload={"module": target.module, "flow": target.flow})
