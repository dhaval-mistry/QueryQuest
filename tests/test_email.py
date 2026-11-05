
### Test Gmail before running the agents

"""
Test QueryQuest Gmail SMTP independently.

Run:
    uv run python -m tests.test_email

This test sends one real email to EMAIL_TO.
"""

from services.email_sender import send_email


def main():

    # Use a small test message before sending articles.
    send_email(
        subject="QueryQuest - Email Test",
        body=(
            "Hello!\n\n"
            "QueryQuest Gmail SMTP is working.\n\n"
            "Powered by Dhaval Mistry | Mahantai"
        )
    )


if __name__ == "__main__":
    main()
