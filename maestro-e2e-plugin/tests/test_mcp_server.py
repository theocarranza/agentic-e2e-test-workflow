"""MCP server boot_emulator must invoke the real boot script and surface failures."""
import importlib.util
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import conftest

PLUGIN_ROOT = conftest.PLUGIN_ROOT
SERVER_PATH = PLUGIN_ROOT / "mcp" / "server.py"


def _load_boot_emulator():
    spec = importlib.util.spec_from_file_location("maestro_mcp_server", SERVER_PATH)
    server = importlib.util.module_from_spec(spec)
    sys.modules["maestro_mcp_server"] = server
    spec.loader.exec_module(server)
    return server.boot_emulator


def test_boot_emulator_uses_boot_emulator_script(tmp_path):
    boot_emulator = _load_boot_emulator()
    captured: dict[str, object] = {}

    def fake_run(cmd, **kwargs):
        captured["cmd"] = cmd
        captured["cwd"] = kwargs.get("cwd")
        return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")

    module = sys.modules["maestro_mcp_server"]
    with patch.object(module, "subprocess") as mock_subprocess:
        mock_subprocess.run = fake_run
        result = boot_emulator(str(tmp_path))

    assert captured["cmd"] == ["bash", "e2e_test/scripts/e2e/boot-emulator.sh"]
    assert captured["cwd"] == str(tmp_path)
    assert result == "Emulator is ready."


def test_boot_emulator_surfaces_nonzero_exit(tmp_path):
    boot_emulator = _load_boot_emulator()

    def fake_run(cmd, **kwargs):
        return subprocess.CompletedProcess(
            cmd,
            1,
            stdout="",
            stderr="ERROR: adb not found",
        )

    module = sys.modules["maestro_mcp_server"]
    with patch.object(module, "subprocess") as mock_subprocess:
        mock_subprocess.run = fake_run
        result = boot_emulator(str(tmp_path))

    assert "Failed to boot emulator" in result
    assert "exit 1" in result
    assert "adb not found" in result


def test_boot_emulator_script_sources_library_and_calls_ensure(tmp_path):
    plugin_scripts = PLUGIN_ROOT / "scripts" / "e2e"
    project_scripts = tmp_path / "e2e_test" / "scripts" / "e2e"
    project_scripts.mkdir(parents=True)

    for script in plugin_scripts.iterdir():
        if script.is_file():
            (project_scripts / script.name).write_text(
                script.read_text(encoding="utf-8"),
                encoding="utf-8",
            )

    boot_script = project_scripts / "boot-emulator.sh"
    boot_script.chmod(0o755)

    # Stub preflight + emulator hooks so the script exercises the wiring without real tools.
    for name in ("lib-preflight.sh", "lib-emulator.sh"):
        path = project_scripts / name
        path.write_text(
            path.read_text(encoding="utf-8")
            + '\npreflight_detect_tools() { :; }\nensure_avd_running() { echo "booted"; }\n',
            encoding="utf-8",
        )

    result = subprocess.run(
        ["bash", "e2e_test/scripts/e2e/boot-emulator.sh"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert "booted" in result.stdout
