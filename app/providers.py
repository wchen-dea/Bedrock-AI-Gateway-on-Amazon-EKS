import json
from typing import Protocol
from urllib.request import Request, urlopen

import boto3

from .config import settings

class FMProvider(Protocol):
    def converse(self, messages: list[dict]) -> str: ...

class MockProvider:
    def converse(self, messages: list[dict]) -> str:
        latest = messages[-1]["content"] if messages else ""
        return f"Mock response: {latest}"

class BedrockProvider:
    def __init__(self) -> None:
        if not settings.bedrock_model_id:
            raise ValueError("BEDROCK_MODEL_ID is required when AI_PROVIDER=bedrock")
        self.client = boto3.client("bedrock-runtime", region_name=settings.aws_region)

    def converse(self, messages: list[dict]) -> str:
        response = self.client.converse(
            modelId=settings.bedrock_model_id,
            messages=[{"role": m["role"], "content": [{"text": m["content"]}]} for m in messages],
            inferenceConfig={"maxTokens": 1024, "temperature": 0.2},
        )
        return response["output"]["message"]["content"][0]["text"]


class OllamaProvider:
    def converse(self, messages: list[dict]) -> str:
        request = Request(
            f"{settings.ollama_base_url.rstrip('/')}/api/chat",
            data=json.dumps(
                {
                    "model": settings.ollama_model,
                    "messages": messages,
                    "stream": False,
                }
            ).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urlopen(request, timeout=120) as response:
            payload = json.load(response)
        return payload["message"]["content"]


class DatabricksProvider:
    def __init__(self) -> None:
        missing = [
            name
            for name, value in (
                ("DATABRICKS_HOST", settings.databricks_host),
                ("DATABRICKS_TOKEN", settings.databricks_token),
                ("DATABRICKS_ENDPOINT", settings.databricks_endpoint),
            )
            if not value
        ]
        if missing:
            raise ValueError(f"{', '.join(missing)} required when AI_PROVIDER=databricks")

    def converse(self, messages: list[dict]) -> str:
        request = Request(
            f"{settings.databricks_host.rstrip('/')}/serving-endpoints/"
            f"{settings.databricks_endpoint}/invocations",
            data=json.dumps({"messages": messages}).encode(),
            headers={
                "Authorization": f"Bearer {settings.databricks_token}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        with urlopen(request, timeout=120) as response:
            payload = json.load(response)
        return payload["choices"][0]["message"]["content"]


def provider() -> FMProvider:
    selected = settings.ai_provider.lower()
    if selected == "bedrock":
        return BedrockProvider()
    if selected == "ollama":
        return OllamaProvider()
    if selected == "databricks":
        return DatabricksProvider()
    return MockProvider()
