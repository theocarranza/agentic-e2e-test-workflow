import subprocess
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("maestro")

@mcp.tool()
def boot_emulator(workspace_root: str) -> str:
    """
    Ensures the Android emulator is running and ready.
    """
    try:
        result = subprocess.run(
            ["bash", "e2e_test/scripts/e2e/lib-emulator.sh"],
            cwd=workspace_root,
            capture_output=True,
            text=True,
            check=False
        )
        return "Emulator is ready."
    except Exception as e:
        return f"Failed to boot emulator: {str(e)}"

@mcp.tool()
def run_maestro_flow(workspace_root: str, flow_filter: str = "") -> str:
    """
    Executes the Maestro E2E test suite using the project's run-e2e.sh script.
    
    Args:
        workspace_root: Absolute path to the project root (e.g. /home/.../seu_mei_simples)
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
            check=False
        )
        output = f"EXIT CODE: {result.returncode}\n\nSTDOUT:\n{result.stdout}\n\nSTDERR:\n{result.stderr}"
        return output
    except Exception as e:
        return f"Failed to execute E2E test script: {str(e)}"

@mcp.tool()
def dump_ui_hierarchy(workspace_root: str) -> str:
    """
    Captures the current UI hierarchy from the active emulator using Maestro.
    Useful for diagnosing why a test failed to find a specific element.
    """
    try:
        # Assuming maestro is in PATH or we can use the vendored one
        maestro_bin = f"{workspace_root}/e2e_test/.dart_tool/maestro/maestro/bin/maestro"
        result = subprocess.run(
            [maestro_bin, "hierarchy"],
            cwd=workspace_root,
            capture_output=True,
            text=True,
            check=False
        )
        return result.stdout if result.stdout else result.stderr
    except Exception as e:
        return f"Failed to dump hierarchy: {str(e)}"

if __name__ == "__main__":
    mcp.run_stdio()
