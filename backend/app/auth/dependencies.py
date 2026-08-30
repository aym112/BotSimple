from fastapi import Depends, HTTPException, Request, status

from app.auth.service import _COOKIE_NAME, decode_access_token
from app.config import Settings, get_settings

COOKIE_NAME = _COOKIE_NAME


def get_current_username(request: Request, settings: Settings = Depends(get_settings)) -> str:
    token = request.cookies.get(COOKIE_NAME)
    if not token:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    username = decode_access_token(token, settings.auth_secret)
    if not username:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired session")
    return username
