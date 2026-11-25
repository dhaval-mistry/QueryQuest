"""AWS-only configuration using the standard AWS SDK credential chain."""
import os
import boto3
from botocore.config import Config
from botocore.exceptions import NoCredentialsError, PartialCredentialsError, ProfileNotFound
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / ".env")


class AWSConfigurationError(RuntimeError):
    """An actionable AWS setup error that is safe to show in the UI."""


def require_research_credentials() -> None:
    """Check IAM credential availability before spending tokens on planning.

    A Bedrock bearer token can authenticate inference but cannot sign an
    AgentCore Web Search request. This checks availability, not IAM permissions.
    """
    message = (
        "AWS Web Search needs IAM credentials. Your Bedrock API token alone "
        "cannot authenticate search. For an AWS project account, run "
        "'aws login --profile queryquest --region us-east-2', choose your project, "
        "and set AWS_PROFILE=queryquest in QueryQuest_AWS/.env. Alternatively, "
        "configure an existing AWS profile or set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY "
        "(plus AWS_SESSION_TOKEN for temporary credentials). Restart the app "
        "after configuration. See QueryQuest_AWS/README.md for setup."
    )
    try:
        credentials = boto3.Session().get_credentials()
    except (NoCredentialsError, PartialCredentialsError, ProfileNotFound) as error:
        raise AWSConfigurationError(message) from error
    if credentials is None:
        raise AWSConfigurationError(message)


def aws_region() -> str:
    return (os.getenv("AWS_REGION") or os.getenv("AWS_DEFAULT_REGION") or "us-east-2").strip()


def aws_client(service: str, region: str | None = None):
    return boto3.client(
        service, region_name=region or aws_region(),
        config=Config(connect_timeout=10, read_timeout=180,
                      retries={"mode": "standard", "max_attempts": 3}),
    )


def bedrock_model(role: str) -> str:
    model = (os.getenv(f"BEDROCK_{role.upper()}_MODEL") or os.getenv("BEDROCK_MODEL")
             or "us.anthropic.claude-sonnet-4-6").strip()
    if model.startswith("openai."):
        raise ValueError("Use a Bedrock Converse model ID, such as us.anthropic.claude-sonnet-4-6, instead of a GPT/Mantle model.")
    return model


def positive_int(name: str, default: int, maximum: int | None = None) -> int:
    value = int(os.getenv(name) or default)
    if value < 1 or (maximum is not None and value > maximum):
        limit = f" between 1 and {maximum}" if maximum else " at least 1"
        raise ValueError(f"{name} must be{limit}")
    return value
