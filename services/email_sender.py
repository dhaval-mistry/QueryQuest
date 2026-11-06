"""Send QueryQuest reports with Gmail SMTP, including formatted HTML.

This is a regular Python utility, not an AI agent.

For compatibility with your existing tests, send_email(subject, body) still
works. Passing html_body=... adds a professional HTML version while retaining
the original plain-text message for email readers that need it.
"""

import os
import smtplib
import ssl
from email.message import EmailMessage

from dotenv import load_dotenv
from email_validator import EmailNotValidError, validate_email

load_dotenv(override=True)


def normalize_email(address: str) -> str:
    """Validate recipient syntax before connecting to SMTP."""
    try:
        return validate_email(
            (address or "").strip(), check_deliverability=False
        ).normalized
    except EmailNotValidError as error:
        raise ValueError("Enter a valid email address.") from error


def build_email_message(
    subject: str,
    body: str,
    sender: str,
    recipient: str,
    html_body: str | None = None,
) -> EmailMessage:
    """Construct a MIME email without making an SMTP network call.

    Keeping construction separate makes it easy to unit test the email body.
    Email clients can choose HTML or plain text as appropriate.
    """
    message = EmailMessage()
    message["From"] = sender
    message["To"] = recipient
    message["Subject"] = subject

    # Keep the plain-text fallback as the first MIME alternative.
    message.set_content(body)

    if html_body:
        # This is the supported multipart/alternative format in Python.
        # The HTML comes from our escaped article renderer, not raw LLM HTML.
        message.add_alternative(html_body, subtype="html")

    return message


def send_email(
    subject: str,
    body: str,
    recipient: str | None = None,
    html_body: str | None = None,
) -> None:
    """Send one report through Gmail SMTP using an App Password.

    The new html_body argument is optional. Older calls still work.
    """
    sender = os.getenv("EMAIL_ADDRESS", "").strip()
    password = os.getenv("EMAIL_APP_PASSWORD", "").replace(" ", "")
    server = os.getenv("EMAIL_SMTP_SERVER", "smtp.gmail.com").strip()
    recipient = normalize_email(recipient or os.getenv("EMAIL_TO") or sender)

    if not sender or not password:
        raise ValueError("Missing EMAIL_ADDRESS or EMAIL_APP_PASSWORD in .env")

    message = build_email_message(
        subject=subject,
        body=body,
        sender=sender,
        recipient=recipient,
        html_body=html_body,
    )

    # Gmail SMTP supports port 587 with TLS started before authentication.
    with smtplib.SMTP(server, 587, timeout=30) as smtp:
        smtp.ehlo()
        smtp.starttls(context=ssl.create_default_context())
        smtp.ehlo()
        smtp.login(sender, password)
        smtp.send_message(message)
