from typing import Dict, List, Union


PromptPayload = Union[str, List[Dict[str, str]]]


def _clean(value: str) -> str:
    return value.strip()


def to_anthropic_xml(instructions: str, payload: str) -> str:
    return (
        f"<instructions>\n{_clean(instructions)}\n</instructions>\n\n"
        f"<payload>\n{_clean(payload)}\n</payload>"
    )


def to_openai_messages(instructions: str, payload: str) -> List[Dict[str, str]]:
    return [
        {"role": "system", "content": _clean(instructions)},
        {"role": "user", "content": _clean(payload)},
    ]


def to_generic_cli_prompt(instructions: str, payload: str) -> str:
    return f"## Instructions\n\n{_clean(instructions)}\n\n## Payload\n\n{_clean(payload)}"


def build_prompt_payload(dialect: str, instructions: str, payload: str) -> PromptPayload:
    normalized = dialect.lower().strip()
    if normalized in {"anthropic", "claude"}:
        return to_anthropic_xml(instructions, payload)
    if normalized in {"openai", "responses"}:
        return to_openai_messages(instructions, payload)
    if normalized in {"cli", "generic"}:
        return to_generic_cli_prompt(instructions, payload)
    raise ValueError(f"Unsupported dialect: {dialect}")
