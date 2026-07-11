"""MCP server boot_emulator must invoke the real boot script and surface failures."""
import importlib.util
import json
import subprocess
import sys
import types
from pathlib import Path
from unittest.mock import patch

import conftest

PLUGIN_ROOT = conftest.PLUGIN_ROOT
SERVER_PATH = PLUGIN_ROOT / "maestro_mcp" / "server.py"


def _load_boot_emulator():
    class FakeFastMCP:
        def __init__(self, _name):
            pass

        def tool(self):
            return lambda function: function

        def run_stdio(self):
            pass

    mcp_package = types.ModuleType("mcp")
    mcp_package.__path__ = []
    mcp_server_package = types.ModuleType("mcp.server")
    mcp_server_package.__path__ = []
    fastmcp_module = types.ModuleType("mcp.server.fastmcp")
    fastmcp_module.FastMCP = FakeFastMCP

    spec = importlib.util.spec_from_file_location("maestro_mcp_server", SERVER_PATH)
    server = importlib.util.module_from_spec(spec)
    with patch.dict(
        sys.modules,
        {
            "mcp": mcp_package,
            "mcp.server": mcp_server_package,
            "mcp.server.fastmcp": fastmcp_module,
            "maestro_mcp_server": server,
        },
    ):
        spec.loader.exec_module(server)
    sys.modules["maestro_mcp_server"] = server
    return server.boot_emulator


def test_mcp_server_paths_do_not_shadow_dependency_package():
    plugin_manifest = json.loads((PLUGIN_ROOT / "plugin.json").read_text(encoding="utf-8"))
    codex_manifest = json.loads(
        (PLUGIN_ROOT / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8")
    )
    mcp_config = json.loads((PLUGIN_ROOT / "mcp_config.json").read_text(encoding="utf-8"))

    assert plugin_manifest["mcp_servers"]["maestro"]["args"][-1] == "./maestro_mcp/server.py"
    assert codex_manifest["mcp_servers"]["maestro"]["args"][-1] == "./maestro_mcp/server.py"
    assert mcp_config["mcpServers"]["maestro"]["args"][-1] == "maestro_mcp/server.py"
    assert SERVER_PATH.is_file()
    assert not (PLUGIN_ROOT / "mcp").exists()


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
