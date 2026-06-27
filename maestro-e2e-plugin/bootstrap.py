import os
import json
import shutil
import argparse
from pathlib import Path
from datetime import datetime, timezone

def register_antigravity(source_dir: Path):
    print("[*] Installing for Antigravity...")
    dest = Path.home() / ".gemini" / "config" / "plugins" / "maestro-e2e-workflow"
    if dest.exists():
        shutil.rmtree(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source_dir, dest, ignore=shutil.ignore_patterns("__pycache__", ".git"))
    print(f"    -> Installed successfully to {dest}")

def register_codex(source_dir: Path):
    print("[*] Installing for AI Codex Harness...")
    # Assuming Codex harness uses a similar plugin architecture path or global plugins folder
    dest = Path.home() / ".codex-plugins" / "maestro-e2e-workflow"
    if dest.exists():
        shutil.rmtree(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source_dir, dest, ignore=shutil.ignore_patterns("__pycache__", ".git"))
    print(f"    -> Installed successfully to {dest}")

def register_claude_plugin(source_dir: Path):
    print("[*] Installing for Claude Code...")
    manifest_path = source_dir / ".claude-plugin" / "plugin.json"
    if not manifest_path.exists():
        print("    -> [!] Could not find .claude-plugin/plugin.json")
        return

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    name = manifest.get("name", "maestro-e2e-workflow")
    version = manifest.get("version", "0.1.0")

    cache_dir = Path.home() / ".claude" / "plugins" / "cache" / "local" / name / version
    if cache_dir.exists():
        shutil.rmtree(cache_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)

    if (source_dir / "skills").is_dir():
        shutil.copytree(source_dir / "skills", cache_dir / "skills", ignore=shutil.ignore_patterns("__pycache__"))
    if (source_dir / "orchestrator_core").is_dir():
        shutil.copytree(source_dir / "orchestrator_core", cache_dir / "orchestrator_core", ignore=shutil.ignore_patterns("__pycache__"))

    clean_manifest = {k: manifest[k] for k in ("name", "description", "version", "author") if k in manifest}
    (cache_dir / "plugin.json").write_text(json.dumps(clean_manifest, indent=2), encoding="utf-8")

    registry_path = Path.home() / ".claude" / "plugins" / "installed_plugins.json"
    registry = {"version": 2, "plugins": {}}
    if registry_path.exists():
        try:
            registry = json.loads(registry_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            pass

    plugin_key = f"{name}@local"
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.") + f"{datetime.now(timezone.utc).microsecond // 1000:03d}Z"
    
    registry["plugins"][plugin_key] = [{
        "scope": "user",
        "installPath": str(cache_dir),
        "version": version,
        "installedAt": now,
        "lastUpdated": now,
    }]

    registry_path.parent.mkdir(parents=True, exist_ok=True)
    registry_path.write_text(json.dumps(registry, indent=2), encoding="utf-8")
    print(f"    -> Registered in Claude Code plugin registry at {cache_dir}")

def main():
    parser = argparse.ArgumentParser(description="Install the Maestro E2E Orchestrator plugin.")
    parser.add_argument("--target", choices=["claude", "antigravity", "codex", "all-agents"], default="all-agents", 
                        help="Target harness to wire (default: all-agents)")
    args = parser.parse_args()

    print("========================================")
    print(" Maestro E2E Orchestrator Installer")
    print(f" Target: {args.target}")
    print("========================================\n")
    source_dir = Path(__file__).parent.absolute()
    
    if args.target in ("antigravity", "all-agents"):
        register_antigravity(source_dir)
    if args.target in ("claude", "all-agents"):
        register_claude_plugin(source_dir)
    if args.target in ("codex", "all-agents"):
        register_codex(source_dir)
    
    print("\n========================================")
    print(" Installation Complete!")
    print(" Please restart your model harness to load the plugin.")
    print(" Run using: /e2e start --module <name>")

if __name__ == "__main__":
    main()
