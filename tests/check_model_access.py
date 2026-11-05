
import os
from dotenv import load_dotenv
from openai import OpenAI, APIStatusError

# Read latest values from .env.
load_dotenv(override=True)

region = os.getenv("AWS_REGION")
model = os.getenv("BEDROCK_MODEL")
key = os.getenv("AWS_BEARER_TOKEN_BEDROCK")

if not key:
    raise ValueError("Missing AWS Bedrock API key")

# Model discovery uses /v1.
discovery = OpenAI(
    api_key=key,
    base_url=f"https://bedrock-mantle.{region}.api.aws/v1",
)

try:
    models = discovery.models.list()

    print("Model discovery successful")
    print("Requested model:", model)
    print("\nModels returned by AWS Bedrock:")
    print("-" * 50)

    for item in models.data:
        print(item.id)

    # Display how many models were returned.
    print(f"\nTotal models: {len(models.data)}")

    # Check whether our configured model appears in the list.
    model_ids = [item.id for item in models.data]

    print(f"\nSelected model: {model}")
    print(f"Model listed: {model in model_ids}")

except APIStatusError as error:
    print("Discovery error:", error.status_code)
    print(error.message)

# GPT-5.6 inference uses /openai/v1.
client = OpenAI(
    api_key=key,
    base_url=f"https://bedrock-mantle.{region}.api.aws/openai/v1",
)

try:
    response = client.responses.create(
        model=model,
        input="Say hello.",
    )

    print("Inference successful!")
    print(response.output_text)

except APIStatusError as error:
    print("Inference failed:", error.status_code)
    print(error.message)
    print("Request ID:", error.request_id)
