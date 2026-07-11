"""AC-8: single canonical engine copy under the plugin package."""
from pathlib import Path

import conftest


def test_root_orchestrator_core_does_not_exist():
    root_engine = conftest.REPO_ROOT / "orchestrator_core"
    assert not root_engine.exists(), (
        f"Stale root engine still present at {root_engine}; "
        "canonical copy is maestro-e2e-plugin/orchestrator_core/"
    )
