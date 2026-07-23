import os
from pathlib import Path
from dotenv import load_dotenv

# Points at the folder this file lives in, so portfolio.db and uploads/
# always land next to your code no matter how the project is run.
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

# -----------------------------
# Database
# -----------------------------
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'portfolio.db'}")

# -----------------------------
# Admin auth (username + password, JWT session tokens)
# -----------------------------
# Used only to create the FIRST admin account on first run. After that,
# log in and change the password from the dashboard — these env values
# are ignored once an admin account already exists in the DB.
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "change-me-please")

# Secret used to sign login session tokens. MUST be a long random value
# in production — anyone with this secret can forge admin sessions.
JWT_SECRET = os.getenv("JWT_SECRET", "dev-only-insecure-secret-change-me")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "720"))  # 12 hours

# -----------------------------
# Uploads
# -----------------------------
UPLOAD_DIR = BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

MAX_UPLOAD_MB = int(os.getenv("MAX_UPLOAD_MB", "8"))

ALLOWED_IMAGE_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp",
}

ALLOWED_VIDEO_TYPES = {
    "video/mp4",
    "video/webm",
    "video/quicktime",
}

MAX_REEL_MB = int(os.getenv("MAX_REEL_MB", "100"))

# -----------------------------
# CORS
# -----------------------------
CORS_ORIGINS = [
    origin.strip()
    for origin in os.getenv("CORS_ORIGINS", "*").split(",")
]

# -----------------------------
# Email (optional — if SMTP_HOST is unset, contact form still saves to DB,
# it just skips sending a notification email)
# -----------------------------
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "nverrma123@gmail.com")
SMTP_PASS = os.getenv("SMTP_PASS", "xrksxzwpeperpgue")
NOTIFY_EMAIL = os.getenv("NOTIFY_EMAIL", "nverrma123@gmail.com")


# TWILIO_SID = os.getenv("ACa3bc4b2c803385dafd623f8fdb8864f2")
# TWILIO_AUTH_TOKEN = os.getenv("410c210d06fa70e4d13d7c6852359e5c")
# TWILIO_WHATSAPP_FROM = os.getenv("+14155238886")
# YOUR_WHATSAPP_NUMBER = os.getenv("9005154244")


# -----------------------------
# Contact form rate limiting (in-memory, per-process)
# -----------------------------
CONTACT_RATE_LIMIT_PER_HOUR = int(os.getenv("CONTACT_RATE_LIMIT_PER_HOUR", "5"))

RESEND_API_KEY = os.getenv("RESEND_API_KEY", "re_G87YyVsR_DmYK2wdRgvBQGU4an3M5TxYM")
