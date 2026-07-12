import sys
import json
from pathlib import Path
from typing import Dict, Any, List

from .skill_package import list_skill_packages


def read_manifests(skills_dir: str) -> List[Dict[str, Any]]:
    return [package.manifest for package in list_skill_packages(Path(skills_dir))]


def handle_list_tools(manifests: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Returns the MCP tools/list response."""
    tools = []
    for manifest in manifests:
        tools.append({
            "name": manifest.get("name"),
            "description": manifest.get("description"),
            "inputSchema": manifest.get("input_schema", {"type": "object", "properties": {}}),
        })
    return {"tools": tools}


def _handle_tools_call(params: Dict[str, Any], skills_dir: str) -> Dict[str, Any]:
    name = params.get("name")
    args = params.get("arguments", {})
    packages = {package.name: package for package in list_skill_packages(Path(skills_dir))}
    if name not in packages:
        raise ValueError(f"Unknown tool: {name}")
    return {
        "content": [{"type": "text", "text": f"Queued task {name} for execution with args: {args}"}]
    }


def process_message(line: str, skills_dir: str) -> str:
    """Processes a single JSON-RPC message and returns the response string."""
    try:
        msg = json.loads(line)
    except json.JSONDecodeError:
        return ""

    # We only handle valid JSON-RPC requests
    if "id" not in msg or "method" not in msg:
        return ""

    msg_id = msg["id"]
    method = msg["method"]

    response = {"jsonrpc": "2.0", "id": msg_id}

    try:
        if method == "initialize":
            response["result"] = {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "agentic-orchestrator", "version": "1.0.0"},
            }
        elif method == "tools/list":
            manifests = read_manifests(skills_dir)
            response["result"] = handle_list_tools(manifests)
        elif method == "tools/call":
            response["result"] = _handle_tools_call(msg.get("params", {}), skills_dir)
        else:
            response["error"] = {"code": -32601, "message": "Method not found"}

    except ValueError as e:
        response["error"] = {"code": -32602, "message": str(e)}
    except Exception as e:
        response["error"] = {"code": -32603, "message": str(e)}

    # MCP requires responses to be a single line JSON
    return json.dumps(response)


def main():
    plugin_root = Path(__file__).resolve().parent.parent
    skills_dir = plugin_root / "skills"

    # Run the JSON-RPC event loop over stdio
    for line in sys.stdin:
        if line.strip():
            res = process_message(line, str(skills_dir))
            if res:
                print(res, flush=True)


if __name__ == "__main__":
    main()
