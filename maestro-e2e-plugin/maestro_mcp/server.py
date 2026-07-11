import subprocess
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("maestro")


def _format_subprocess_failure(
    result: subprocess.CompletedProcess[str], action: str
) -> str:
    detail = (result.stderr or result.stdout or "unknown error").strip()
    return f"Failed to {action} (exit {result.returncode}): {detail}"


@mcp.tool()
def boot_emulator(workspace_root: str) -> str:
    """Ensure the Android emulator is running and ready."""
    try:
        result = subprocess.run(
            ["bash", "e2e_test/scripts/e2e/boot-emulator.sh"],
            cwd=workspace_root,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            return _format_subprocess_failure(result, "boot emulator")
        return "Emulator is ready."
    except Exception as exc:
        return f"Failed to boot emulator: {exc}"


@mcp.tool()
def run_maestro_flow(workspace_root: str, flow_filter: str = "") -> str:
    """
    Execute the Maestro E2E test suite using the project's run-e2e.sh script.

    Args:
        workspace_root: Absolute path to the project root.
        flow_filter: Optional path to a specific flow file to run.
    """
    cmd = ["bash", "e2e_test/scripts/e2e/run-e2e.sh"]
    env = None
    if flow_filter:
        import os

        env = os.environ.copy()
        env["FLOW_FILTER"] = flow_filter

    try:
        result = subprocess.run(
            cmd,
            cwd=workspace_root,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        return (
            f"EXIT CODE: {result.returncode}\n\n"
            f"STDOUT:\n{result.stdout}\n\n"
            f"STDERR:\n{result.stderr}"
        )
    except Exception as exc:
        return f"Failed to execute E2E test script: {exc}"


@mcp.tool()
def dump_ui_hierarchy(workspace_root: str) -> str:
    """Capture the current UI hierarchy from the active emulator."""
    try:
        maestro_bin = (
            f"{workspace_root}/e2e_test/.dart_tool/maestro/maestro/bin/maestro"
        )
        result = subprocess.run(
            [maestro_bin, "hierarchy"],
            cwd=workspace_root,
            capture_output=True,
            text=True,
            check=False,
        )
        return result.stdout if result.stdout else result.stderr
    except Exception as exc:
        return f"Failed to dump hierarchy: {exc}"


if __name__ == "__main__":
    mcp.run_stdio()
