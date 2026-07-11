"""AC-3 regression: error.log presence beats freshness for correcao."""
from pathlib import Path
import time

from orchestrator_core.router import resolve_routing
from orchestrator_core.state import QueueState, Task, WorkflowTarget


def _write(path: Path, content: str = "x") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_error_log_wins_over_stale_artifact_for_stage3(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    workspace = tmp_path / "e2e_test"
    module = workspace / "modules" / "attendance"
    scenario = module / "scenarios" / "archive"

    _write(module / "domain.md", "domain")
    time.sleep(0.02)
    _write(scenario / "test-plan.md", "plan")
    time.sleep(0.02)
    _write(scenario / "blueprint.md", "blueprint")
    time.sleep(0.02)
    flow = scenario / "archive.flow.yaml"
    _write(flow, "flow")
    # Make stage_3 newer than stage_2 so freshness alone would NOT select atualizacao.
    time.sleep(0.02)
    flow.write_text("flow-fresh", encoding="utf-8")

    mailbox = tmp_path / ".agentic" / "e2e_prompts"
    mailbox.mkdir(parents=True)
    (mailbox / "stage_3.error.log").write_text("selector failed", encoding="utf-8")

    state = QueueState(
        target=WorkflowTarget(module="attendance", flow="archive"),
        tasks={"stage_3": Task(id="stage_3", skill_name="maestro_implementer")},
    )
    event = resolve_routing(state, str(workspace))

    assert event.type == "TaskSpawnedEvent"
    assert event.payload["task_id"] == "stage_3"
    assert event.payload["mode"] == "correcao"
