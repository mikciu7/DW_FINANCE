"""
token_tracker.py — zlicza tokeny LLM per user, blokuje po przekroczeniu limitu.
"""
from uuid import UUID
from psycopg2.extras import RealDictCursor
from backend.database import get_connection
from fastapi import HTTPException


def track_and_check(user_id: UUID | str, tokens_in: int, tokens_out: int,
                    endpoint: str, model: str):
    """
    Zapisuje użycie tokenów i sprawdza miesięczny limit.
    Rzuca HTTP 429 jeśli limit przekroczony.
    """
    uid = str(user_id)

    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Zapisz użycie
            cur.execute("""
                INSERT INTO token_usage (user_id, endpoint, tokens_in, tokens_out, model)
                VALUES (%s, %s, %s, %s, %s)
            """, (uid, endpoint, tokens_in, tokens_out, model))

            # Suma w bieżącym miesiącu
            cur.execute("""
                SELECT COALESCE(SUM(tokens_in + tokens_out), 0) AS used
                FROM token_usage
                WHERE user_id = %s
                  AND timestamp >= date_trunc('month', NOW())
            """, (uid,))
            used = cur.fetchone()["used"]

            # Pobierz limit
            cur.execute("""
                SELECT monthly_token_limit, is_blocked
                FROM user_limits WHERE user_id = %s
            """, (uid,))
            row = cur.fetchone()

        conn.commit()

    if not row:
        return

    limit = row["monthly_token_limit"]

    if used > limit:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE user_limits SET is_blocked = TRUE WHERE user_id = %s
                """, (uid,))
            conn.commit()
        raise HTTPException(
            status_code=429,
            detail=f"Miesięczny limit tokenów wyczerpany ({used:,}/{limit:,}). Skontaktuj się z administratorem."
        )


def get_monthly_usage(user_id: UUID | str) -> dict:
    uid = str(user_id)
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT
                    COALESCE(SUM(tokens_in + tokens_out), 0) AS used,
                    COALESCE(SUM(tokens_in), 0)              AS tokens_in,
                    COALESCE(SUM(tokens_out), 0)             AS tokens_out,
                    COUNT(*)                                  AS calls
                FROM token_usage
                WHERE user_id = %s
                  AND timestamp >= date_trunc('month', NOW())
            """, (uid,))
            usage = dict(cur.fetchone())

            cur.execute("""
                SELECT monthly_token_limit, is_blocked, reset_date
                FROM user_limits WHERE user_id = %s
            """, (uid,))
            limits = cur.fetchone()

    result = dict(usage)
    if limits:
        result["limit"] = limits["monthly_token_limit"]
        result["is_blocked"] = limits["is_blocked"]
        result["reset_date"] = str(limits["reset_date"]) if limits["reset_date"] else None
    return result