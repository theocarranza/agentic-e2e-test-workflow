from collections.abc import Mapping


def bind_tools_for_openai(manifest):
    return [
        {
            "type": "function",
            "function": {
                "name": tool["name"],
                "description": tool["description"],
                "parameters": schema,
            },
        }
        for tool, schema in _validated_tools(manifest)
    ]


def bind_tools_for_anthropic(manifest):
    return [
        {
            "name": tool["name"],
            "description": tool["description"],
            "input_schema": schema,
        }
        for tool, schema in _validated_tools(manifest)
    ]


def _validated_tools(manifest):
    if not isinstance(manifest, Mapping):
        raise ValueError("manifest must be an object")
    tools = manifest.get("tools", [])
    if not isinstance(tools, list):
        raise ValueError("tools must be a list")

    return [(_validated_tool(tool), _tool_schema(tool)) for tool in tools]


def _validated_tool(tool):
    if not isinstance(tool, Mapping):
        raise ValueError("tool declarations must be objects")

    missing = [
        field
        for field in ("name", "description")
        if field not in tool
    ]
    if "input_schema" not in tool and "parameters" not in tool:
        missing.append("input_schema or parameters")

    if missing:
        raise ValueError(f"tool declaration missing fields: {', '.join(missing)}")

    return tool


def _tool_schema(tool):
    schema = tool.get("input_schema", tool.get("parameters"))
    if not isinstance(schema, dict):
        raise ValueError("tool schema must be a dict")

    if "type" in schema:
        if schema.get("type") != "object":
            raise ValueError("tool schema type must be object")
        if "properties" in schema and not isinstance(schema.get("properties"), dict):
            raise ValueError("tool schema properties must be a dict")
        return schema
    return {"type": "object", "properties": schema}
