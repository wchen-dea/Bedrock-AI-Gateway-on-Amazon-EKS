from typing import Protocol
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

def provider() -> FMProvider:
    return BedrockProvider() if settings.ai_provider.lower() == "bedrock" else MockProvider()
