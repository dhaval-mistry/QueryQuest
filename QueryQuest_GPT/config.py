"""Configuration for the preserved OpenAI/GPT project."""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / ".env")


def configure_tracing():
    """Respect the local setting; tracing defaults to disabled."""
    from agents import set_tracing_disabled
    disabled = os.getenv("OPENAI_AGENTS_TRACING_DISABLED", "true").lower() in {"true", "1", "yes"}
    set_tracing_disabled(disabled)
