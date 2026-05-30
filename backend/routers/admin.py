"""
admin.py — panel administracyjny: zarządzanie userami, usage stats, sesje.
"""
from fastapi import APIRouter, Depends, HTTPException
from psycopg2.extras import RealDictCursor
from backend.middleware.auth_middleware import require_admin
from backend.database import get_connection
from backend.services import auth_service as svc
from backend.services.token_tracker import get_monthly_usage
from pydantic import BaseModel

router = APIRouter(prefix="/admin", tags=["admin"],
                   dependencies=[Depends(require_admin)])


class BanRequest(BaseModel):
    reason: str


# ── Użytkownicy ───────────────────────────────────────────────────────────────

@router.get("/users")
def list_users():
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT u.id, u.email, u.role, u.is_active, u.is_banned,
                       u.ban_reason, u.totp_enabled, u.created_at,
                       u.last_seen_at, u.registration_ip, u.last_ip,
                       ul.monthly_token_limit, ul.is_blocked
                FROM users u
                LEFT JOIN user_limits ul ON ul.user_id = u.id
                ORDER BY u.created_at DESC
            """)
            rows = [dict(r) for r in cur.fetchall()]
    for r in rows:
        r["id"] = str(r["id"])
        if r.get("created_at"):  r["created_at"]   = str(r["created_at"])
        if r.get("last_seen_at"):r["last_seen_at"]  = str(r["last_seen_at"])
    return rows


@router.post("/users/{user_id}/ban")
def ban_user(user_id: str, body: BanRequest):
    user = svc.get_user_by_id(user_id)
    if not user:
        raise HTTPException(404, "Użytkownik nie istnieje")
    if user["role"] == "admin":
        raise HTTPException(403, "Nie można zbanować admina")
    svc.ban_user(user_id, body.reason)
    return {"message": f"Użytkownik {user['email']} zbanowany"}


@router.post("/users/{user_id}/unban")
def unban_user(user_id: str):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE users SET is_banned = FALSE, ban_reason = NULL WHERE id = %s
            """, (user_id,))
        conn.commit()
    return {"message": "Użytkownik odblokowany"}


@router.post("/users/{user_id}/set-limit")
def set_token_limit(user_id: str, limit: int):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE user_limits SET monthly_token_limit = %s, is_blocked = FALSE
                WHERE user_id = %s
            """, (limit, user_id))
        conn.commit()
    return {"message": f"Limit ustawiony na {limit:,} tokenów"}


# ── Sesje ─────────────────────────────────────────────────────────────────────

@router.get("/users/{user_id}/sessions")
def get_user_sessions(user_id: str):
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT id, ip, user_agent, created_at, last_active_at,
                       expires_at, revoked, revoked_reason
                FROM sessions WHERE user_id = %s
                ORDER BY created_at DESC LIMIT 20
            """, (user_id,))
            rows = [dict(r) for r in cur.fetchall()]
    for r in rows:
        r["id"] = str(r["id"])
        for f in ("created_at", "last_active_at", "expires_at", "revoked_at"):
            if r.get(f): r[f] = str(r[f])
    return rows


@router.delete("/users/{user_id}/sessions")
def revoke_user_sessions(user_id: str):
    svc.revoke_all_user_sessions(user_id, "admin_revoke")
    return {"message": "Wszystkie sesje unieważnione"}


# ── Usage stats ───────────────────────────────────────────────────────────────

@router.get("/usage")
def usage_stats():
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT
                    u.id, u.email,
                    COALESCE(SUM(t.tokens_in + t.tokens_out), 0) AS tokens_month,
                    COALESCE(COUNT(t.id), 0)                     AS calls_month,
                    ul.monthly_token_limit,
                    ul.is_blocked
                FROM users u
                LEFT JOIN token_usage t ON t.user_id = u.id
                    AND t.timestamp >= date_trunc('month', NOW())
                LEFT JOIN user_limits ul ON ul.user_id = u.id
                GROUP BY u.id, u.email, ul.monthly_token_limit, ul.is_blocked
                ORDER BY tokens_month DESC
            """)
            rows = [dict(r) for r in cur.fetchall()]
    for r in rows:
        r["id"] = str(r["id"])
    return rows


@router.get("/usage/{user_id}")
def user_usage(user_id: str):
    return get_monthly_usage(user_id)