"""Stage-4 QC gate: verdict must be exactly valid (LLM qc-report.md)."""
from orchestrator_core.evaluator import evaluate_stage_4


def _qc(verdict_line: str, extra: str = "") -> str:
    body = f"# E2E Quality Control Report\n\n{verdict_line}\n"
    if extra:
        body += f"\n{extra}\n"
    return body


def test_stage4_accepts_valid_verdict():
    assert evaluate_stage_4(_qc("**Verdict**: valid")) == []


def test_stage4_rejects_invalid_verdict():
    critiques = evaluate_stage_4(
        _qc("**Verdict**: invalid", "## Violations\n- missing appId")
    )
    assert any("invalid" in c.lower() for c in critiques)


def test_stage4_rejects_missing_verdict():
    critiques = evaluate_stage_4("# E2E Quality Control Report\n\nNo verdict here.\n")
    assert critiques


def test_stage4_rejects_placeholder_verdict():
    critiques = evaluate_stage_4(_qc("**Verdict**: [valid | invalid]"))
    assert critiques
