"""Manual Bedrock access check. This invokes a model and may incur charges."""
from config import aws_client, bedrock_model


def main():
    model = bedrock_model("planner")
    response = aws_client("bedrock-runtime").converse(
        modelId=model,
        messages=[{"role": "user", "content": [{"text": "Say hello."}]}],
        inferenceConfig={"maxTokens": 32},
    )
    print("Bedrock inference successful:", model)
    for block in response["output"]["message"]["content"]:
        if "text" in block:
            print(block["text"])


if __name__ == "__main__":
    main()
