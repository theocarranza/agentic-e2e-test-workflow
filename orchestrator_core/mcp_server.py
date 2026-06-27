import sys
import json
from pathlib import Path
from typing import Dict, Any, List

def read_manifests(skills_dir: str) -> List[Dict[str, Any]]:
    """Discovers all manifest.json files in the skills directory."""
    manifests = []
    base_path = Path(skills_dir)
    if not base_path.exists():
        return manifests
        
    for skill_path in base_path.iterdir():
        if skill_path.is_dir():
            manifest_file = skill_path / "manifest.json"
            if manifest_file.exists():
                try:
                    with open(manifest_file, 'r') as f:
                        manifests.append(json.load(f))
                except Exception:
                    pass
    return manifests

def handle_list_tools(manifests: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Returns the MCP tools/list response."""
    tools = []
    for m in manifests:
        tools.append({
            "name": m.get("name"),
            "description": m.get("description"),
            "inputSchema": m.get("input_schema", {"type": "object", "properties": {}})
        })
    return {"tools": tools}

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
                "serverInfo": {"name": "agentic-orchestrator", "version": "1.0.0"}
            }
        elif method == "tools/list":
            manifests = read_manifests(skills_dir)
            response["result"] = handle_list_tools(manifests)
        elif method == "tools/call":
            # Here we interface with the OrchestratorStream
            # In a full implementation:
            # 1. Dispatch TaskSpawnedEvent to the queue
            # 2. Wait for worker output or tool execution
            # 3. Evaluate Output (Evaluator Gate)
            # 4. Return results to the host
            params = msg.get("params", {})
            name = params.get("name")
            args = params.get("arguments", {})
            
            response["result"] = {
                "content": [{"type": "text", "text": f"Queued task {name} for execution with args: {args}"}]
            }
        else:
            response["error"] = {"code": -32601, "message": "Method not found"}
            
    except Exception as e:
        response["error"] = {"code": -32603, "message": str(e)}
        
    # MCP requires responses to be a single line JSON
    return json.dumps(response)

def main():
    current_dir = Path(__file__).parent
    skills_dir = current_dir.parent.parent / "skills"
    
    # Run the JSON-RPC event loop over stdio
    for line in sys.stdin:
        if line.strip():
            res = process_message(line, str(skills_dir))
            if res:
                print(res, flush=True)

if __name__ == "__main__":
    main()
