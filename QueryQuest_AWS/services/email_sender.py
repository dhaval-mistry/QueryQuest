"""Send QueryQuest reports through Amazon SES using AWS credentials."""

import os
from email.message import EmailMessage

from config import aws_client
from email_validator import EmailNotValidError, validate_email



def normalize_email(address: str) -> str:
    """Validate recipient syntax before calling Amazon SES."""
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
    """Construct a MIME email without making a network call.

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
    """Send one report through Amazon SES, preserving HTML and plain text."""
    sender = normalize_email(os.getenv("EMAIL_ADDRESS", ""))
    recipient = normalize_email(recipient or os.getenv("EMAIL_TO") or sender)
    message = build_email_message(
        subject=subject, body=body, sender=sender,
        recipient=recipient, html_body=html_body,
    )
    aws_client("sesv2", os.getenv("AWS_SES_REGION") or None).send_email(
        FromEmailAddress=sender,
        Destination={"ToAddresses": [recipient]},
        Content={"Raw": {"Data": message.as_bytes()}},
    )
