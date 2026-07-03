import sys
import unittest
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parent.parent / "maestro-e2e-plugin"
sys.path.insert(0, str(PLUGIN_ROOT))

from orchestrator_core.adapters import build_stage_context, get_stage_prompt_file
from orchestrator_core.state import WorkflowTarget


class TestStagePromptMapping(unittest.TestCase):
    def setUp(self) -> None:
        self.prompts_dir = PLUGIN_ROOT / "orchestrator_core" / "prompts"
        self.target = WorkflowTarget(module="attendance", flow="archive-student")

    def test_stage_4_prompt_file_resolves(self) -> None:
        path = get_stage_prompt_file("stage_4", self.prompts_dir)
        self.assertTrue(path.is_file(), f"expected prompt file at {path}")
        self.assertEqual(path.name, "4-execution-and-healing.prompt.md")

    def test_build_stage_context_includes_stage_4_inputs(self) -> None:
        prompt = build_stage_context(
            self.target,
            "stage_4",
            "novo",
            self.prompts_dir,
            workspace_dir="e2e_test",
        )
        self.assertIn("<system_instructions>", prompt)
        self.assertIn("Executable Verification & Self-Healing", prompt)
        self.assertIn("--- INPUT: MAESTRO FLOW (*.flow.yaml) ---", prompt)


if __name__ == "__main__":
    unittest.main()
