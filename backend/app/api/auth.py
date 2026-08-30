from fastapi import APIRouter, Depends, HTTPException, Request, Response, status

from app.auth.dependencies import COOKIE_NAME, get_current_username
from app.auth.schemas import LoginRequest, UserOut
from app.auth.service import create_access_token, verify_password
from app.config import Settings, get_settings
from app.rate_limit import limiter

router = APIRouter(tags=["auth"])


@router.post("/auth/login", response_model=UserOut)
@limiter.limit("5/minute")
def login(
    request: Request,
    response: Response,
    body: LoginRequest,
    settings: Settings = Depends(get_settings),
) -> UserOut:
    valid_username = body.username == settings.demo_username
    valid_password = verify_password(body.password, settings.demo_password_hash)
    if not (valid_username and valid_password):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password")

    token = create_access_token(body.username, settings.auth_secret, settings.auth_token_ttl_minutes)
    is_production = settings.env != "development"
    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        httponly=True,
        secure=is_production,
        # Frontend and backend are on different domains in production (Vercel vs
        # Render) - a cross-site fetch() only sends the cookie with SameSite=None,
        # which itself requires Secure. Lax is fine (and simpler) for same-origin dev.
        samesite="none" if is_production else "lax",
        max_age=settings.auth_token_ttl_minutes * 60,
    )
    return UserOut(username=body.username)


@router.post("/auth/logout")
def logout(response: Response) -> dict:
    response.delete_cookie(COOKIE_NAME)
    return {"ok": True}


@router.get("/auth/me", response_model=UserOut)
def me(username: str = Depends(get_current_username)) -> UserOut:
    return UserOut(username=username)
