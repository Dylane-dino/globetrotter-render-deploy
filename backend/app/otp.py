"""Short-lived OTP state and optional SMTP delivery for local development."""
import os
import secrets
import smtplib
import socket
from html import escape
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage
from email.utils import formataddr

from fastapi import HTTPException

_codes: dict[str, tuple[str, datetime]] = {}

# Force DNS resolution to IPv4 (AF_INET) to prevent Errno 101 on Render,
# whose network runner does not route outbound IPv6 SMTP connections.
_orig_getaddrinfo = socket.getaddrinfo


def _getaddrinfo_ipv4(*args, **kwargs):
    responses = _orig_getaddrinfo(*args, **kwargs)
    return [response for response in responses if response[0] == socket.AF_INET]


socket.getaddrinfo = _getaddrinfo_ipv4


def issue(email: str) -> str:
    """Create a short-lived verification code without performing network I/O."""
    code = f"{secrets.randbelow(1_000_000):06d}"
    _codes[email.lower()] = (code, datetime.now(timezone.utc) + timedelta(minutes=5))
    return code


def send_otp_email(email: str, code: str, name: str | None = None) -> None:
    """Deliver an OTP email without allowing SMTP failures to affect requests."""
    host = os.environ.get("SMTP_HOST")
    if not host:
        # Development fallback: does not expose a code in API responses.
        print(f"[GlobeTrotter DEV OTP] {email}: {code}")
        return

    try:
        message = EmailMessage()
        smtp_from = os.environ.get("SMTP_FROM", "no-reply@globetrotter.local")
        greeting_name = name.strip() if name and name.strip() else "there"
        html_greeting_name = escape(greeting_name)
        message["Subject"] = "Verify your account"
        message["From"] = formataddr(("GlobalTrotter", smtp_from))
        message["To"] = email
        message.set_content(
            f"Verify your account\n\nHi {greeting_name},\n\n"
            f"Your code is:\n\n{code}\n\nThis code expires in 5 minutes."
        )
        message.add_alternative(
            f"""<!doctype html>
<html lang=\"en\">
  <body style=\"margin:0;font-family:Arial,sans-serif;color:#1f2937;\">
    <main style=\"max-width:520px;margin:0 auto;padding:32px 24px;\">
      <h1 style=\"margin:0 0 24px;font-size:24px;\">Verify your account</h1>
      <p>Hi {html_greeting_name},</p>
      <p>Your code is:</p>
      <p style=\"margin:24px 0;font-size:32px;font-weight:700;letter-spacing:2px;\">{code}</p>
      <p style=\"color:#6b7280;font-size:14px;\">This code expires in 5 minutes.</p>
    </main>
  </body>
</html>""",
            subtype="html",
        )
        with smtplib.SMTP(host, int(os.environ.get("SMTP_PORT", "587")), timeout=10) as client:
            if os.environ.get("SMTP_TLS", "true").lower() == "true":
                client.starttls()
            username, password = os.environ.get("SMTP_USERNAME"), os.environ.get("SMTP_PASSWORD")
            if username and password:
                client.login(username, password)
            client.send_message(message)
    except (OSError, smtplib.SMTPException, ValueError) as exc:
        # Background delivery must never turn a completed signup into a 503.
        print(f"[GlobeTrotter OTP] Could not send verification email to {email}: {exc}")


def verify(email: str, code: str) -> None:
    record = _codes.get(email.lower())
    if not record or record[1] < datetime.now(timezone.utc) or not secrets.compare_digest(record[0], code):
        raise HTTPException(status_code=400, detail="Invalid or expired verification code")
    del _codes[email.lower()]
