"""Stage-3 quality gate must not pass when required tokens appear only in comments."""
from orchestrator_core.evaluator import evaluate_maestro_flow


def test_stage3_rejects_commented_placeholders():
    flow = """\
# appId: com.example
# launch_clean
---
- tapOn: "missing"
"""
    critiques = evaluate_maestro_flow(flow)
    assert critiques
    assert any("appId" in c for c in critiques)
    assert any("lifecycle subflow" in c for c in critiques)


def test_stage3_accepts_real_declarations():
    flow = """\
appId: com.example
---
- runFlow: launch_clean
"""
    assert evaluate_maestro_flow(flow) == []
