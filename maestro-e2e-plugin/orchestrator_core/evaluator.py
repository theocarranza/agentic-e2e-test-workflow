from typing import List

def evaluate_domain(content: str) -> List[str]:
    critiques = []
    required_sections = [
        "## 1. Domain Overview",
        "## 2. Exhaustive Data Model",
        "## 3. Lifecycle and Relevant States",
        "## 4. Functional Areas and Business Logic"
    ]
    for section in required_sections:
        if section not in content:
            critiques.append(f"Missing required section: '{section}'")
    return critiques

def evaluate_test_plan(content: str) -> List[str]:
    critiques = []
    if "```gherkin" not in content.lower():
        critiques.append("Missing Gherkin code block.")
    if "Feature:" not in content and "Funcionalidade:" not in content:
        critiques.append("Missing 'Feature:' declaration.")
    if "Scenario:" not in content and "Cenário:" not in content:
        critiques.append("Missing at least one 'Scenario:'.")
    if "## Implementation Notes" not in content and "## Notas para o implementador" not in content:
        critiques.append("Missing '## Implementation Notes' section.")
    return critiques

def evaluate_blueprint(content: str) -> List[str]:
    critiques = []
    if "| Element | Widget | Type | Current Selector | Gap |" not in content and "| Elemento |" not in content:
        critiques.append("Missing the interactive elements table header.")
    if "## Consolidated Semantics to Add" not in content and "## Semantics a adicionar" not in content:
        critiques.append("Missing the Consolidated Semantics section.")
    return critiques

def evaluate_maestro_flow(content: str, file_path: str = None) -> List[str]:
    critiques = []
    if "appId:" not in content:
        critiques.append("Missing 'appId:' declaration.")
    if "launch_clean" not in content and "start_authenticated_session" not in content:
        critiques.append("Missing required lifecycle subflow (launch_clean or start_authenticated_session).")
    
    # Fail fast if static checks fail
    if critiques:
        return critiques

    # Phase 4: Execution Harness Integration
    if file_path:
        import subprocess
        try:
            print(f"[*] Running physical Maestro test harness for {file_path}...")
            # In a real environment, this invokes the test runner against the emulator.
            # E.g., `npm run test:e2e:android` or direct `maestro test`
            result = subprocess.run(
                ["maestro", "test", file_path],
                capture_output=True,
                text=True,
                timeout=120
            )
            if result.returncode != 0:
                raise Exception(f"Maestro physical execution failed:\n{result.stderr}")
        except FileNotFoundError:
            print("[!] Maestro CLI not installed. Skipping live execution gate (Dry-Run Mode).")
        except subprocess.TimeoutExpired:
            critiques.append("Test timed out after 120s. Is the emulator running and responsive?")
            
    return critiques

def evaluate_stage_4(content: str) -> List[str]:
    critiques = []
    if "Execution & Healing Report" not in content:
        critiques.append("The document must include a title 'Execution & Healing Report'.")
    if "**Status**:" not in content:
        critiques.append("The document must contain a '**Status**: [PASS | HEALED | FATAL]' field.")
    return critiques

def evaluate_artifact(stage_id: str, content: str, file_path: str = None) -> List[str]:
    """
    Evaluates the LLM generated artifact against the strict checklists for that stage.
    Returns a list of critiques (strings) if validation fails, or an empty list if successful.
    """
    if stage_id == "stage_0":
        return evaluate_domain(content)
    elif stage_id == "stage_1":
        return evaluate_test_plan(content)
    elif stage_id == "stage_2":
        return evaluate_blueprint(content)
    elif stage_id == "stage_3":
        return evaluate_maestro_flow(content, file_path)
    elif stage_id == "stage_4":
        return evaluate_stage_4(content)
    return ["Unknown stage_id for evaluation."]

if __name__ == "__main__":
    import argparse
    from pathlib import Path
    import sys
    
    parser = argparse.ArgumentParser(description="Evaluate a specific E2E artifact stage.")
    parser.add_argument("--stage", required=True, help="Stage ID (e.g., stage_3)")
    parser.add_argument("--file", required=True, help="Path to the artifact file")
    
    args = parser.parse_args()
    
    path = Path(args.file)
    if not path.exists():
        print(f"File {path} does not exist.")
        sys.exit(1)
        
    content = path.read_text(encoding="utf-8")
    
    mailbox = Path.cwd() / ".agentic" / "e2e_prompts"
    mailbox.mkdir(parents=True, exist_ok=True)
    error_log = mailbox / f"{args.stage}.error.log"
    
    try:
        critiques = evaluate_artifact(args.stage, content, str(path))
        if critiques:
            raise Exception("Quality Gate Failed:\n" + "\n".join(critiques))
            
        print(f"[+] Quality Gate Passed for {args.stage}!")
        if error_log.exists():
            error_log.unlink()
        sys.exit(0)
    except Exception as e:
        print(f"[!] Quality Gate Failed for {args.stage}!")
        print(str(e))
        error_log.write_text(str(e))
        sys.exit(1)
