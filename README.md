# NeoEye — Platforma Analizy Giełdowej

Aplikacja webowa do analizy fundamentalnej spółek giełdowych z asystentem AI, modelem predykcji ML i danymi makroekonomicznymi.

---

## Spółki

AAPL · AMZN · AVGO · GOOG · META · MSFT · NVDA · ORCL · TSLA · AMD

---

## Funkcjonalności

### Zakładki

| Zakładka | Co zawiera |
|---|---|
| **Ceny Akcji** | Historyczne kursy dzienne, porównanie wielu spółek na jednym wykresie, delta % |
| **Raporty Finansowe** | Dane kwartalne z 10-K/10-Q: P&L, bilans, cash flow — wykres + tabela, multi-select spółek |
| **Features** | ~60 wyliczonych wskaźników (marże, wzrosty, momentum, P/E, z-score) z opisami po polsku |
| **Model ML** | Predykcje zwrotów akcji (Random Forest), feature importance, metryki modelu |
| **Zmienne Makro** | Dane FRED: GDP, inflacja (CPI), stopy procentowe, bezrobocie, S&P500, ceny ropy, kursy walut |
| **Asystent AI** | Chat z agentem który widzi co aktualnie ogląda użytkownik |

### Asystent AI

- Widzi aktualny kontekst: zakładka, wybrane spółki, wskaźnik, zakres dat
- Pobiera dane z bazy na żądanie (ceny, finanse, wskaźniki, makro)
- Czyta pełne raporty 10-K/10-Q z EDGAR (MD&A, business, ryzyka) — pyta o zgodę przed kosztownym wywołaniem
- Informuje o obcięciu tekstu i oferuje pełną wersję
- Rozumie że dane finansowe są kwartalne, ceny dzienne

### Bezpieczeństwo

- Sesje serwerowe w PostgreSQL — natychmiastowy ban = DELETE sesji
- Hasła: Argon2id (64MB RAM, 3 iteracje)
- 2FA TOTP obowiązkowe (Google Authenticator / Authy)
- TOTP secret szyfrowany AES-256-GCM w bazie
- Rate limiting: 5 prób logowania / 15 min per IP, 3 rejestracje / h per IP
- IP tracking: max 3 konta per IP
- Monitoring tokenów LLM: limit miesięczny per user, auto-blokada przy przekroczeniu

### Panel Admina

Dostępny **tylko przez SSH tunnel** (nie wystawiony na internet):

```bash
ssh -L 8080:localhost:8080 -i klucz.pem ubuntu@EC2_IP
# Potem: http://localhost:8080
```

Widoki: Dashboard · Użytkownicy (ban/unban/limit) · Zużycie tokenów · Sesje

---

## Architektura

```
Internet → nginx (port 80)
              ├── /        → React SPA
              ├── /api/*   → FastAPI backend (port 8000)
              ├── /auth/*  → Auth endpoints
              └── /admin/* → Admin API

localhost:8080 → Admin panel (tylko SSH tunnel)

FastAPI → PostgreSQL (AWS RDS)
       → OpenAI API (gpt-4o-mini)
       → SEC EDGAR (edgartools)
       → yfinance (ceny akcji)
       → FRED (dane makro)
```

### Stack

| Warstwa | Technologia |
|---|---|
| Frontend | React 19 + TypeScript + Vite + Recharts + TailwindCSS |
| Backend | Python 3.11 + FastAPI + uvicorn (4 workers) |
| Baza danych | PostgreSQL (AWS RDS) |
| Deployment | Docker Compose na AWS EC2 Ubuntu |
| Auth | Sesje serwerowe + Argon2id + TOTP |
| AI | OpenAI gpt-4o-mini + tool calling |
| ML | scikit-learn Random Forest |

---

## Tabele w bazie

| Tabela | Zawartość |
|---|---|
| `prices` | Dzienne ceny akcji (OHLCV) |
| `financials` | Kwartalne dane finansowe z 10-K/10-Q |
| `features` | ~60 wskaźników per spółka per kwartał |
| `predictions` | Predykcje ML zwrotów |
| `model_metrics` | Metryki modelu (R², MAE, hit rate) |
| `macro_data` | Dane FRED (dzienne/miesięczne/kwartalne) |
| `users` | Konta użytkowników |
| `sessions` | Sesje serwerowe |
| `token_usage` | Zużycie tokenów LLM per user |
| `user_limits` | Miesięczne limity tokenów per user |
| `login_attempts` | Historia prób logowania |
| `verification_tokens` | Tokeny jednorazowe (2FA pending) |

---

## Deployment

### Zmienne środowiskowe `.env`

```env
DB_HOST=...
DB_NAME=...
DB_USER=...
DB_PASS=...
DB_PORT=5432
OPENAI_API_KEY=...
SESSION_SECRET=<64 bytes hex>        # python -c "import secrets; print(secrets.token_hex(64))"
TOTP_ENCRYPTION_KEY=<32 bytes hex>   # python -c "import secrets; print(secrets.token_hex(32))"
ADMIN_EMAIL=...
ADMIN_PASSWORD=...
```

### Pierwsze uruchomienie

```bash
git clone ... && cd DW_FINANCE
cp .env.example .env && nano .env
docker-compose up --build -d
docker-compose exec backend python -m backend.migrate_auth
```

### Update

```bash
git pull
docker-compose stop backend frontend && docker-compose rm -f backend frontend
docker-compose up --build -d backend frontend
```

---

## Checklist przed pokazaniem projektu

### Krytyczne

- [ ] `SESSION_SECRET` i `TOTP_ENCRYPTION_KEY` w `.env` nie są `CHANGE_ME`
- [ ] `ADMIN_EMAIL` i `ADMIN_PASSWORD` ustawione
- [ ] Migracja auth uruchomiona: `docker-compose exec backend python -m backend.migrate_auth`
- [ ] Czas serwera zsynchronizowany (wymagane dla TOTP): `sudo timedatectl set-ntp true`
- [ ] Aplikacja dostępna pod EC2 IP na porcie 80
- [ ] Rejestracja działa i 2FA setup działa
- [ ] Logowanie z kodem TOTP działa
- [ ] Chat z agentem odpowiada
- [ ] Admin panel dostępny przez SSH tunnel na `localhost:8080`

### Dane

- [ ] Ceny akcji załadowane (wykres w "Ceny Akcji")
- [ ] Dane finansowe załadowane ("Raporty Finansowe")
- [ ] Features wyliczone ("Features" — wykresy widoczne)
- [ ] Dane FRED załadowane ("Zmienne Makro")
- [ ] Model ML wytrenowany (`stock_prediction_model.pkl` istnieje w kontenerze)

### Dysk EC2

```bash
df -h                  # powinno być >20% wolnego miejsca
docker system df       # rozmiar obrazów Docker
docker system prune -a # wyczyść nieużywane obrazy jeśli mało miejsca
```

### Test agenta — co zapytać

```
"Hej, co teraz widzisz?"                          → opis kontekstu bez tool call
"Jaka była wartość sp500 w maju 2025?"             → get_macro_data z filtrami
"Jak wyglądało revenue MSFT w Q2 2025?"            → get_financials z datami
"Jakie są plany NVDA na przyszłość?"               → pyta o zgodę, potem get_filing_text
"Porównaj marże AAPL i MSFT w ostatnim roku"       → 2x get_features równolegle
```

---

## Znane ograniczenia

| Ograniczenie | Opis |
|---|---|
| EPS historyczny | Dane przed splitami akcji nie są korygowane automatycznie |
| `get_filing_text` | Pobieranie 5-15 sek, tylko spółki US-listed notowane na EDGAR |
| Model ML | Demonstracyjny, nie produkcyjny |
| Tokeny OpenAI | Limit org: 200k TPM. Długie rozmowy z dużymi danymi mogą przekroczyć |
| Reset hasła | Wyłączony celowo — utrata hasła = nowe konto |
| 2FA sync | Czas serwera musi być zgodny z NTP, inaczej kody TOTP są odrzucane |

---

## Pliki konfiguracyjne

| Plik | Opis |
|---|---|
| `docker-compose.yml` | Serwisy: backend, frontend, admin |
| `frontend/nginx.conf` | Routing `/api/*`, `/auth/*`, `/admin/*` do backendu |
| `backend/services/LLM_CONTEXT.md` | Dokumentacja kontekstu agenta AI |
| `.env` | Zmienne środowiskowe (nie commitować!) |