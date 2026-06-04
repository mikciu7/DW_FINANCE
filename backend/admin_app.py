"""
admin_app.py — Panel administracyjny NeoEye.
Dostepny TYLKO przez SSH tunnel:
    ssh -L 8080:localhost:8080 -i klucz.pem ubuntu@EC2_IP
Potem: http://localhost:8080
"""
import os
from datetime import datetime
from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()

from backend.database import get_connection
from backend.services import auth_service as svc
from backend.services.token_tracker import get_monthly_usage

app = FastAPI(title="NeoEye Admin", docs_url=None, redoc_url=None)


# ── HTML helpers ───────────────────────────────────────────────────────────────

def page(title: str, body: str, flash: str = "") -> HTMLResponse:
    flash_html = f'<div class="flash">{flash}</div>' if flash else ""
    html = f"""<!DOCTYPE html>
<html lang="pl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>NeoEye Admin — {title}</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
          background: #0f172a; color: #e2e8f0; min-height: 100vh; }}
  nav {{ background: #1e293b; border-bottom: 1px solid #334155; padding: 12px 24px;
         display: flex; gap: 24px; align-items: center; }}
  nav .logo {{ color: #60a5fa; font-weight: 700; font-size: 18px; margin-right: 16px; }}
  nav a {{ color: #94a3b8; text-decoration: none; font-size: 14px; padding: 6px 12px;
           border-radius: 6px; transition: all .15s; }}
  nav a:hover, nav a.active {{ background: #334155; color: #e2e8f0; }}
  .container {{ max-width: 1400px; margin: 0 auto; padding: 24px; }}
  h1 {{ font-size: 22px; font-weight: 600; margin-bottom: 20px; color: #f1f5f9; }}
  .flash {{ background: #166534; border: 1px solid #16a34a; color: #bbf7d0;
            padding: 10px 16px; border-radius: 8px; margin-bottom: 16px; font-size: 14px; }}
  .flash.err {{ background: #7f1d1d; border-color: #dc2626; color: #fecaca; }}
  table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
  th {{ background: #1e293b; padding: 10px 12px; text-align: left; font-weight: 600;
        color: #94a3b8; border-bottom: 1px solid #334155; white-space: nowrap; }}
  td {{ padding: 9px 12px; border-bottom: 1px solid #1e293b; vertical-align: middle; }}
  tr:hover td {{ background: #1e293b44; }}
  .badge {{ display: inline-block; padding: 2px 8px; border-radius: 9999px; font-size: 11px; font-weight: 600; }}
  .badge-green {{ background: #14532d; color: #86efac; }}
  .badge-red {{ background: #7f1d1d; color: #fca5a5; }}
  .badge-yellow {{ background: #713f12; color: #fcd34d; }}
  .badge-blue {{ background: #1e3a5f; color: #93c5fd; }}
  .badge-gray {{ background: #1e293b; color: #94a3b8; }}
  .btn {{ display: inline-block; padding: 5px 12px; border-radius: 6px; font-size: 12px;
          font-weight: 600; cursor: pointer; border: none; text-decoration: none; transition: all .15s; }}
  .btn-red {{ background: #dc2626; color: #fff; }}
  .btn-red:hover {{ background: #b91c1c; }}
  .btn-green {{ background: #16a34a; color: #fff; }}
  .btn-green:hover {{ background: #15803d; }}
  .btn-blue {{ background: #2563eb; color: #fff; }}
  .btn-blue:hover {{ background: #1d4ed8; }}
  .btn-gray {{ background: #334155; color: #e2e8f0; }}
  .btn-gray:hover {{ background: #475569; }}
  .progress {{ background: #1e293b; border-radius: 9999px; height: 6px; min-width: 80px; }}
  .progress-bar {{ height: 6px; border-radius: 9999px; background: #3b82f6; }}
  .progress-bar.warn {{ background: #f59e0b; }}
  .progress-bar.danger {{ background: #ef4444; }}
  .stat-card {{ background: #1e293b; border: 1px solid #334155; border-radius: 12px;
                padding: 20px 24px; display: inline-block; min-width: 160px; }}
  .stat-card .val {{ font-size: 28px; font-weight: 700; color: #f1f5f9; }}
  .stat-card .lbl {{ font-size: 12px; color: #64748b; margin-top: 4px; }}
  .cards {{ display: flex; gap: 16px; flex-wrap: wrap; margin-bottom: 24px; }}
  .modal-form {{ background: #1e293b; border: 1px solid #334155; border-radius: 12px;
                 padding: 20px; max-width: 500px; margin-bottom: 24px; }}
  input[type=text], input[type=number], select {{
    background: #0f172a; border: 1px solid #334155; color: #e2e8f0;
    padding: 7px 12px; border-radius: 6px; font-size: 13px; width: 100%; }}
  input:focus, select:focus {{ outline: none; border-color: #3b82f6; }}
  label {{ display: block; font-size: 12px; color: #94a3b8; margin-bottom: 4px; margin-top: 12px; }}
  .mono {{ font-family: 'SF Mono', Monaco, monospace; font-size: 12px; color: #94a3b8; }}
</style>
</head>
<body>
<nav>
  <span class="logo">NeoEye Admin</span>
  <a href="/">Dashboard</a>
  <a href="/users">Uzytkownicy</a>
  <a href="/usage">Zuzycie tokenow</a>
  <a href="/sessions">Sesje</a>
</nav>
<div class="container">
  <h1>{title}</h1>
  {flash_html}
  {body}
</div>
</body>
</html>"""
    return HTMLResponse(html)


def fmt_dt(dt) -> str:
    if not dt: return "—"
    if isinstance(dt, str): return dt[:16]
    return str(dt)[:16]


def pct_bar(used: int, limit: int) -> str:
    if not limit: return ""
    pct = min(100, int(used / limit * 100))
    cls = "danger" if pct >= 90 else ("warn" if pct >= 70 else "")
    return f'<div class="progress"><div class="progress-bar {cls}" style="width:{pct}%"></div></div><span style="font-size:11px;color:#64748b">{pct}%</span>'


# ── Routes ─────────────────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
def dashboard():
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT COUNT(*) as n FROM users")
            total_users = cur.fetchone()["n"]
            cur.execute("SELECT COUNT(*) as n FROM users WHERE is_banned=TRUE")
            banned = cur.fetchone()["n"]
            cur.execute("SELECT COUNT(*) as n FROM sessions WHERE revoked=FALSE AND expires_at > NOW()")
            active_sessions = cur.fetchone()["n"]
            cur.execute("""
                SELECT COALESCE(SUM(tokens_in+tokens_out),0) as n FROM token_usage
                WHERE timestamp >= date_trunc('month', NOW())
            """)
            tokens_month = cur.fetchone()["n"]
            cur.execute("""
                SELECT u.email, COALESCE(SUM(t.tokens_in+t.tokens_out),0) as tok
                FROM users u
                LEFT JOIN token_usage t ON t.user_id=u.id AND t.timestamp >= NOW()-INTERVAL '24h'
                GROUP BY u.email ORDER BY tok DESC LIMIT 5
            """)
            top_today = cur.fetchall()

    top_rows = "".join(
        f"<tr><td>{r['email']}</td><td>{int(r['tok']):,}</td></tr>"
        for r in top_today if r['tok'] > 0
    ) or "<tr><td colspan=2 style='color:#64748b'>Brak aktywnosci</td></tr>"

    body = f"""
    <div class="cards">
      <div class="stat-card"><div class="val">{total_users}</div><div class="lbl">Uzytkownicy</div></div>
      <div class="stat-card"><div class="val">{banned}</div><div class="lbl">Zbanowani</div></div>
      <div class="stat-card"><div class="val">{active_sessions}</div><div class="lbl">Aktywne sesje</div></div>
      <div class="stat-card"><div class="val">{int(tokens_month):,}</div><div class="lbl">Tokeny (ten miesiac)</div></div>
    </div>
    <h2 style="font-size:15px;color:#94a3b8;margin-bottom:12px">Top uzytkownicy (ostatnie 24h)</h2>
    <table style="max-width:500px">
      <tr><th>Email</th><th>Tokeny</th></tr>
      {top_rows}
    </table>
    """
    return page("Dashboard", body)


@app.get("/users", response_class=HTMLResponse)
def users_list(flash: str = ""):
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT u.id, u.email, u.role, u.is_active, u.is_banned, u.ban_reason,
                       u.totp_enabled, u.created_at, u.last_seen_at,
                       u.registration_ip, u.last_ip,
                       ul.monthly_token_limit,
                       COALESCE(SUM(t.tokens_in+t.tokens_out),0) AS tokens_month
                FROM users u
                LEFT JOIN user_limits ul ON ul.user_id=u.id
                LEFT JOIN token_usage t ON t.user_id=u.id
                    AND t.timestamp >= date_trunc('month', NOW())
                GROUP BY u.id, u.email, u.role, u.is_active, u.is_banned, u.ban_reason,
                         u.totp_enabled, u.created_at, u.last_seen_at,
                         u.registration_ip, u.last_ip, ul.monthly_token_limit
                ORDER BY u.created_at DESC
            """)
            users = [dict(r) for r in cur.fetchall()]

    rows = ""
    for u in users:
        uid = str(u["id"])
        status = '<span class="badge badge-red">Zbanowany</span>' if u["is_banned"] else \
                 '<span class="badge badge-green">Aktywny</span>'
        role = '<span class="badge badge-yellow">admin</span>' if u["role"] == "admin" else \
               '<span class="badge badge-gray">user</span>'
        totp = '<span class="badge badge-green">2FA</span>' if u["totp_enabled"] else \
               '<span class="badge badge-red">brak 2FA</span>'
        bar = pct_bar(int(u["tokens_month"] or 0), int(u["monthly_token_limit"] or 100000))
        actions = ""
        if not u["is_banned"] and u["role"] != "admin":
            actions += f'<form method="post" action="/users/{uid}/ban" style="display:inline"><input type="hidden" name="reason" value="Admin ban"><button class="btn btn-red">Ban</button></form> '
        if u["is_banned"]:
            actions += f'<form method="post" action="/users/{uid}/unban" style="display:inline"><button class="btn btn-green">Odban</button></form> '
        actions += f'<a href="/users/{uid}/sessions" class="btn btn-gray">Sesje</a> '
        actions += f'<a href="/users/{uid}/limit" class="btn btn-blue">Limit</a>'

        rows += f"""<tr>
            <td class="mono">{u['email']}</td>
            <td>{status}</td><td>{role}</td><td>{totp}</td>
            <td>{int(u['tokens_month'] or 0):,} / {int(u['monthly_token_limit'] or 0):,}<br>{bar}</td>
            <td class="mono" style="font-size:11px">{u.get('last_ip') or '—'}</td>
            <td style="font-size:11px;color:#64748b">{fmt_dt(u.get('last_seen_at'))}</td>
            <td>{actions}</td>
        </tr>"""

    body = f"""
    <table>
      <tr><th>Email</th><th>Status</th><th>Rola</th><th>2FA</th>
          <th>Tokeny (miesiac)</th><th>Ostatni IP</th><th>Ostatnio widziany</th><th>Akcje</th></tr>
      {rows}
    </table>"""
    return page("Uzytkownicy", body, flash)


@app.post("/users/{user_id}/ban")
def ban_user(user_id: str, reason: str = Form(default="Admin ban")):
    user = svc.get_user_by_id(user_id)
    if not user or user["role"] == "admin":
        raise HTTPException(403)
    svc.ban_user(user_id, reason)
    return RedirectResponse(f"/users?flash=Uzytkownik+{user['email']}+zbanowany", status_code=303)


@app.post("/users/{user_id}/unban")
def unban_user(user_id: str):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("UPDATE users SET is_banned=FALSE, ban_reason=NULL WHERE id=%s", (user_id,))
        conn.commit()
    return RedirectResponse("/users?flash=Uzytkownik+odblokowany", status_code=303)


@app.get("/users/{user_id}/limit", response_class=HTMLResponse)
def limit_form(user_id: str):
    user = svc.get_user_by_id(user_id)
    if not user: raise HTTPException(404)
    usage = get_monthly_usage(user_id)
    body = f"""
    <div class="modal-form">
      <p style="margin-bottom:16px">Uzytkownik: <strong>{user['email']}</strong><br>
      Zuzycie w tym miesiacu: <strong>{int(usage.get('used',0)):,}</strong> tokenow</p>
      <form method="post" action="/users/{user_id}/limit">
        <label>Miesięczny limit tokenów</label>
        <input type="number" name="limit" value="{usage.get('limit', 100000)}" min="0" step="10000">
        <br><br>
        <button type="submit" class="btn btn-blue">Zapisz limit</button>
        <a href="/users" class="btn btn-gray" style="margin-left:8px">Anuluj</a>
      </form>
    </div>"""
    return page(f"Limit tokenow — {user['email']}", body)


@app.post("/users/{user_id}/limit")
def set_limit(user_id: str, limit: int = Form(...)):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE user_limits SET monthly_token_limit=%s, is_blocked=FALSE WHERE user_id=%s
            """, (limit, user_id))
        conn.commit()
    return RedirectResponse(f"/users?flash=Limit+ustawiony+na+{limit:,}+tokenow", status_code=303)


@app.get("/usage", response_class=HTMLResponse)
def usage_page():
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT u.email,
                       COALESCE(SUM(t.tokens_in+t.tokens_out),0) AS total,
                       COALESCE(SUM(t.tokens_in),0)              AS inp,
                       COALESCE(SUM(t.tokens_out),0)             AS out,
                       COALESCE(COUNT(t.id),0)                   AS calls,
                       ul.monthly_token_limit, ul.is_blocked
                FROM users u
                LEFT JOIN token_usage t ON t.user_id=u.id
                    AND t.timestamp >= date_trunc('month', NOW())
                LEFT JOIN user_limits ul ON ul.user_id=u.id
                GROUP BY u.email, ul.monthly_token_limit, ul.is_blocked
                ORDER BY total DESC
            """)
            stats = [dict(r) for r in cur.fetchall()]

            cur.execute("""
                SELECT endpoint,
                       SUM(tokens_in+tokens_out) AS total,
                       COUNT(*) AS calls
                FROM token_usage
                WHERE timestamp >= date_trunc('month', NOW())
                GROUP BY endpoint ORDER BY total DESC
            """)
            by_endpoint = [dict(r) for r in cur.fetchall()]

    rows = ""
    for s in stats:
        blocked = '<span class="badge badge-red">ZABLOKOWANY</span>' if s["is_blocked"] else ""
        bar = pct_bar(int(s["total"]), int(s["monthly_token_limit"] or 100000))
        rows += f"""<tr>
            <td class="mono">{s['email']}</td>
            <td>{int(s['total']):,} {blocked}</td>
            <td>{int(s['inp']):,}</td>
            <td>{int(s['out']):,}</td>
            <td>{int(s['calls'])}</td>
            <td>{int(s['monthly_token_limit'] or 0):,}</td>
            <td>{bar}</td>
        </tr>"""

    ep_rows = "".join(
        f"<tr><td>{e['endpoint']}</td><td>{int(e['total']):,}</td><td>{int(e['calls'])}</td></tr>"
        for e in by_endpoint
    )

    body = f"""
    <h2 style="font-size:15px;color:#94a3b8;margin-bottom:12px">Per uzytkownik (biezacy miesiac)</h2>
    <table style="margin-bottom:32px">
      <tr><th>Email</th><th>Tokeny razem</th><th>Input</th><th>Output</th><th>Wywolania</th><th>Limit</th><th>Wykorz.</th></tr>
      {rows}
    </table>
    <h2 style="font-size:15px;color:#94a3b8;margin-bottom:12px">Per endpoint</h2>
    <table style="max-width:500px">
      <tr><th>Endpoint</th><th>Tokeny</th><th>Wywolania</th></tr>
      {ep_rows}
    </table>"""
    return page("Zuzycie tokenow", body)


@app.get("/sessions", response_class=HTMLResponse)
def sessions_page():
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT s.id, u.email, s.ip, s.user_agent,
                       s.created_at, s.last_active_at, s.expires_at,
                       s.revoked, s.revoked_reason
                FROM sessions s
                JOIN users u ON u.id=s.user_id
                ORDER BY s.last_active_at DESC NULLS LAST
                LIMIT 100
            """)
            sessions = [dict(r) for r in cur.fetchall()]

    rows = ""
    for s in sessions:
        status = '<span class="badge badge-red">Uniewazniona</span>' if s["revoked"] else \
                 '<span class="badge badge-green">Aktywna</span>'
        ua = (s.get("user_agent") or "")[:60] + ("..." if len(s.get("user_agent") or "") > 60 else "")
        kill_btn = "" if s["revoked"] else \
            f'<form method="post" action="/sessions/{str(s["id"])}/revoke" style="display:inline"><button class="btn btn-red">Uniewaznij</button></form>'
        rows += f"""<tr>
            <td class="mono" style="font-size:12px">{s['email']}</td>
            <td>{status}</td>
            <td class="mono">{s.get('ip') or '—'}</td>
            <td style="font-size:11px;color:#64748b;max-width:200px;overflow:hidden">{ua}</td>
            <td style="font-size:11px;color:#64748b">{fmt_dt(s.get('last_active_at'))}</td>
            <td style="font-size:11px;color:#64748b">{fmt_dt(s.get('expires_at'))}</td>
            <td>{kill_btn}</td>
        </tr>"""

    body = f"""
    <table>
      <tr><th>Email</th><th>Status</th><th>IP</th><th>User Agent</th>
          <th>Ostatnia aktywnosc</th><th>Wygasa</th><th>Akcja</th></tr>
      {rows}
    </table>"""
    return page("Sesje", body)


@app.get("/users/{user_id}/sessions", response_class=HTMLResponse)
def user_sessions(user_id: str):
    user = svc.get_user_by_id(user_id)
    if not user: raise HTTPException(404)
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT id, ip, user_agent, created_at, last_active_at,
                       expires_at, revoked, revoked_reason
                FROM sessions WHERE user_id=%s ORDER BY created_at DESC
            """, (user_id,))
            sessions = [dict(r) for r in cur.fetchall()]

    rows = ""
    for s in sessions:
        status = '<span class="badge badge-red">Uniewazniona</span>' if s["revoked"] else \
                 '<span class="badge badge-green">Aktywna</span>'
        rows += f"""<tr>
            <td>{status}</td>
            <td class="mono">{s.get('ip') or '—'}</td>
            <td style="font-size:11px;color:#64748b">{fmt_dt(s.get('created_at'))}</td>
            <td style="font-size:11px;color:#64748b">{fmt_dt(s.get('last_active_at'))}</td>
            <td style="font-size:11px;color:#64748b">{s.get('revoked_reason') or '—'}</td>
        </tr>"""

    kill_all = f'<form method="post" action="/users/{user_id}/sessions/revoke-all" style="margin-bottom:16px"><button class="btn btn-red">Uniewaznij wszystkie sesje</button></form>'
    body = f"""
    <p style="margin-bottom:16px;color:#94a3b8">Uzytkownik: <strong style="color:#f1f5f9">{user['email']}</strong></p>
    {kill_all}
    <table>
      <tr><th>Status</th><th>IP</th><th>Utworzona</th><th>Ostatnia aktywnosc</th><th>Powod unieaznienia</th></tr>
      {rows}
    </table>"""
    return page(f"Sesje — {user['email']}", body)


@app.post("/users/{user_id}/sessions/revoke-all")
def revoke_all_sessions(user_id: str):
    svc.revoke_all_user_sessions(user_id, "admin_revoke")
    return RedirectResponse(f"/users/{user_id}/sessions?flash=Sesje+uniewaznione", status_code=303)


@app.post("/sessions/{session_id}/revoke")
def revoke_session(session_id: str):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE sessions SET revoked=TRUE, revoked_at=NOW(), revoked_reason='admin_revoke'
                WHERE id=%s
            """, (session_id,))
        conn.commit()
    return RedirectResponse("/sessions?flash=Sesja+uniewazniona", status_code=303)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)