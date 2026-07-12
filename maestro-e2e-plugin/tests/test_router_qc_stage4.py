"""F5 router: QC invalid routes implementer correcao; stage_5 after valid QC."""
from pathlib import Path

from orchestrator_core.main import init_workflow
from orchestrator_core.router import get_artifact_path, resolve_routing


def test_artifact_paths_stage4_qc_and_stage5_execution(tmp_path):
    from orchestrator_core.state import WorkflowTarget

    target = WorkflowTarget(module="attendance", flow="archive")
    base = tmp_path / "e2e_test"
    assert get_artifact_path(target, "stage_4", str(base)).name == "qc-report.md"
    assert get_artifact_path(target, "stage_5", str(base)).name == "execution-report.md"


def test_qc_error_log_routes_stage3_correcao(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    workspace = tmp_path / "e2e_test"
    scenario = workspace / "modules" / "mod" / "scenarios" / "login"
    scenario.mkdir(parents=True)
    (workspace / "modules" / "mod" / "domain.md").write_text("d", encoding="utf-8")
    (scenario / "test-plan.md").write_text("p", encoding="utf-8")
    (scenario / "blueprint.md").write_text("b", encoding="utf-8")
    (scenario / "login.flow.yaml").write_text("appId: x\n", encoding="utf-8")
    (scenario / "qc-report.md").write_text("**Verdict**: invalid\n", encoding="utf-8")

    mailbox = tmp_path / ".agentic" / "e2e_prompts"
    mailbox.mkdir(parents=True)
    (mailbox / "stage_4.error.log").write_text("Quality Gate Failed:\ninvalid", encoding="utf-8")

    state = init_workflow("mod", "login")
    event = resolve_routing(state, base_dir=str(workspace))

    assert event.type == "TaskSpawnedEvent"
    assert event.payload["task_id"] == "stage_3"
    assert event.payload["mode"] == "correcao"


def test_valid_qc_missing_execution_routes_stage5(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    workspace = tmp_path / "e2e_test"
    scenario = workspace / "modules" / "mod" / "scenarios" / "login"
    scenario.mkdir(parents=True)
    (workspace / "modules" / "mod" / "domain.md").write_text("d", encoding="utf-8")
    (scenario / "test-plan.md").write_text("p", encoding="utf-8")
    (scenario / "blueprint.md").write_text("b", encoding="utf-8")
    flow = scenario / "login.flow.yaml"
    flow.write_text("appId: x\n", encoding="utf-8")
    qc = scenario / "qc-report.md"
    qc.write_text("**Verdict**: valid\n", encoding="utf-8")
    # Ensure QC is newer than flow, and flow is not older than blueprint/plan
    import os
    import time

    now = time.time()
    for path in (
        workspace / "modules" / "mod" / "domain.md",
        scenario / "test-plan.md",
        scenario / "blueprint.md",
    ):
        os.utime(path, (now - 30, now - 30))
    os.utime(flow, (now - 10, now - 10))
    os.utime(qc, (now, now))

    state = init_workflow("mod", "login")
    event = resolve_routing(state, base_dir=str(workspace))

    assert event.type == "TaskSpawnedEvent"
    assert event.payload["task_id"] == "stage_5"


def test_three_qc_rejections_trip_circuit_breaker(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    workspace = tmp_path / "e2e_test"
    scenario = workspace / "modules" / "mod" / "scenarios" / "login"
    scenario.mkdir(parents=True)
    (workspace / "modules" / "mod" / "domain.md").write_text("d", encoding="utf-8")
    (scenario / "test-plan.md").write_text("p", encoding="utf-8")
    (scenario / "blueprint.md").write_text("b", encoding="utf-8")
    (scenario / "login.flow.yaml").write_text("appId: x\n", encoding="utf-8")
    (scenario / "qc-report.md").write_text("**Verdict**: invalid\n", encoding="utf-8")

    mailbox = tmp_path / ".agentic" / "e2e_prompts"
    mailbox.mkdir(parents=True)
    (mailbox / "stage_4.error.log").write_text("fail", encoding="utf-8")
    (mailbox / "stage_4.rejection_count").write_text("3", encoding="utf-8")

    state = init_workflow("mod", "login")
    event = resolve_routing(state, base_dir=str(workspace))

    assert event.type == "CircuitBreakerTrippedEvent"
    assert event.payload["task_id"] == "stage_4"
    assert "3" in str(event.payload.get("message", "")) or event.payload.get("rejection_count") == 3
