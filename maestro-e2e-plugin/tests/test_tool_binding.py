import unittest

from orchestrator_core.tool_binding import bind_tools_for_anthropic, bind_tools_for_openai


MANIFEST = {
    "name": "echo",
    "version": "1.0.0",
    "description": "Echo input text.",
    "input_schema": {"type": "object", "properties": {}},
    "outputs": {"type": "text"},
    "tools": [
        {
            "name": "echo_text",
            "description": "Echo text through CLI.",
            "input_schema": {
                "type": "object",
                "properties": {"text": {"type": "string"}},
                "required": ["text"],
            },
        }
    ],
}


REFERENCE_SHAPED_MANIFEST = {
    **MANIFEST,
    "tools": [
        {
            "name": "echo_text",
            "description": "Echo text through CLI.",
            "parameters": {"text": {"type": "string"}},
        }
    ],
}


class ToolBindingTests(unittest.TestCase):
    def test_bind_tools_for_openai_maps_input_schema_to_function_parameters(self):
        result = bind_tools_for_openai(MANIFEST)

        self.assertEqual(
            result,
            [
                {
                    "type": "function",
                    "function": {
                        "name": "echo_text",
                        "description": "Echo text through CLI.",
                        "parameters": MANIFEST["tools"][0]["input_schema"],
                    },
                }
            ],
        )

    def test_bind_tools_for_anthropic_maps_input_schema_to_anthropic_tool_shape(self):
        result = bind_tools_for_anthropic(MANIFEST)

        self.assertEqual(
            result,
            [
                {
                    "name": "echo_text",
                    "description": "Echo text through CLI.",
                    "input_schema": MANIFEST["tools"][0]["input_schema"],
                }
            ],
        )

    def test_missing_required_tool_schema_raises_value_error(self):
        manifest = {
            **MANIFEST,
            "tools": [{"name": "echo_text", "description": "Echo text through CLI."}],
        }

        with self.assertRaises(ValueError) as ctx:
            bind_tools_for_openai(manifest)

        self.assertIn("missing fields", str(ctx.exception))

    def test_reference_shaped_parameters_bind_for_openai_and_anthropic(self):
        schema = {"type": "object", "properties": {"text": {"type": "string"}}}

        self.assertEqual(
            bind_tools_for_openai(REFERENCE_SHAPED_MANIFEST),
            [
                {
                    "type": "function",
                    "function": {
                        "name": "echo_text",
                        "description": "Echo text through CLI.",
                        "parameters": schema,
                    },
                }
            ],
        )
        self.assertEqual(
            bind_tools_for_anthropic(REFERENCE_SHAPED_MANIFEST),
            [
                {
                    "name": "echo_text",
                    "description": "Echo text through CLI.",
                    "input_schema": schema,
                }
            ],
        )

    def test_non_object_manifest_raises_value_error(self):
        with self.assertRaises(ValueError) as ctx:
            bind_tools_for_openai(True)

        self.assertIn("manifest", str(ctx.exception))

    def test_minimal_object_schema_is_preserved(self):
        manifest = {
            **MANIFEST,
            "tools": [
                {
                    "name": "empty_object",
                    "description": "Accepts any object.",
                    "input_schema": {"type": "object"},
                }
            ],
        }

        self.assertEqual(
            bind_tools_for_openai(manifest)[0]["function"]["parameters"],
            {"type": "object"},
        )

    def test_malformed_object_schema_properties_raise_value_error(self):
        manifest = {
            **MANIFEST,
            "tools": [
                {
                    "name": "bad_schema",
                    "description": "Has malformed properties.",
                    "input_schema": {"type": "object", "properties": []},
                }
            ],
        }

        with self.assertRaises(ValueError) as ctx:
            bind_tools_for_openai(manifest)

        self.assertIn("properties", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
