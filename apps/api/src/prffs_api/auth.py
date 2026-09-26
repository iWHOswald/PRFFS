from secrets import compare_digest

from fastapi import Header, HTTPException

from .config import get_settings


def require_admin(x_admin_token: str | None = Header(default=None)) -> None:
    expected = get_settings().admin_token
    if not expected:
        raise HTTPException(status_code=503, detail="Admin access is not configured")
    if not x_admin_token or not compare_digest(x_admin_token.encode(), expected.encode()):
        raise HTTPException(status_code=401, detail="Admin sign-in required")
