import smtplib
import logging
from email.mime.text import MIMEText

import config

logger = logging.getLogger("portfolio.email")


def send_contact_notification(name: str, email: str, message: str, event_date: str | None):
    if not config.SMTP_HOST or not config.NOTIFY_EMAIL:
        logger.info("Email not configured — skipping notification for %s", email)
        return

    body = (
        f"New inquiry from the portfolio site.\n\n"
        f"Name: {name}\n"
        f"Email: {email}\n"
        f"Event date: {event_date or 'Not specified'}\n\n"
        f"Message:\n{message}\n"
    )

    msg = MIMEText(body)
    msg["Subject"] = f"New portfolio inquiry from {name}"
    msg["From"] = config.SMTP_USER
    msg["To"] = config.NOTIFY_EMAIL

    try:
        with smtplib.SMTP(config.SMTP_HOST, config.SMTP_PORT, timeout=10) as server:
            server.starttls()

            if config.SMTP_USER:
                server.login(config.SMTP_USER, config.SMTP_PASS)

            server.sendmail(
                msg["From"],
                [config.NOTIFY_EMAIL],
                msg.as_string(),
            )

        logger.info("Contact notification email sent for %s", email)

    except Exception:
        logger.exception("Failed to send contact notification email")
        raise
