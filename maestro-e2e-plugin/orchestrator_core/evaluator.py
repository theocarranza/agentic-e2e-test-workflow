import re
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

    # Execution is now strictly delegated to Stage 4 (Execution & Healing).
    # We only do static YAML validation here if needed.
            
    return critiques

def evaluate_stage_4(content: str) -> List[str]:
    critiques = []
    if "Execution & Healing Report" not in content:
        critiques.append("The document must include a title 'Execution & Healing Report'.")

    status_match = re.search(r"\*\*Status\*\*:\s*(.+)", content)
    if not status_match:
        critiques.append("The document must contain a '**Status**: [PASS | HEALED | FATAL]' field.")
        return critiques

    raw_status = status_match.group(1).strip()
    tokens = [t.strip().upper() for t in re.split(r"\|", raw_status.strip("[] ")) if t.strip()]
    if len(tokens) != 1:
        critiques.append(
            "Status must be exactly PASS or HEALED (not the template placeholder or multiple values)."
        )
        return critiques

    status = tokens[0]
    if status == "FATAL":
        critiques.append("Execution report status is FATAL; E2E must pass before stage_4 can complete.")
    elif status not in ("PASS", "HEALED"):
        critiques.append(f"Execution report status must be PASS or HEALED, got '{raw_status}'.")
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


def run_evaluate_cli(stage: str, file_path: str) -> int:
    """
    Imperative evaluate gate (F11/F10):
    PASS ⇒ clear error.log, exit 0; FAIL ⇒ write critiques to error.log, exit 1.
    """
    from pathlib import Path

    path = Path(file_path)
    if not path.exists():
        print(f"File {path} does not exist.")
        return 1

    content = path.read_text(encoding="utf-8")
    mailbox = Path.cwd() / ".agentic" / "e2e_prompts"
    mailbox.mkdir(parents=True, exist_ok=True)
    error_log = mailbox / f"{stage}.error.log"

    critiques = evaluate_artifact(stage, content, str(path))
    if critiques:
        message = "Quality Gate Failed:\n" + "\n".join(critiques)
        print(f"[!] Quality Gate Failed for {stage}!")
        print(message)
        error_log.write_text(message, encoding="utf-8")
        return 1

    print(f"[+] Quality Gate Passed for {stage}!")
    error_log.unlink(missing_ok=True)
    return 0


if __name__ == "__main__":
    import argparse
    import sys

    parser = argparse.ArgumentParser(description="Evaluate a specific E2E artifact stage.")
    parser.add_argument("--stage", required=True, help="Stage ID (e.g., stage_3)")
    parser.add_argument("--file", required=True, help="Path to the artifact file")
    args = parser.parse_args()
    sys.exit(run_evaluate_cli(args.stage, args.file))
