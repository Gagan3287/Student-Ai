"""
JWT authentication middleware — FastAPI dependency for protected routes.

Usage in any router:
    from app.middleware.auth_middleware import get_current_user
    from app.models.user import User

    @router.get("/protected")
    def protected_endpoint(current_user: User = Depends(get_current_user)):
        return {"user_id": str(current_user.id)}

The dependency extracts the token from the Authorization header, decodes it,
and fetches the corresponding user from the database. If anything fails
(missing header, invalid token, expired token, deleted user), it raises
HTTP 401 with a descriptive detail message.
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.services.auth_service import decode_access_token

# HTTPBearer extracts the token from "Authorization: Bearer <token>"
bearer_scheme = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    """
    FastAPI dependency that validates a JWT and returns the current User.

    Raises HTTP 401 on:
      - Missing Authorization header
      - Malformed or expired JWT
      - User not found in database (e.g. account deleted after token issued)
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        user_id = decode_access_token(credentials.credentials)
    except JWTError:
        raise credentials_exception

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise credentials_exception

    return user
