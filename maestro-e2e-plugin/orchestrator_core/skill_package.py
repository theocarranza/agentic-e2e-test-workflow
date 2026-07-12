import json
import os
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List


REQUIRED_MANIFEST_FIELDS = ("name", "version", "description", "outputs")


def _contained_path(base: Path, path: Path, label: str) -> Path:
    resolved_base = base.resolve()
    resolved_path = path.resolve()
    if resolved_path != resolved_base and resolved_base not in resolved_path.parents:
        raise ValueError(f"{label} escapes skill package: {path}")
    return resolved_path


@dataclass(frozen=True)
class SkillPackage:
    root: Path
    manifest: Dict[str, Any]
    instructions: str
    tool_paths: Dict[str, Path] = field(default_factory=dict)

    @property
    def name(self) -> str:
        return str(self.manifest["name"])

    @property
    def version(self) -> str:
        return str(self.manifest["version"])

    @property
    def description(self) -> str:
        return str(self.manifest["description"])

    @property
    def input_schema(self) -> Dict[str, Any]:
        if "input_schema" in self.manifest:
            return dict(self.manifest["input_schema"])
        return dict(self.manifest["inputs"])


def _read_manifest(skill_dir: Path) -> Dict[str, Any]:
    manifest_path = skill_dir / "manifest.json"
    if not manifest_path.exists():
        raise ValueError(f"Missing manifest.json: {skill_dir}")
    with manifest_path.open("r", encoding="utf-8") as handle:
        manifest = json.load(handle)
    if not isinstance(manifest, Mapping):
        raise ValueError(f"Manifest {manifest_path} must be an object")
    missing = [field for field in REQUIRED_MANIFEST_FIELDS if field not in manifest]
    if "input_schema" not in manifest and "inputs" not in manifest:
        missing.append("input_schema or inputs")
    if missing:
        raise ValueError(f"Manifest {manifest_path} missing required fields: {', '.join(missing)}")
    input_schema = manifest.get("input_schema", manifest.get("inputs"))
    if not isinstance(input_schema, dict):
        raise ValueError(f"Manifest {manifest_path} input_schema must be an object")
    return manifest


def _read_instructions(skill_dir: Path, manifest: Dict[str, Any]) -> str:
    instructions_path = _contained_path(
        skill_dir,
        skill_dir / str(manifest.get("authoritative_instructions", "instructions.md")),
        "Instructions path",
    )
    if not instructions_path.exists():
        raise ValueError(f"Missing instructions.md: {skill_dir}")
    return instructions_path.read_text(encoding="utf-8").strip()


def _discover_tools(skill_dir: Path, manifest: Dict[str, Any]) -> Dict[str, Path]:
    tools_dir = skill_dir / "tools"
    tools = manifest.get("tools", [])
    if not isinstance(tools, list):
        raise ValueError("Manifest tools must be a list")
    if not tools_dir.exists():
        if tools:
            raise ValueError(f"Missing tools directory: {tools_dir}")
        return {}
    tool_paths: Dict[str, Path] = {}
    for tool in tools:
        if not isinstance(tool, Mapping):
            raise ValueError("Each tool entry must be an object")
        name = tool.get("name")
        command = tool.get("command")
        executable = tool.get("executable")
        if not name or not (command or executable):
            raise ValueError("Each tool entry must define name and command or executable")
        path = _contained_path(
            tools_dir if command else skill_dir,
            tools_dir / str(command) if command else skill_dir / str(executable),
            "Tool path",
        )
        if not path.is_file():
            raise ValueError(f"Tool command not found: {path}")
        if not os.access(path, os.X_OK):
            raise ValueError(f"Tool command is not executable: {path}")
        tool_paths[str(name)] = path
    return tool_paths


def load_skill_package(skill_dir: Path) -> SkillPackage:
    root = Path(skill_dir)
    manifest = _read_manifest(root)
    instructions = _read_instructions(root, manifest)
    tool_paths = _discover_tools(root, manifest)
    return SkillPackage(root=root, manifest=manifest, instructions=instructions, tool_paths=tool_paths)


def list_skill_packages(skills_root: Path) -> List[SkillPackage]:
    root = Path(skills_root)
    if not root.exists():
        return []
    packages: List[SkillPackage] = []
    for child in sorted(root.iterdir()):
        if not child.is_dir():
            continue
        try:
            packages.append(load_skill_package(child))
        except ValueError:
            continue
    return packages
