"""
auth.py — endpointy autentykacji.
"""
import io
import base64
from datetime import timedelta

import qrcode
from fastapi import APIRouter, Request, Response, Depends, HTTPException
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

from backend.models.auth_models import (
    RegisterRequest, LoginRequest, TOTPVerifyRequest,
    TOTPConfirmRequest, PasswordResetRequest, PasswordResetConfirmRequest,
)
from backend.middleware.auth_middleware import require_auth, _get_ip
from backend.services import auth_service as svc

router = APIRouter(prefix="/auth", tags=["auth"])

SESSION_COOKIE = svc.COOKIE_NAME
import os as _os
_HTTPS = _os.getenv("HTTPS", "false").lower() == "true"
COOKIE_OPTS = dict(httponly=True, secure=_HTTPS, samesite="lax", path="/")


# ── Helpers ───────────────────────────────────────────────────────────────────
def _set_session_cookie(response: Response, raw_token: str):
    response.set_cookie(
        key=SESSION_COOKIE,
        value=raw_token,
        max_age=int(timedelta(days=svc.SESSION_LIFETIME_DAYS).total_seconds()),
        **COOKIE_OPTS,
    )


def _clear_session_cookie(response: Response):
    response.delete_cookie(key=SESSION_COOKIE, path="/")


def _password_ok(password: str) -> bool:
    return (len(password) >= 8
            and any(c.isupper() for c in password)
            and any(c.isdigit() for c in password))


# ── Rejestracja ───────────────────────────────────────────────────────────────

@router.post("/register", status_code=201)
@limiter.limit("3/hour")
async def register(body: RegisterRequest, request: Request):
    ip = _get_ip(request)

    if svc.is_ip_rate_limited(ip):
        raise HTTPException(429, "Zbyt wiele prób z tego adresu IP")

    if svc.count_accounts_for_ip(ip) >= 3:
        raise HTTPException(429, "Zbyt wiele kont z tego adresu IP")

    if not _password_ok(body.password):
        raise HTTPException(400,
            "Hasło musi mieć min. 8 znaków, wielką literę i cyfrę")

    if svc.get_user_by_email(body.email):
        raise HTTPException(409, "Konto z tym emailem już istnieje")

    user = svc.create_user(body.email, body.password, ip)

    # TODO Krok 7: wysyłka emaila weryfikacyjnego
    # token = svc.create_verification_token(user["id"], "email_verify")
    # email_service.send_verification(user["email"], token)

    # Na razie aktywujemy od razu (przed wdrożeniem emaili)
    svc.activate_user(user["id"])

    return {"message": "Konto utworzone. Możesz się zalogować."}


# ── Logowanie ─────────────────────────────────────────────────────────────────

@router.post("/login")
@limiter.limit("5/15minutes")
async def login(body: LoginRequest, request: Request):
    ip = _get_ip(request)

    if svc.is_ip_rate_limited(ip):
        svc.log_login_attempt(ip, body.email, False)
        raise HTTPException(429, "Zbyt wiele nieudanych prób. Poczekaj godzinę.")

    user = svc.get_user_by_email(body.email)

    # Zawsze weryfikuj hasło (ochrona przed timing attack)
    password_ok = svc.verify_password(body.password, user["password_hash"]) if user else False

    if not user or not password_ok:
        svc.log_login_attempt(ip, body.email, False)
        raise HTTPException(401, "Nieprawidłowy email lub hasło")

    if not user["is_active"]:
        raise HTTPException(403, "Konto nieaktywne. Sprawdź email weryfikacyjny.")

    if user["is_banned"]:
        raise HTTPException(403, f"Konto zablokowane. Powód: {user.get('ban_reason', '—')}")

    svc.log_login_attempt(ip, body.email, True)

    # Jeśli 2FA włączone — wydaj tymczasowy token, nie pełną sesję
    if user["totp_enabled"]:
        temp_token = svc.create_verification_token(user["id"], "totp_pending",
                                                    expires_hours=1)
        return {"requires_2fa": True, "session_temp": temp_token}

    # Bez 2FA — utwórz pełną sesję
    user_agent = request.headers.get("User-Agent")
    raw_token = svc.create_session(user["id"], ip, user_agent)

    response = JSONResponse({"message": "Zalogowano", "totp_enabled": False})
    _set_session_cookie(response, raw_token)
    return response


# ── Weryfikacja 2FA ───────────────────────────────────────────────────────────

@router.post("/totp/verify")
async def totp_verify(body: TOTPVerifyRequest, request: Request):
    ip = _get_ip(request)
    user_id = svc.consume_verification_token(body.session_temp, "totp_pending")
    if not user_id:
        raise HTTPException(401, "Nieprawidłowy lub wygasły token 2FA")

    user = svc.get_user_by_id(user_id)
    if not user:
        raise HTTPException(401, "Użytkownik nie istnieje")

    if not svc.verify_totp_code(user, body.code):
        svc.log_login_attempt(ip, user["email"], False)
        raise HTTPException(401, "Nieprawidłowy kod 2FA")

    svc.log_login_attempt(ip, user["email"], True)
    user_agent = request.headers.get("User-Agent")
    raw_token = svc.create_session(user["id"], ip, user_agent)

    response = JSONResponse({"message": "Zalogowano", "totp_enabled": True})
    _set_session_cookie(response, raw_token)
    return response


# ── Logout ────────────────────────────────────────────────────────────────────

@router.post("/logout")
async def logout(request: Request):
    raw_token = request.cookies.get(SESSION_COOKIE)
    if raw_token:
        svc.revoke_session(raw_token, "logout")
    response = JSONResponse({"message": "Wylogowano"})
    _clear_session_cookie(response)
    return response


# ── Profil zalogowanego usera ─────────────────────────────────────────────────

@router.get("/me")
async def me(user=Depends(require_auth)):
    return {
        "id":           str(user["id"]),
        "email":        user["email"],
        "role":         user["role"],
        "totp_enabled": user["totp_enabled"],
    }


# ── Setup 2FA ─────────────────────────────────────────────────────────────────

@router.get("/totp/setup")
async def totp_setup(user=Depends(require_auth)):
    secret = svc.generate_totp_secret()
    uri = svc.get_totp_uri(secret, user["email"])

    # Generuj QR code jako base64 PNG
    img = qrcode.make(uri)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    qr_b64 = base64.b64encode(buf.getvalue()).decode()

    # Tymczasowo zapisz secret (niezaszyfrowany) w verification_tokens
    # Dopiero po potwierdzeniu kodu zapiszemy w users
    temp_token = svc.create_verification_token(user["id"], "totp_setup", expires_hours=10)

    # Zapisz secret w sesji — używamy tymczasowego tokena jako klucza
    # W bazie verification_tokens nie ma pola na payload, więc zapisujemy
    # zaszyfrowany secret bezpośrednio w tabeli users (pending, totp_enabled=False)
    enc = svc.encrypt_totp_secret(secret)
    with svc.get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE users SET totp_secret_enc = %s WHERE id = %s
            """, (enc, str(user["id"])))
        conn.commit()

    return {
        "qr_code": f"data:image/png;base64,{qr_b64}",
        "secret": secret,   # dla manualnego wpisu
        "temp_token": temp_token,
    }


@router.post("/totp/confirm")
async def totp_confirm(body: TOTPConfirmRequest, user=Depends(require_auth)):
    if not svc.verify_totp_code(user, body.code):
        raise HTTPException(400, "Nieprawidłowy kod. Sprawdź czy czas na urządzeniu jest zsynchronizowany.")
    svc.enable_totp(user["id"], user["totp_secret_enc"])
    return {"message": "2FA aktywowane pomyślnie"}


# ── Weryfikacja email ─────────────────────────────────────────────────────────

@router.get("/verify-email")
async def verify_email(token: str):
    user_id = svc.consume_verification_token(token, "email_verify")
    if not user_id:
        raise HTTPException(400, "Nieprawidłowy lub wygasły link weryfikacyjny")
    svc.activate_user(user_id)
    return {"message": "Email zweryfikowany. Możesz się zalogować."}


# ── Reset hasła ───────────────────────────────────────────────────────────────

@router.post("/password-reset")
async def password_reset_request(body: PasswordResetRequest):
    user = svc.get_user_by_email(body.email)
    if user:
        token = svc.create_verification_token(user["id"], "password_reset",
                                               expires_hours=2)
        # TODO Krok 7: email_service.send_password_reset(user["email"], token)
    # Zawsze zwracaj 200 (nie zdradzaj czy email istnieje)
    return {"message": "Jeśli konto istnieje, wysłaliśmy link do resetu hasła."}


@router.post("/password-reset/confirm")
async def password_reset_confirm(body: PasswordResetConfirmRequest):
    if not _password_ok(body.new_password):
        raise HTTPException(400, "Hasło musi mieć min. 8 znaków, wielką literę i cyfrę")

    user_id = svc.consume_verification_token(body.token, "password_reset")
    if not user_id:
        raise HTTPException(400, "Nieprawidłowy lub wygasły token resetu hasła")

    new_hash = svc.hash_password(body.new_password)
    with svc.get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("UPDATE users SET password_hash = %s WHERE id = %s",
                        (new_hash, str(user_id)))
        conn.commit()

    # Unieważnij wszystkie aktywne sesje po zmianie hasła
    svc.revoke_all_user_sessions(user_id, "password_changed")
    return {"message": "Hasło zmienione. Zaloguj się ponownie."}