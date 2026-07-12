import tempfile
import unittest
from pathlib import Path

from orchestrator_core.persistence import (
    project_state_dir,
    read_project_json,
    stable_workspace_id,
    write_project_json,
)


class PersistenceTests(unittest.TestCase):
    def test_workspace_id_is_stable_and_path_safe(self):
        first = stable_workspace_id("/tmp/My Project")
        second = stable_workspace_id("/tmp/My Project/")

        self.assertEqual(first, second)
        self.assertRegex(first, r"^[a-f0-9]{16}$")

    def test_project_state_dir_lives_under_plugin_projects(self):
        with tempfile.TemporaryDirectory() as tmp:
            plugin_root = Path(tmp) / "plugin"
            result = project_state_dir(plugin_root, "/workspace/app")

            self.assertEqual(result.parent, plugin_root / "projects")
            self.assertTrue(result.name)

    def test_write_and_read_project_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            plugin_root = Path(tmp) / "plugin"
            payload = {"queue": {"status": "Ready"}}

            path = write_project_json(plugin_root, "/workspace/app", "queue.json", payload)
            loaded = read_project_json(plugin_root, "/workspace/app", "queue.json")

            self.assertTrue(path.exists())
            self.assertEqual(loaded, payload)

    def test_missing_project_json_returns_default(self):
        with tempfile.TemporaryDirectory() as tmp:
            plugin_root = Path(tmp) / "plugin"

            loaded = read_project_json(
                plugin_root, "/workspace/app", "missing.json", default={"ok": True}
            )

            self.assertEqual(loaded, {"ok": True})


if __name__ == "__main__":
    unittest.main()
