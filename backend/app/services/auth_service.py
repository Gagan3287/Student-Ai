"""
Authentication service — JWT creation/validation and password hashing.

Design decisions:
  - bcrypt via passlib: salted, adaptive cost factor. bcrypt is the correct
    choice for password storage — argon2 is slightly better but overkill here.
  - JWT via python-jose: standard HS256 tokens. The access token payload
    contains {sub: user_id, exp: expiry_timestamp} only — minimal surface area.
  - No refresh tokens in Phase 1 (YAGNI). Can be added later.
"""

from datetime import datetime, timedelta, timezone
import logging

from jose import JWTError, jwt
import bcrypt
from sqlalchemy.orm import Session

from app.config import settings
from app.models.user import User

logger = logging.getLogger(__name__)

# ─── Password hashing ─────────────────────────────────────────────────────────
# bcrypt with default cost factor (12 in gensalt()). Higher = slower hash = harder brute force.

def hash_password(plain_password: str) -> str:
    """Hash a plain-text password with bcrypt. Store the result, never the plain text."""
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(plain_password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Return True if plain_password matches the stored bcrypt hash."""
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
    except Exception as exc:
        logger.error(f"Password verification error: {exc}")
        return False


# ─── JWT ──────────────────────────────────────────────────────────────────────

def create_access_token(user_id: str) -> tuple[str, int]:
    """
    Create a signed JWT access token.

    Returns:
        (token_string, expires_in_seconds)
    """
    expires_delta = timedelta(hours=settings.jwt_expiry_hours)
    expire = datetime.now(timezone.utc) + expires_delta

    payload = {
        "sub": user_id,         # "subject" — the user this token represents
        "exp": expire,          # expiry — python-jose handles the Unix timestamp conversion
        "iat": datetime.now(timezone.utc),  # issued-at
    }

    token = jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    return token, int(expires_delta.total_seconds())


def decode_access_token(token: str) -> str:
    """
    Decode and validate a JWT. Returns the user_id (sub claim).
    Raises JWTError (imported from jose) on any validation failure.
    """
    payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    user_id: str = payload.get("sub")
    if user_id is None:
        raise JWTError("Token missing 'sub' claim")
    return user_id


# ─── User operations ──────────────────────────────────────────────────────────

def create_user(db: Session, email: str, password: str, full_name: str | None) -> User:
    """
    Register a new user. Raises ValueError if email is already taken.
    """
    if db.query(User).filter(User.email == email.lower()).first():
        raise ValueError("A user with this email already exists")

    user = User(
        email=email.lower(),
        password_hash=hash_password(password),
        full_name=full_name,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, email: str, password: str) -> User | None:
    """
    Verify email + password. Returns the User on success, None on failure.
    Always runs the full bcrypt verification even if the user doesn't exist
    (to prevent timing-attack enumeration of valid emails).
    """
    user = db.query(User).filter(User.email == email.lower()).first()

    # If user not found, run a dummy verify to maintain constant time
    if not user:
        verify_password(password, "$2b$12$dummy.hash.to.prevent.timing.attacks.padding.extra")
        return None

    if not verify_password(password, user.password_hash):
        return None

    # Update last login timestamp
    user.last_login = datetime.now(timezone.utc)
    db.commit()

    return user
