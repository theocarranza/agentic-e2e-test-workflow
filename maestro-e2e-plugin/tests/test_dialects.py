import unittest

from orchestrator_core.dialects import (
    build_prompt_payload,
    to_anthropic_xml,
    to_generic_cli_prompt,
    to_openai_messages,
)


class DialectTests(unittest.TestCase):
    def test_anthropic_xml_wraps_sections_without_mutating_text(self):
        result = to_anthropic_xml("Follow the manifest.", "Task payload.")

        self.assertEqual(
            result,
            "<instructions>\nFollow the manifest.\n</instructions>\n\n<payload>\nTask payload.\n</payload>",
        )

    def test_openai_messages_use_system_and_user_roles(self):
        result = to_openai_messages("Follow the manifest.", "Task payload.")

        self.assertEqual(
            result,
            [
                {"role": "system", "content": "Follow the manifest."},
                {"role": "user", "content": "Task payload."},
            ],
        )

    def test_generic_cli_prompt_is_plain_markdown(self):
        result = to_generic_cli_prompt("Follow the manifest.", "Task payload.")

        self.assertEqual(
            result,
            "## Instructions\n\nFollow the manifest.\n\n## Payload\n\nTask payload.",
        )

    def test_build_prompt_payload_dispatches_by_dialect(self):
        self.assertIsInstance(build_prompt_payload("openai", "I", "P"), list)
        self.assertIsInstance(build_prompt_payload("responses", "I", "P"), list)
        self.assertIn("<instructions>", build_prompt_payload("anthropic", "I", "P"))
        self.assertIn("<instructions>", build_prompt_payload("claude", "I", "P"))
        self.assertIn("## Instructions", build_prompt_payload("cli", "I", "P"))
        self.assertIn("## Instructions", build_prompt_payload("generic", "I", "P"))

    def test_unknown_dialect_is_rejected(self):
        with self.assertRaises(ValueError) as ctx:
            build_prompt_payload("unknown", "I", "P")

        self.assertIn("Unsupported dialect", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
