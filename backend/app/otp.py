"""Short-lived OTP state and optional SMTP delivery for local development."""
import os
import secrets
import smtplib
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage

from fastapi import HTTPException

_codes: dict[str, tuple[str, datetime]] = {}


def issue(email: str) -> int:
    code = f"{secrets.randbelow(1_000_000):06d}"
    _codes[email.lower()] = (code, datetime.now(timezone.utc) + timedelta(minutes=5))
    host = os.environ.get("SMTP_HOST")
    if host:
        message = EmailMessage()
        message["Subject"] = "Your GlobeTrotter verification code"
        message["From"] = os.environ.get("SMTP_FROM", "no-reply@globetrotter.local")
        message["To"] = email
        message.set_content(f"Your GlobeTrotter code is {code}. It expires in 5 minutes.")
        try:
            with smtplib.SMTP(host, int(os.environ.get("SMTP_PORT", "587")), timeout=10) as client:
                if os.environ.get("SMTP_TLS", "true").lower() == "true": client.starttls()
                username, password = os.environ.get("SMTP_USERNAME"), os.environ.get("SMTP_PASSWORD")
                if username and password: client.login(username, password)
                client.send_message(message)
        except OSError as exc:
            raise HTTPException(status_code=503, detail="Could not send the verification email.") from exc
    else:
        # Development fallback: does not expose a code in API responses.
        print(f"[GlobeTrotter DEV OTP] {email}: {code}")
    return 300


def verify(email: str, code: str) -> None:
    record = _codes.get(email.lower())
    if not record or record[1] < datetime.now(timezone.utc) or not secrets.compare_digest(record[0], code):
        raise HTTPException(status_code=400, detail="Invalid or expired verification code")
    del _codes[email.lower()]
