import hashlib
import json
from pathlib import Path
from typing import Any


def stable_workspace_id(workspace_root: str) -> str:
    normalized = str(Path(workspace_root).expanduser().resolve(strict=False))
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:16]


def project_state_dir(plugin_root: Path, workspace_root: str) -> Path:
    return Path(plugin_root) / "projects" / stable_workspace_id(workspace_root)


def write_project_json(
    plugin_root: Path, workspace_root: str, filename: str, payload: Any
) -> Path:
    state_dir = project_state_dir(plugin_root, workspace_root)
    state_dir.mkdir(parents=True, exist_ok=True)
    path = state_dir / filename
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def read_project_json(
    plugin_root: Path, workspace_root: str, filename: str, default: Any = None
) -> Any:
    path = project_state_dir(plugin_root, workspace_root) / filename
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))
