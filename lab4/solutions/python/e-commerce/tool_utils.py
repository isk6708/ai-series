"""Helpers shared by server.py (MCP SDK 1.x) and server_v2.py (MCP SDK 2.x)."""
import json

from pydantic import BaseModel

import tools

no_params_object = {
    "type": "object",
    "properties": {},
    "required": []
}


def pydantic_to_json(model_cls: type[BaseModel] | None) -> dict:
    """Turn a Pydantic model into the JSON Schema MCP expects for a tool's inputSchema."""
    if model_cls is None:
        return no_params_object
    schema = model_cls.model_json_schema()  # .schema() is deprecated in Pydantic v2
    properties = {}
    for prop, details in schema.get("properties", {}).items():
        properties[prop] = {"type": details.get("type", "string")}
        if "default" in details:
            properties[prop]["default"] = details["default"]
    return {
        "type": "object",
        "properties": properties,
        "required": schema.get("required", []),
    }


def to_text(result) -> str:
    """Serialise a tool result (Pydantic model, list of models, dict, str ...) to readable JSON."""
    if isinstance(result, str):
        return result

    def convert(value):
        if isinstance(value, BaseModel):
            return value.model_dump()
        if isinstance(value, list):
            return [convert(v) for v in value]
        if isinstance(value, dict):
            return {k: convert(v) for k, v in value.items()}
        return value

    return json.dumps(convert(result), indent=2)


async def run_tool(name: str, arguments: dict | None) -> str:
    if name not in tools.tools:
        raise ValueError(f"Unknown tool: {name}")
    tool = tools.tools[name]
    try:
        result = await tool["handler"](arguments or {})
    except Exception as e:
        raise ValueError(f"Error calling tool {name}: {str(e)}")
    return to_text(result)
