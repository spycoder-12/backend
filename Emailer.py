import logging
import requests

import config

logger = logging.getLogger("portfolio.email")


def send_contact_notification(name: str, email: str, message: str, event_date: str | None):
    if not config.RESEND_API_KEY or not config.NOTIFY_EMAIL:
        logger.info("Email not configured — skipping notification for %s", email)
        return

    body = (
        f"New inquiry from the portfolio site.\n\n"
        f"Name: {name}\n"
        f"Email: {email}\n"
        f"Event date: {event_date or 'Not specified'}\n\n"
        f"Message:\n{message}\n"
    )

    try:
        response = requests.post(
            "https://api.resend.com/emails",
            headers={"Authorization": f"Bearer {config.RESEND_API_KEY}"},
            json={
                "from": "onboarding@resend.dev",
                "to": [config.NOTIFY_EMAIL],
                "subject": f"New portfolio inquiry from {name}",
                "text": body,
            },
            timeout=10,
        )
        response.raise_for_status()
        logger.info("Contact notification email sent for %s", email)

    except Exception:
        logger.exception("Failed to send contact notification email")
        raise
