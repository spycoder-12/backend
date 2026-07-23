import logging
import resend

import config

logger = logging.getLogger("portfolio.email")


def send_contact_notification(name: str, email: str, message: str, event_date: str | None):
    if not config.RESEND_API_KEY or not config.NOTIFY_EMAIL:
        logger.info("Email not configured — skipping notification for %s", email)
        return

    resend.api_key = config.RESEND_API_KEY

    body_html = (
        f"<p><strong>Name:</strong> {name}</p>"
        f"<p><strong>Email:</strong> {email}</p>"
        f"<p><strong>Event date:</strong> {event_date or 'Not specified'}</p>"
        f"<p><strong>Message:</strong><br>{message}</p>"
    )

    try:
        resend.Emails.send({
            "from": "onboarding@resend.dev",
            "to": config.NOTIFY_EMAIL,
            "subject": f"New portfolio inquiry from {name}",
            "html": body_html,
        })
        logger.info("Contact notification email sent for %s", email)

    except Exception:
        logger.exception("Failed to send contact notification email")
        raise
