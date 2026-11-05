
"""
Shared configuration for QueryQuest.

This file provides:
1. AWS Bedrock model connection.
2. OpenAI Agents SDK tracing configuration.
"""

import os

from dotenv import load_dotenv

# Load environment variables before initializing the SDK.
#load_dotenv()
load_dotenv(override=True)

print("AWS Region:", os.getenv("AWS_REGION"))
print("Bedrock Model:", os.getenv("BEDROCK_MODEL"))
print("Bedrock Base URL:", os.getenv("BEDROCK_BASE_URL"))

from openai import AsyncOpenAI
from agents import OpenAIResponsesModel, set_tracing_export_api_key


def get_bedrock_model():
    """Return an AWS Bedrock model for our agents."""

    region = os.getenv("AWS_REGION", "us-east-1")
    api_key = os.getenv("AWS_BEARER_TOKEN_BEDROCK")
    model_name = os.getenv("BEDROCK_MODEL", "openai.gpt-5.6-luna")

    if not api_key:
        raise ValueError("AWS Bedrock API key is missing.")

    # Use AWS's OpenAI-compatible endpoint.
    client = AsyncOpenAI(
        api_key=api_key,
        base_url=f"https://bedrock-mantle.{region}.api.aws/v1",
    )

    return OpenAIResponsesModel(
        model=model_name,
        openai_client=client,
    )


def configure_tracing():
    """Send agent execution traces to OpenAI."""

    openai_key = os.getenv("OPENAI_API_KEY")

    if not openai_key:
        raise ValueError("OpenAI tracing API key is missing.")

    # This key uploads traces, not LLM requests.
    set_tracing_export_api_key(openai_key)
