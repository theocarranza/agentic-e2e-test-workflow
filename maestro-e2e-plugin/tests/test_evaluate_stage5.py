"""Stage-5 quality gate for execution reports (former stage_4)."""
from orchestrator_core.evaluator import evaluate_stage_5


def _report(status_line: str) -> str:
    return f"# Execution & Healing Report: archive\n\n{status_line}\n"


def test_stage5_pass_accepts_pass_status():
    assert evaluate_stage_5(_report("**Status**: PASS")) == []


def test_stage5_pass_accepts_healed_status():
    assert evaluate_stage_5(_report("**Status**: HEALED")) == []


def test_stage5_rejects_fatal_status():
    critiques = evaluate_stage_5(_report("**Status**: FATAL"))
    assert any("FATAL" in c for c in critiques)


def test_stage5_rejects_template_placeholder():
    critiques = evaluate_stage_5(_report("**Status**: [PASS | HEALED | FATAL]"))
    assert critiques
