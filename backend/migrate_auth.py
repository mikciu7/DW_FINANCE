"""
migrate_auth.py — jednorazowa migracja: dodaje tabele systemu autentykacji.
Uruchom raz na istniejącej bazie:
    python -m backend.migrate_auth
"""
import os, sys
ROOT = os.path.dirname(os.path.dirname(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from backend.database import get_connection


def migrate():
    print("=== Auth migration ===")
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE EXTENSION IF NOT EXISTS "pgcrypto";

                -- ── Użytkownicy ────────────────────────────────────────────
                CREATE TABLE IF NOT EXISTS users (
                    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    email             TEXT UNIQUE NOT NULL,
                    password_hash     TEXT NOT NULL,
                    totp_secret_enc   TEXT,
                    totp_enabled      BOOLEAN DEFAULT FALSE,
                    backup_codes_hash TEXT[],
                    is_active         BOOLEAN DEFAULT FALSE,
                    is_banned         BOOLEAN DEFAULT FALSE,
                    ban_reason        TEXT,
                    role              TEXT DEFAULT 'user',
                    created_at        TIMESTAMPTZ DEFAULT NOW(),
                    last_seen_at      TIMESTAMPTZ,
                    registration_ip   INET,
                    last_ip           INET,
                    email_verified    BOOLEAN DEFAULT FALSE
                );

                -- ── Sesje serwerowe ────────────────────────────────────────
                CREATE TABLE IF NOT EXISTS sessions (
                    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    session_token   TEXT UNIQUE NOT NULL,
                    ip              INET,
                    user_agent      TEXT,
                    created_at      TIMESTAMPTZ DEFAULT NOW(),
                    last_active_at  TIMESTAMPTZ DEFAULT NOW(),
                    expires_at      TIMESTAMPTZ NOT NULL,
                    revoked         BOOLEAN DEFAULT FALSE,
                    revoked_at      TIMESTAMPTZ,
                    revoked_reason  TEXT
                );
                CREATE INDEX IF NOT EXISTS idx_sessions_token
                    ON sessions(session_token) WHERE NOT revoked;
                CREATE INDEX IF NOT EXISTS idx_sessions_user
                    ON sessions(user_id);

                -- ── Użycie tokenów LLM ─────────────────────────────────────
                CREATE TABLE IF NOT EXISTS token_usage (
                    id          BIGSERIAL PRIMARY KEY,
                    user_id     UUID NOT NULL REFERENCES users(id),
                    timestamp   TIMESTAMPTZ DEFAULT NOW(),
                    endpoint    TEXT NOT NULL,
                    tokens_in   INTEGER NOT NULL DEFAULT 0,
                    tokens_out  INTEGER NOT NULL DEFAULT 0,
                    model       TEXT
                );
                CREATE INDEX IF NOT EXISTS idx_token_usage_user_month
                    ON token_usage(user_id, timestamp);

                -- ── Limity per użytkownik ──────────────────────────────────
                CREATE TABLE IF NOT EXISTS user_limits (
                    user_id             UUID PRIMARY KEY REFERENCES users(id),
                    monthly_token_limit INTEGER DEFAULT 100000,
                    is_blocked          BOOLEAN DEFAULT FALSE,
                    reset_date          DATE DEFAULT (
                        date_trunc('month', NOW()) + INTERVAL '1 month'
                    )
                );

                -- ── Próby logowania ────────────────────────────────────────
                CREATE TABLE IF NOT EXISTS login_attempts (
                    id        BIGSERIAL PRIMARY KEY,
                    ip        INET NOT NULL,
                    email     TEXT,
                    success   BOOLEAN NOT NULL,
                    timestamp TIMESTAMPTZ DEFAULT NOW()
                );
                CREATE INDEX IF NOT EXISTS idx_login_attempts_ip
                    ON login_attempts(ip, timestamp);

                -- ── Tokeny jednorazowe (email, reset hasła) ────────────────
                CREATE TABLE IF NOT EXISTS verification_tokens (
                    token      TEXT PRIMARY KEY,
                    user_id    UUID REFERENCES users(id) ON DELETE CASCADE,
                    type       TEXT NOT NULL,
                    expires_at TIMESTAMPTZ NOT NULL,
                    used       BOOLEAN DEFAULT FALSE
                );
            """)
        conn.commit()
    print("[1/1] Tabele auth utworzone.")

    # Utwórz konto admina jeśli nie istnieje
    _create_admin_if_missing()
    print("=== Migracja zakonczona ===")


def _create_admin_if_missing():
    admin_email = os.getenv("ADMIN_EMAIL")
    admin_password = os.getenv("ADMIN_PASSWORD")
    if not admin_email or not admin_password:
        print("[!] Brak ADMIN_EMAIL / ADMIN_PASSWORD w .env — pomijam tworzenie admina.")
        return

    from passlib.context import CryptContext
    pwd_ctx = CryptContext(
        schemes=["argon2"],
        argon2__memory_cost=65536,
        argon2__time_cost=3,
        argon2__parallelism=2,
    )
    password_hash = pwd_ctx.hash(admin_password)

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM users WHERE email = %s", (admin_email,))
            if cur.fetchone():
                print(f"[admin] Konto {admin_email} już istnieje.")
                return
            cur.execute("""
                INSERT INTO users (email, password_hash, is_active, email_verified, role)
                VALUES (%s, %s, TRUE, TRUE, 'admin')
                RETURNING id
            """, (admin_email, password_hash))
            user_id = cur.fetchone()[0]
            cur.execute("""
                INSERT INTO user_limits (user_id, monthly_token_limit)
                VALUES (%s, 10000000)
            """, (user_id,))
        conn.commit()
    print(f"[admin] Konto admina {admin_email} utworzone.")


if __name__ == "__main__":
    migrate()