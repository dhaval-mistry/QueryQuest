"""Send QueryQuest articles through Gmail SMTP.

This is a normal Python service, not an LLM agent.
The recipient argument is optional for backward compatibility with the
existing `send_email(subject, body)` tests.
"""

import os
import smtplib
import ssl
from email.message import EmailMessage

from dotenv import load_dotenv
from email_validator import EmailNotValidError, validate_email

load_dotenv(override=True)


def normalize_email(address: str) -> str:
    """Validate and normalize a user-entered recipient email address."""
    try:
        # Do not perform a DNS lookup here. We just check email syntax.
        return validate_email(
            (address or "").strip(), check_deliverability=False
        ).normalized
    except EmailNotValidError as error:
        raise ValueError("Enter a valid email address.") from error


def send_email(subject: str, body: str, recipient: str | None = None) -> None:
    """Send text to one recipient using the Gmail address in .env.

    When recipient is omitted, use EMAIL_TO (or EMAIL_ADDRESS).
    This preserves the behavior of the earlier local email test.
    """
    sender = os.getenv("EMAIL_ADDRESS", "").strip()
    password = os.getenv("EMAIL_APP_PASSWORD", "").replace(" ", "")
    server = os.getenv("EMAIL_SMTP_SERVER", "smtp.gmail.com").strip()
    recipient = normalize_email(
        recipient or os.getenv("EMAIL_TO") or sender
    )

    if not sender or not password:
        raise ValueError("Missing EMAIL_ADDRESS or EMAIL_APP_PASSWORD in .env")

    # Construct a real MIME email, rather than joining headers by hand.
    message = EmailMessage()
    message["From"] = sender
    message["To"] = recipient
    message["Subject"] = subject
    message.set_content(body)

    # Gmail accepts SMTP submission with STARTTLS on port 587.
    with smtplib.SMTP(server, 587, timeout=30) as smtp:
        smtp.ehlo()
        smtp.starttls(context=ssl.create_default_context())
        smtp.ehlo()
        smtp.login(sender, password)
        smtp.send_message(message)
