"""JSON-RPC mcp_server skill discovery (distinct from FastMCP maestro_mcp tests)."""
import json
import tempfile
import unittest
from pathlib import Path

from orchestrator_core.mcp_server import process_message


def make_skill(root: Path):
    skill = root / "echo"
    skill.mkdir(parents=True)
    (skill / "manifest.json").write_text(
        json.dumps(
            {
                "name": "echo",
                "version": "1.0.0",
                "description": "Echo input text.",
                "input_schema": {
                    "type": "object",
                    "properties": {"text": {"type": "string"}},
                    "required": ["text"],
                },
                "outputs": {"type": "text"},
                "tools": [],
            }
        ),
        encoding="utf-8",
    )
    (skill / "instructions.md").write_text("Echo the input text.", encoding="utf-8")


class McpServerSkillsTests(unittest.TestCase):
    def test_tools_list_reads_universal_skill_packages(self):
        with tempfile.TemporaryDirectory() as tmp:
            skills_root = Path(tmp) / "skills"
            make_skill(skills_root)
            message = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "tools/list"})

            response = json.loads(process_message(message, str(skills_root)))

            self.assertEqual(response["result"]["tools"][0]["name"], "echo")
            self.assertEqual(
                response["result"]["tools"][0]["inputSchema"]["required"], ["text"]
            )

    def test_tools_call_returns_queued_task_response(self):
        with tempfile.TemporaryDirectory() as tmp:
            skills_root = Path(tmp) / "skills"
            make_skill(skills_root)
            message = json.dumps(
                {
                    "jsonrpc": "2.0",
                    "id": 2,
                    "method": "tools/call",
                    "params": {"name": "echo", "arguments": {"text": "hello"}},
                }
            )

            response = json.loads(process_message(message, str(skills_root)))

            self.assertEqual(response["id"], 2)
            self.assertIn(
                "Queued task echo", response["result"]["content"][0]["text"]
            )

    def test_tools_call_rejects_unknown_skill(self):
        with tempfile.TemporaryDirectory() as tmp:
            message = json.dumps(
                {
                    "jsonrpc": "2.0",
                    "id": 3,
                    "method": "tools/call",
                    "params": {"name": "missing", "arguments": {}},
                }
            )

            response = json.loads(process_message(message, tmp))

            self.assertEqual(response["error"]["code"], -32602)
            self.assertIn("Unknown tool", response["error"]["message"])


if __name__ == "__main__":
    unittest.main()
