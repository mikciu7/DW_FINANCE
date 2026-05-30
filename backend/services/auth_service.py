"""
auth_service.py — logika sesji serwerowych, haseł (Argon2id), szyfrowania TOTP.
"""
import os
import secrets
import hashlib
import base64
from datetime import datetime, timezone, timedelta
from uuid import UUID

import pyotp
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from passlib.context import CryptContext
from psycopg2.extras import RealDictCursor

from backend.database import get_connection

# ── Hasła ─────────────────────────────────────────────────────────────────────
pwd_context = CryptContext(
    schemes=["argon2"],
    argon2__memory_cost=65536,   # 64 MB
    argon2__time_cost=3,
    argon2__parallelism=2,
)

# ── Klucz AES dla TOTP secret ─────────────────────────────────────────────────
def _totp_key() -> bytes:
    key_hex = os.getenv("TOTP_ENCRYPTION_KEY", "")
    if len(key_hex) < 64:
        raise RuntimeError("TOTP_ENCRYPTION_KEY must be 32 bytes (64 hex chars) in .env")
    return bytes.fromhex(key_hex[:64])

# ── Session config ─────────────────────────────────────────────────────────────
SESSION_LIFETIME_DAYS = 30
COOKIE_NAME = "neoeye_session"


# ══════════════════════════════════════════════════════════════════════════════
# Hasła
# ══════════════════════════════════════════════════════════════════════════════

def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


# ══════════════════════════════════════════════════════════════════════════════
# Użytkownicy
# ══════════════════════════════════════════════════════════════════════════════

def get_user_by_email(email: str) -> dict | None:
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM users WHERE email = %s", (email,))
            row = cur.fetchone()
    return dict(row) if row else None


def get_user_by_id(user_id: UUID | str) -> dict | None:
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM users WHERE id = %s", (str(user_id),))
            row = cur.fetchone()
    return dict(row) if row else None


def create_user(email: str, password: str, registration_ip: str | None) -> dict:
    password_hash = hash_password(password)
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                INSERT INTO users (email, password_hash, registration_ip)
                VALUES (%s, %s, %s)
                RETURNING *
            """, (email, password_hash, registration_ip))
            user = dict(cur.fetchone())
            cur.execute("""
                INSERT INTO user_limits (user_id) VALUES (%s)
            """, (user["id"],))
        conn.commit()
    return user


def update_last_seen(user_id: UUID | str, ip: str | None):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE users SET last_seen_at = NOW(), last_ip = %s WHERE id = %s
            """, (ip, str(user_id)))
        conn.commit()


# ══════════════════════════════════════════════════════════════════════════════
# Sesje
# ══════════════════════════════════════════════════════════════════════════════

def _hash_token(raw_token: str) -> str:
    return hashlib.sha256(raw_token.encode()).hexdigest()


def create_session(user_id: UUID | str, ip: str | None, user_agent: str | None) -> str:
    """Tworzy sesję, zwraca raw token do ustawienia w cookie."""
    raw_token = secrets.token_urlsafe(48)
    token_hash = _hash_token(raw_token)
    expires_at = datetime.now(timezone.utc) + timedelta(days=SESSION_LIFETIME_DAYS)

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO sessions (user_id, session_token, ip, user_agent, expires_at)
                VALUES (%s, %s, %s, %s, %s)
            """, (str(user_id), token_hash, ip, user_agent, expires_at))
        conn.commit()
    return raw_token


def validate_session(raw_token: str) -> dict | None:
    """
    Waliduje sesję. Zwraca pełny rekord usera lub None.
    Aktualizuje last_active_at sesji przy każdym żądaniu.
    """
    token_hash = _hash_token(raw_token)
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT s.id as session_id, u.*
                FROM sessions s
                JOIN users u ON u.id = s.user_id
                WHERE s.session_token = %s
                  AND s.revoked = FALSE
                  AND s.expires_at > NOW()
                  AND u.is_banned = FALSE
                  AND u.is_active = TRUE
            """, (token_hash,))
            row = cur.fetchone()
            if row:
                cur.execute("""
                    UPDATE sessions SET last_active_at = NOW() WHERE id = %s
                """, (row["session_id"],))
        conn.commit()
    return dict(row) if row else None


def revoke_session(raw_token: str, reason: str = "logout"):
    token_hash = _hash_token(raw_token)
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE sessions
                SET revoked = TRUE, revoked_at = NOW(), revoked_reason = %s
                WHERE session_token = %s
            """, (reason, token_hash))
        conn.commit()


def revoke_all_user_sessions(user_id: UUID | str, reason: str = "admin_ban"):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE sessions
                SET revoked = TRUE, revoked_at = NOW(), revoked_reason = %s
                WHERE user_id = %s AND revoked = FALSE
            """, (reason, str(user_id)))
        conn.commit()


# ══════════════════════════════════════════════════════════════════════════════
# TOTP
# ══════════════════════════════════════════════════════════════════════════════

def generate_totp_secret() -> str:
    return pyotp.random_base32()


def encrypt_totp_secret(secret: str) -> str:
    key = _totp_key()
    aesgcm = AESGCM(key)
    nonce = os.urandom(12)
    ciphertext = aesgcm.encrypt(nonce, secret.encode(), None)
    return base64.b64encode(nonce + ciphertext).decode()


def decrypt_totp_secret(enc: str) -> str:
    key = _totp_key()
    aesgcm = AESGCM(key)
    data = base64.b64decode(enc)
    nonce, ciphertext = data[:12], data[12:]
    return aesgcm.decrypt(nonce, ciphertext, None).decode()


def get_totp_uri(secret: str, email: str) -> str:
    return pyotp.TOTP(secret).provisioning_uri(email, issuer_name="NeoEye")


def verify_totp_code(user: dict, code: str) -> bool:
    if not user.get("totp_secret_enc"):
        return False
    secret = decrypt_totp_secret(user["totp_secret_enc"])
    totp = pyotp.TOTP(secret)
    return totp.verify(code, valid_window=2)


def enable_totp(user_id: UUID | str, secret_enc: str):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE users
                SET totp_secret_enc = %s, totp_enabled = TRUE
                WHERE id = %s
            """, (secret_enc, str(user_id)))
        conn.commit()


# ══════════════════════════════════════════════════════════════════════════════
# Tokeny jednorazowe (email verification, password reset)
# ══════════════════════════════════════════════════════════════════════════════

def create_verification_token(user_id: UUID | str, token_type: str,
                               expires_hours: int = 24) -> str:
    raw = secrets.token_urlsafe(32)
    token_hash = _hash_token(raw)
    expires_at = datetime.now(timezone.utc) + timedelta(hours=expires_hours)
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO verification_tokens (token, user_id, type, expires_at)
                VALUES (%s, %s, %s, %s)
            """, (token_hash, str(user_id), token_type, expires_at))
        conn.commit()
    return raw


def consume_verification_token(raw_token: str, token_type: str) -> UUID | None:
    token_hash = _hash_token(raw_token)
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT * FROM verification_tokens
                WHERE token = %s AND type = %s AND used = FALSE AND expires_at > NOW()
            """, (token_hash, token_type))
            row = cur.fetchone()
            if not row:
                return None
            cur.execute("UPDATE verification_tokens SET used = TRUE WHERE token = %s",
                        (token_hash,))
        conn.commit()
    return row["user_id"]


# ══════════════════════════════════════════════════════════════════════════════
# IP / anti-abuse helpers
# ══════════════════════════════════════════════════════════════════════════════

def log_login_attempt(ip: str, email: str, success: bool):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO login_attempts (ip, email, success) VALUES (%s, %s, %s)
            """, (ip, email, success))
        conn.commit()


def is_ip_rate_limited(ip: str) -> bool:
    """True jeśli IP ma >= 10 nieudanych prób w ostatniej godzinie."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT COUNT(*) FROM login_attempts
                WHERE ip = %s AND success = FALSE
                  AND timestamp > NOW() - INTERVAL '1 hour'
            """, (ip,))
            count = cur.fetchone()[0]
    return count >= 10


def count_accounts_for_ip(ip: str) -> int:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM users WHERE registration_ip = %s", (ip,))
            return cur.fetchone()[0]


def ban_user(user_id: UUID | str, reason: str):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE users SET is_banned = TRUE, ban_reason = %s WHERE id = %s
            """, (reason, str(user_id)))
        conn.commit()
    revoke_all_user_sessions(user_id, reason="banned")


def activate_user(user_id: UUID | str):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE users SET is_active = TRUE, email_verified = TRUE WHERE id = %s
            """, (str(user_id),))
        conn.commit()