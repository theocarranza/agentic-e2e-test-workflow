"""F10/F11: evaluate CLI exit codes and error.log lifecycle."""
import os
import subprocess
import sys
from pathlib import Path

import conftest

PYTHON = sys.executable
PLUGIN_ROOT = conftest.PLUGIN_ROOT


def _run_evaluate(cwd: Path, stage: str, artifact: Path) -> subprocess.CompletedProcess:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(PLUGIN_ROOT)
    return subprocess.run(
        [
            PYTHON,
            "-m",
            "orchestrator_core.main",
            "evaluate",
            "--stage",
            stage,
            "--file",
            str(artifact),
        ],
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
    )


def _pass_domain() -> str:
    return "\n".join(
        [
            "## 1. Domain Overview",
            "## 2. Exhaustive Data Model",
            "## 3. Lifecycle and Relevant States",
            "## 4. Functional Areas and Business Logic",
            "body",
        ]
    )


def test_evaluate_pass_exits_zero_and_leaves_no_error_log(tmp_path):
    artifact = tmp_path / "domain.md"
    artifact.write_text(_pass_domain(), encoding="utf-8")

    result = _run_evaluate(tmp_path, "stage_0", artifact)

    assert result.returncode == 0, result.stderr + result.stdout
    error_log = tmp_path / ".agentic" / "e2e_prompts" / "stage_0.error.log"
    assert not error_log.exists()


def test_evaluate_fail_exits_one_and_writes_error_log(tmp_path):
    artifact = tmp_path / "domain.md"
    artifact.write_text("incomplete", encoding="utf-8")

    result = _run_evaluate(tmp_path, "stage_0", artifact)

    assert result.returncode == 1
    error_log = tmp_path / ".agentic" / "e2e_prompts" / "stage_0.error.log"
    assert error_log.exists()
    assert "Missing required section" in error_log.read_text(encoding="utf-8")


def test_evaluate_pass_after_fail_removes_error_log(tmp_path):
    artifact = tmp_path / "domain.md"
    artifact.write_text("incomplete", encoding="utf-8")
    fail = _run_evaluate(tmp_path, "stage_0", artifact)
    assert fail.returncode == 1
    error_log = tmp_path / ".agentic" / "e2e_prompts" / "stage_0.error.log"
    assert error_log.exists()

    artifact.write_text(_pass_domain(), encoding="utf-8")
    passed = _run_evaluate(tmp_path, "stage_0", artifact)

    assert passed.returncode == 0, passed.stderr + passed.stdout
    assert not error_log.exists()
