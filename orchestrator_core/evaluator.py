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

def evaluate_maestro_flow(content: str) -> List[str]:
    critiques = []
    if "appId:" not in content:
        critiques.append("Missing 'appId:' declaration.")
    if "launch_clean" not in content and "start_authenticated_session" not in content:
        critiques.append("Missing required lifecycle subflow (launch_clean or start_authenticated_session).")
    if "extendedWaitUntil:" in content and "tapOn:" in content:
        # A rudimentary check; true AST parsing of YAML would be better
        if "visible:" in content:
            # We don't fail immediately, but this is a strict warning in the prompt.
            pass
    return critiques

def evaluate_artifact(stage_id: str, content: str) -> List[str]:
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
        return evaluate_maestro_flow(content)
    return ["Unknown stage_id for evaluation."]
