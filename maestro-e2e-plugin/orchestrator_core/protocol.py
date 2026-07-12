import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict


@dataclass(frozen=True)
class CliCommand:
    executable: Path
    arguments: Dict[str, Any]


def _tool_path(name: str, tool_paths: Dict[str, Path]) -> Path:
    if name not in tool_paths:
        raise ValueError(f"Unknown tool: {name}")
    return tool_paths[name]


def _openai_arguments(native_call: Dict[str, Any]) -> Dict[str, Any]:
    raw_arguments = native_call.get("arguments", "{}")
    if isinstance(raw_arguments, str):
        parsed = json.loads(raw_arguments)
    else:
        parsed = raw_arguments
    if not isinstance(parsed, dict):
        raise ValueError("OpenAI function arguments must decode to an object")
    return parsed


def _anthropic_arguments(native_call: Dict[str, Any]) -> Dict[str, Any]:
    parsed = native_call.get("input", {})
    if not isinstance(parsed, dict):
        raise ValueError("Anthropic tool input must be an object")
    return parsed


def normalize_tool_call(
    protocol: str, native_call: Dict[str, Any], tool_paths: Dict[str, Path]
) -> CliCommand:
    normalized = protocol.lower().strip()
    if normalized in {"openai", "responses"}:
        name = str(native_call.get("name", ""))
        return CliCommand(
            executable=_tool_path(name, tool_paths),
            arguments=_openai_arguments(native_call),
        )
    if normalized in {"anthropic", "claude"}:
        name = str(native_call.get("name", ""))
        return CliCommand(
            executable=_tool_path(name, tool_paths),
            arguments=_anthropic_arguments(native_call),
        )
    raise ValueError(f"Unsupported protocol: {protocol}")
