"""AC-7: stage_4 prompt mapping + context inputs."""
from pathlib import Path

from orchestrator_core.adapters import build_stage_context, get_stage_prompt_file
from orchestrator_core.state import WorkflowTarget


def test_get_stage_prompt_file_stage4_resolves_healing_prompt(tmp_path):
    prompts_dir = tmp_path / "prompts"
    prompts_dir.mkdir()
    healing = prompts_dir / "4-execution-and-healing.prompt.md"
    healing.write_text("# healing", encoding="utf-8")

    resolved = get_stage_prompt_file("stage_4", prompts_dir)

    assert resolved == healing


def test_build_stage_context_stage4_includes_flow_path_blueprint_and_test_plan(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    workspace = tmp_path / "e2e_test"
    scenario = workspace / "modules" / "attendance" / "scenarios" / "archive"
    scenario.mkdir(parents=True)
    flow = scenario / "archive.flow.yaml"
    flow.write_text("appId: com.example\n---\n- launchApp\n", encoding="utf-8")
    (scenario / "blueprint.md").write_text("# blueprint body", encoding="utf-8")
    (scenario / "test-plan.md").write_text("# test plan body", encoding="utf-8")

    prompts_dir = tmp_path / "prompts"
    prompts_dir.mkdir()
    (prompts_dir / "4-execution-and-healing.prompt.md").write_text("sys", encoding="utf-8")

    target = WorkflowTarget(module="attendance", flow="archive")
    context = build_stage_context(target, "stage_4", "novo", prompts_dir, str(workspace))

    assert "--- INPUT: TARGET FLOW (path) ---" in context
    assert str(flow) in context
    assert "--- INPUT: WIDGET BLUEPRINT (blueprint.md) ---" in context
    assert "# blueprint body" in context
    assert "--- INPUT: TEST PLAN (test-plan.md) ---" in context
    assert "# test plan body" in context
    # Flow content is path-only — must not embed the YAML body as the primary input.
    assert "--- INPUT: TARGET FLOW (path) ---" in context
    path_section = context.split("--- INPUT: TARGET FLOW (path) ---", 1)[1]
    path_section = path_section.split("---", 1)[0]
    assert "appId:" not in path_section


def test_stage4_ejection_override_prefers_project_prompt(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    ejected = tmp_path / "e2e_test" / "prompts"
    ejected.mkdir(parents=True)
    override = ejected / "4-execution-and-healing.prompt.md"
    override.write_text("ejected-stage-4", encoding="utf-8")

    packaged = tmp_path / "packaged_prompts"
    packaged.mkdir()
    (packaged / "4-execution-and-healing.prompt.md").write_text("packaged", encoding="utf-8")

    resolved = get_stage_prompt_file("stage_4", packaged)

    assert resolved == override
