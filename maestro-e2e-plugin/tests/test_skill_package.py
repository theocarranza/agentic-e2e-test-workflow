import json
import stat
import tempfile
import unittest
from pathlib import Path

from orchestrator_core.skill_package import SkillPackage, load_skill_package, list_skill_packages


class SkillPackageTests(unittest.TestCase):
    def test_loads_manifest_instructions_and_executable_tools(self):
        with tempfile.TemporaryDirectory() as tmp:
            skill_dir = Path(tmp) / "echo_skill"
            tools_dir = skill_dir / "tools"
            tools_dir.mkdir(parents=True)
            (skill_dir / "manifest.json").write_text(
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
                        "tools": [
                            {
                                "name": "echo_text",
                                "description": "Echo text through CLI.",
                                "command": "echo_text",
                                "input_schema": {
                                    "type": "object",
                                    "properties": {"text": {"type": "string"}},
                                    "required": ["text"],
                                },
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            (skill_dir / "instructions.md").write_text("Return the input text.", encoding="utf-8")
            tool = tools_dir / "echo_text"
            tool.write_text("#!/usr/bin/env bash\nprintf '%s\\n' \"$1\"\n", encoding="utf-8")
            tool.chmod(tool.stat().st_mode | stat.S_IXUSR)

            package = load_skill_package(skill_dir)

            self.assertIsInstance(package, SkillPackage)
            self.assertEqual(package.name, "echo")
            self.assertEqual(package.version, "1.0.0")
            self.assertEqual(package.instructions, "Return the input text.")
            self.assertEqual(package.tool_paths["echo_text"], tool)

    def test_rejects_missing_required_manifest_fields(self):
        with tempfile.TemporaryDirectory() as tmp:
            skill_dir = Path(tmp) / "bad_skill"
            skill_dir.mkdir()
            (skill_dir / "manifest.json").write_text('{"name": "bad"}', encoding="utf-8")
            (skill_dir / "instructions.md").write_text("Do work.", encoding="utf-8")

            with self.assertRaises(ValueError) as ctx:
                load_skill_package(skill_dir)

            self.assertIn("version", str(ctx.exception))
            self.assertIn("input_schema", str(ctx.exception))

    def test_rejects_declared_tool_when_tools_directory_is_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            skill_dir = Path(tmp) / "bad_tool_skill"
            skill_dir.mkdir()
            (skill_dir / "manifest.json").write_text(
                json.dumps(
                    {
                        "name": "bad-tool",
                        "version": "1.0.0",
                        "description": "Declares a missing tool.",
                        "input_schema": {"type": "object", "properties": {}},
                        "outputs": {"type": "text"},
                        "tools": [{"name": "missing_tool", "command": "missing_tool"}],
                    }
                ),
                encoding="utf-8",
            )
            (skill_dir / "instructions.md").write_text("Use the missing tool.", encoding="utf-8")

            with self.assertRaises(ValueError) as ctx:
                load_skill_package(skill_dir)

            self.assertIn("tools", str(ctx.exception))

    def test_loads_reference_shaped_manifest(self):
        with tempfile.TemporaryDirectory() as tmp:
            skill_dir = Path(tmp) / "dart_ast_refactor"
            tools_dir = skill_dir / "tools"
            tools_dir.mkdir(parents=True)
            (skill_dir / "manifest.json").write_text(
                json.dumps(
                    {
                        "name": "dart-ast-refactor",
                        "version": "1.0.0",
                        "description": "Analyzes Dart source code.",
                        "inputs": {
                            "target_file": {"type": "string"},
                            "goal": {"type": "string"},
                        },
                        "outputs": {"type": "object"},
                        "tools": [
                            {
                                "name": "ast_parser",
                                "executable": "tools/ast_parser.sh",
                                "description": "Parses Dart files.",
                            }
                        ],
                        "authoritative_instructions": "reference_instructions.md",
                    }
                ),
                encoding="utf-8",
            )
            (skill_dir / "reference_instructions.md").write_text("Use the AST parser.", encoding="utf-8")
            executable = tools_dir / "ast_parser.sh"
            executable.write_text("#!/usr/bin/env bash\nprintf '%s\\n' \"$1\"\n", encoding="utf-8")
            executable.chmod(executable.stat().st_mode | stat.S_IXUSR)

            package = load_skill_package(skill_dir)

            self.assertEqual(package.input_schema, {"target_file": {"type": "string"}, "goal": {"type": "string"}})
            self.assertEqual(package.instructions, "Use the AST parser.")
            self.assertEqual(package.tool_paths["ast_parser"], executable)

    def test_lists_only_valid_skill_packages(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            valid = root / "valid"
            invalid = root / "invalid"
            valid.mkdir()
            invalid.mkdir()
            (valid / "manifest.json").write_text(
                json.dumps(
                    {
                        "name": "valid",
                        "version": "1.0.0",
                        "description": "Valid skill.",
                        "input_schema": {"type": "object", "properties": {}},
                        "outputs": {"type": "text"},
                    }
                ),
                encoding="utf-8",
            )
            (valid / "instructions.md").write_text("Do valid work.", encoding="utf-8")
            (invalid / "manifest.json").write_text('{"name": "invalid"}', encoding="utf-8")

            packages = list_skill_packages(root)

            self.assertEqual([package.name for package in packages], ["valid"])

    def test_malformed_tool_declarations_do_not_break_package_discovery(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            valid = root / "valid"
            invalid = root / "invalid"
            valid.mkdir()
            invalid.mkdir()
            (invalid / "tools").mkdir()
            (valid / "manifest.json").write_text(
                json.dumps(
                    {
                        "name": "valid",
                        "version": "1.0.0",
                        "description": "Valid skill.",
                        "input_schema": {"type": "object", "properties": {}},
                        "outputs": {"type": "text"},
                    }
                ),
                encoding="utf-8",
            )
            (valid / "instructions.md").write_text("Do valid work.", encoding="utf-8")
            (invalid / "manifest.json").write_text(
                json.dumps(
                    {
                        "name": "invalid",
                        "version": "1.0.0",
                        "description": "Malformed tool declarations.",
                        "input_schema": {"type": "object", "properties": {}},
                        "outputs": {"type": "text"},
                        "tools": ["bad"],
                    }
                ),
                encoding="utf-8",
            )
            (invalid / "instructions.md").write_text("Do invalid work.", encoding="utf-8")

            packages = list_skill_packages(root)

            self.assertEqual([package.name for package in packages], ["valid"])

    def test_non_object_manifest_does_not_break_package_discovery(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            valid = root / "valid"
            invalid = root / "invalid"
            valid.mkdir()
            invalid.mkdir()
            (valid / "manifest.json").write_text(
                json.dumps(
                    {
                        "name": "valid",
                        "version": "1.0.0",
                        "description": "Valid skill.",
                        "input_schema": {"type": "object", "properties": {}},
                        "outputs": {"type": "text"},
                    }
                ),
                encoding="utf-8",
            )
            (valid / "instructions.md").write_text("Do valid work.", encoding="utf-8")
            (invalid / "manifest.json").write_text("true", encoding="utf-8")
            (invalid / "instructions.md").write_text("Do invalid work.", encoding="utf-8")

            packages = list_skill_packages(root)

            self.assertEqual([package.name for package in packages], ["valid"])

    def test_rejects_instruction_path_outside_skill_package(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            skill_dir = root / "escaping_instructions"
            skill_dir.mkdir()
            (root / "outside.md").write_text("Do outside work.", encoding="utf-8")
            (skill_dir / "manifest.json").write_text(
                json.dumps(
                    {
                        "name": "escaping-instructions",
                        "version": "1.0.0",
                        "description": "Escapes instruction path.",
                        "input_schema": {"type": "object", "properties": {}},
                        "outputs": {"type": "text"},
                        "authoritative_instructions": "../outside.md",
                    }
                ),
                encoding="utf-8",
            )

            with self.assertRaises(ValueError) as ctx:
                load_skill_package(skill_dir)

            self.assertIn("escapes", str(ctx.exception))

    def test_rejects_tool_path_outside_allowed_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            skill_dir = root / "escaping_tool"
            tools_dir = skill_dir / "tools"
            tools_dir.mkdir(parents=True)
            outside = root / "outside_tool"
            outside.write_text("#!/usr/bin/env bash\n", encoding="utf-8")
            outside.chmod(outside.stat().st_mode | stat.S_IXUSR)
            (skill_dir / "manifest.json").write_text(
                json.dumps(
                    {
                        "name": "escaping-tool",
                        "version": "1.0.0",
                        "description": "Escapes tool path.",
                        "input_schema": {"type": "object", "properties": {}},
                        "outputs": {"type": "text"},
                        "tools": [{"name": "outside_tool", "command": "../outside_tool"}],
                    }
                ),
                encoding="utf-8",
            )
            (skill_dir / "instructions.md").write_text("Use the tool.", encoding="utf-8")

            with self.assertRaises(ValueError) as ctx:
                load_skill_package(skill_dir)

            self.assertIn("escapes", str(ctx.exception))

    def test_rejects_non_executable_tool_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            skill_dir = Path(tmp) / "non_executable_tool"
            tools_dir = skill_dir / "tools"
            tools_dir.mkdir(parents=True)
            tool = tools_dir / "plain_file"
            tool.write_text("not executable", encoding="utf-8")
            tool.chmod(tool.stat().st_mode & ~stat.S_IXUSR & ~stat.S_IXGRP & ~stat.S_IXOTH)
            (skill_dir / "manifest.json").write_text(
                json.dumps(
                    {
                        "name": "non-executable-tool",
                        "version": "1.0.0",
                        "description": "Declares a non-executable tool.",
                        "input_schema": {"type": "object", "properties": {}},
                        "outputs": {"type": "text"},
                        "tools": [{"name": "plain_file", "command": "plain_file"}],
                    }
                ),
                encoding="utf-8",
            )
            (skill_dir / "instructions.md").write_text("Use the tool.", encoding="utf-8")

            with self.assertRaises(ValueError) as ctx:
                load_skill_package(skill_dir)

            self.assertIn("executable", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
