from typing import Dict, List


def propose_instruction_update(task_id: str, critiques: List[str]) -> Dict[str, str]:
    critique_lines = "\n".join(f"- {critique}" for critique in critiques)
    return {
        "operation": "Update",
        "requires_authorization": "IMPLEMENTATION APPROVED",
        "summary": f"Instruction update proposal for {task_id} after repeated evaluator failures.",
        "candidate_instruction": (
            f"For {task_id}, address these evaluator failures before returning an artifact:\n"
            f"{critique_lines}"
        ),
    }
