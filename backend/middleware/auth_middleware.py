"""
auth_middleware.py — walidacja sesji na każdym chronionym żądaniu.
"""
from fastapi import Request, HTTPException
from backend.services.auth_service import validate_session, update_last_seen, COOKIE_NAME


async def require_auth(request: Request):
    """
    Dependency do wstrzyknięcia w endpointy wymagające logowania.
    Ustawia request.state.user.
    """
    raw_token = request.cookies.get(COOKIE_NAME)
    if not raw_token:
        raise HTTPException(status_code=401, detail="Nie zalogowany")

    user = validate_session(raw_token)
    if not user:
        raise HTTPException(status_code=401, detail="Sesja wygasła lub unieważniona")

    ip = _get_ip(request)
    update_last_seen(user["id"], ip)
    request.state.user = user
    return user


async def require_admin(request: Request):
    user = await require_auth(request)
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Brak uprawnień")
    return user


def _get_ip(request: Request) -> str | None:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else None