import json
import unittest
from pathlib import Path

from orchestrator_core.protocol import CliCommand, normalize_tool_call


TOOL_PATHS = {"echo_text": Path("/tmp/plugin/tools/echo_text")}


class ProtocolTests(unittest.TestCase):
    def test_normalizes_openai_function_call(self):
        native = {
            "type": "function_call",
            "name": "echo_text",
            "arguments": json.dumps({"text": "hello"}),
        }

        command = normalize_tool_call("openai", native, TOOL_PATHS)

        self.assertEqual(
            command,
            CliCommand(
                executable=Path("/tmp/plugin/tools/echo_text"),
                arguments={"text": "hello"},
            ),
        )

    def test_normalizes_anthropic_tool_use(self):
        native = {
            "type": "tool_use",
            "name": "echo_text",
            "input": {"text": "hello"},
        }

        command = normalize_tool_call("anthropic", native, TOOL_PATHS)

        self.assertEqual(
            command,
            CliCommand(
                executable=Path("/tmp/plugin/tools/echo_text"),
                arguments={"text": "hello"},
            ),
        )

    def test_rejects_unknown_tool(self):
        native = {"type": "tool_use", "name": "missing", "input": {}}

        with self.assertRaises(ValueError) as ctx:
            normalize_tool_call("anthropic", native, TOOL_PATHS)

        self.assertIn("Unknown tool", str(ctx.exception))

    def test_rejects_unknown_protocol(self):
        with self.assertRaises(ValueError) as ctx:
            normalize_tool_call("unknown", {}, TOOL_PATHS)

        self.assertIn("Unsupported protocol", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
