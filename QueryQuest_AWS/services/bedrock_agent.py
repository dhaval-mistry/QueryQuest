"""Synchronous Bedrock agents with validated Pydantic outputs."""
from dataclasses import dataclass
import json
import logging
from typing import Generic, TypeVar
from pydantic import BaseModel, ValidationError
from config import aws_client, positive_int

Output = TypeVar("Output", bound=BaseModel)
logger = logging.getLogger(__name__)


def normalize_containers(value, schema):
    """Decode JSON strings only where the schema expects an object or array.

    Text fields are never parsed or rewritten. Pydantic still checks all values
    and required fields after this narrow transport-format repair.
    """
    expected = schema.get("type")
    if isinstance(value, str) and expected in {"array", "object"}:
        try:
            decoded = json.loads(value)
        except (ValueError, TypeError):
            return value
        if expected == "array" and isinstance(decoded, list):
            value = decoded
        elif expected == "object" and isinstance(decoded, dict):
            value = decoded
    if expected == "array" and isinstance(value, list):
        return [normalize_containers(item, schema.get("items", {})) for item in value]
    if expected == "object" and isinstance(value, dict):
        properties = schema.get("properties", {})
        return {key: normalize_containers(item, properties.get(key, {})) for key, item in value.items()}
    return value


def tool_schema(output_type: type[BaseModel]) -> dict:
    """Inline Pydantic references for Bedrock tool input schema support."""
    schema = output_type.model_json_schema()
    definitions = schema.get("$defs", {})

    def expand(value):
        if isinstance(value, list):
            return [expand(item) for item in value]
        if not isinstance(value, dict):
            return value
        if "$ref" in value:
            return expand(definitions[value["$ref"].split("/")[-1]])
        return {key: ({name: expand(field) for name, field in item.items()}
                      if key == "properties" else expand(item))
                for key, item in value.items()
                if key not in {"$defs", "title"}}

    expanded = expand(schema)
    return {key: expanded[key] for key in ("type", "properties", "required") if key in expanded}


@dataclass
class BedrockAgent(Generic[Output]):
    name: str
    instructions: str
    model: str
    output_type: type[Output]

    def run(self, prompt: str) -> Output:
        """Use a forced output tool; this schema tool executes no action."""
        client = aws_client("bedrock-runtime")
        schema = tool_schema(self.output_type)
        request = dict(
            modelId=self.model,
            system=[{"text": self.instructions + "\nReturn your result using submit_result. "
                     "Use actual JSON arrays and objects for nested fields, never JSON encoded inside strings."}],
            messages=[{"role": "user", "content": [{"text": prompt}]}],
            inferenceConfig={"maxTokens": positive_int("BEDROCK_MAX_TOKENS", 4096), "temperature": 0},
            toolConfig={
                "tools": [{"toolSpec": {
                    "name": "submit_result",
                    "description": "Submit the completed structured result.",
                    "inputSchema": {"json": schema},
                }}],
                "toolChoice": {"tool": {"name": "submit_result"}},
            },
        )
        for attempt in range(2):
            response = client.converse(**request)
            if response.get("stopReason") != "tool_use":
                raise ValueError(f"{self.name}: Bedrock did not complete structured output (stop reason: {response.get('stopReason')}).")
            calls = [block["toolUse"] for block in response["output"]["message"]["content"] if "toolUse" in block]
            if len(calls) != 1 or calls[0]["name"] != "submit_result":
                raise ValueError(f"{self.name}: Bedrock returned an unexpected structured result.")
            try:
                return self.output_type.model_validate(normalize_containers(calls[0]["input"], schema))
            except ValidationError as error:
                if attempt:
                    raise
                # Retry only this agent, using the same question/evidence. Do not
                # repeat planning or searches or include model content in logs.
                problems = [{"field": ".".join(map(str, item["loc"])), "error": item["type"]}
                            for item in error.errors(include_input=False, include_url=False)]
                logger.warning("%s returned invalid structured output; retrying once: %s", self.name, problems)
                request["messages"] = [{"role": "user", "content": [{"text": prompt +
                    "\nYour previous result failed schema validation. Correct these fields: " + json.dumps(problems) +
                    ". Return a complete result matching submit_result; preserve the supplied evidence and source IDs."}]}]
