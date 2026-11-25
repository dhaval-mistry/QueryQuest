"""Manual OpenAI inference check. Makes a real API call."""
import os
from config import configure_tracing
from openai import OpenAI


def main():
    configure_tracing()
    response = OpenAI().responses.create(
        model=os.getenv("DEFAULT_MODEL_NAME", "gpt-5.4-mini"), input="Say hello.",
    )
    print(response.output_text)


if __name__ == "__main__":
    main()
