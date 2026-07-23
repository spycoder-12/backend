"""
Username + password admin authentication.

Login flow:
  1. POST /admin/login {username, password} -> verifies against the hashed
     password stored in the `admins` table, returns a signed JWT.
  2. The dashboard stores that JWT and sends it as
     `Authorization: Bearer <token>` on every admin-only request.
  3. `require_admin` (a FastAPI dependency) verifies the token on each
     request and rejects anything invalid/expired.

Passwords are hashed with bcrypt directly (not via passlib) — passlib's
bcrypt backend has a known incompatibility with bcrypt>=4.1 (it looks for
a `bcrypt.__about__.__version__` attribute that no longer exists), so we
skip that layer entirely and call the bcrypt library ourselves.
"""

from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

import Models
import config
from Database import get_db

# Registering this as a security scheme (instead of a raw Header param) is
# what makes Swagger UI show a proper "Authorize" lock button — paste the
# token from /admin/login once and it's sent on every protected request you
# try from /docs. auto_error=False so we can return our own 401 message
# instead of FastAPI's generic one when the header is missing entirely.
_bearer_scheme = HTTPBearer(auto_error=False)

# bcrypt silently ignores/breaks on inputs over 72 bytes, so we truncate
# defensively before hashing or checking.
_MAX_PASSWORD_BYTES = 72


def hash_password(password: str) -> str:
    pw_bytes = password.encode("utf-8")[:_MAX_PASSWORD_BYTES]
    return bcrypt.hashpw(pw_bytes, bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    pw_bytes = password.encode("utf-8")[:_MAX_PASSWORD_BYTES]
    try:
        return bcrypt.checkpw(pw_bytes, password_hash.encode("utf-8"))
    except ValueError:
        # Malformed/legacy hash in the DB — treat as a failed login, not a 500.
        return False


def create_access_token(username: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=config.JWT_EXPIRE_MINUTES)
    payload = {"sub": username, "exp": expire}
    return jwt.encode(payload, config.JWT_SECRET, algorithm=config.JWT_ALGORITHM)


def _decode_access_token(token: str) -> str:
    try:
        payload = jwt.decode(token, config.JWT_SECRET, algorithms=[config.JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session expired, please log in again")
    except jwt.PyJWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid session token")
    return payload["sub"]


def require_admin(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer_scheme),
    db: Session = Depends(get_db),
) -> str:
    """FastAPI dependency: validates the Bearer token and returns the admin's username."""
    if credentials is None or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid Authorization header",
        )

    token = credentials.credentials
    username = _decode_access_token(token)

    admin = db.query(Models.Admin).filter(Models.Admin.username == username).first()
    if admin is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Admin account no longer exists")

    return username


def ensure_default_admin(db: Session) -> None:
    """Creates the first admin account (from env vars) if the table is empty.

    Runs once at startup. If an admin already exists, this is a no-op —
    env vars only matter for bootstrapping the very first account.
    """
    if db.query(Models.Admin).first() is not None:
        return

    default_admin = Models.Admin(
        username=config.ADMIN_USERNAME,
        password_hash=hash_password(config.ADMIN_PASSWORD),
    )
    db.add(default_admin)
    db.commit()
