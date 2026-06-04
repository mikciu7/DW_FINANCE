# Co dokładnie dostaje LLM przy każdym zapytaniu

## Ogólna struktura wiadomości

```
messages = [
    { role: "system",    content: SYSTEM_PROMPT },         ← stały przy każdym zapytaniu
    { role: "user",      content: poprzednie pytanie },    ⎤
    { role: "assistant", content: poprzednia odpowiedź },  ⎥ historia rozmowy
    { role: "tool",      content: wynik narzędzia },       ⎦ (pełna, bez przycinania)
    ...
    { role: "user",      content: KONTEKST + PYTANIE },    ← aktualne zapytanie
]
+ tools: [...definicje narzędzi...]
```

---

## 1. SYSTEM PROMPT

Wysyłany zawsze jako pierwsza wiadomość. Zawiera:

### a) Opis aplikacji
Wyjaśnia czym jest NeoEye, jakie ma zakładki i jaki typ danych w każdej.

### b) Instrukcja użycia kontekstu
Informuje LLM że `[KONTEKST WIDOKU]` = co user aktualnie ogląda, ale user może pytać o cokolwiek.

### c) Zasady wyboru narzędzi
```
ceny akcji          → get_prices
dane finansowe      → get_financials
wskaźniki/metryki   → get_features
makroekonomia/FRED  → get_macro_data
pytanie o kontekst  → NIE fetuj, opisz z kontekstu
```

### d) Ważne reguły
- Dane finansowe są **KWARTALNE** (nie miesięczne)
- Ceny akcji są **DZIENNE**
- Dane FRED mają różną częstotliwość (dzienne/miesięczne/kwartalne)
- Zawsze filtruj `columns` i daty
- `file_date` dotyczy TYLKO `get_macro_data`

### e) Mapa kolumn
Pełna lista nazw kolumn dla każdego narzędzia żeby LLM wiedział jaką nazwę podać w `columns=[]`.

---

## 2. KONTEKST WIDOKU (per zapytanie)

Budowany dynamicznie przez `_build_context_prefix()` z obiektu `ChatContext`.

### Pola zawsze obecne
```
Użytkownik aktualnie przegląda zakładkę: **{page}**.
```

### Pola warunkowe
| Pole | Kiedy wysyłane | Przykład |
|---|---|---|
| `tickers` | gdy wybrana ≥1 spółka | `Wybrane spółki: MSFT, AAPL.` |
| `tab` | gdy wybrana zakładka w Financials | `Aktywna sekcja: Income Statement.` |
| `metric` + `metricLabel` | gdy wybrany wskaźnik na wykresie | `Wybrany wskaźnik: Revenue (revenue).` |
| `dateRange` | gdy ustawiony zakres dat | `Zakres dat: 2020-01-01 – 2026-03-31.` |
| `macro_metrics` | **tylko na zakładce Makro** | `Wybrane wskaźniki makro: gdpc1, sp500.` |
| `fileDate` | **tylko na zakładce Makro** | `Snapshot FRED (file_date): 2026-06-01.` |

### Przykład — Raporty Finansowe
```
[KONTEKST WIDOKU]
Użytkownik aktualnie przegląda zakładkę: **Raporty Finansowe**.
Wybrane spółki: MSFT.
Aktywna sekcja: Income Statement.
Wybrany wskaźnik na wykresie: Revenue (revenue).
Zakres dat: 2009-09-30 – 2026-03-31.

[PYTANIE UŻYTKOWNIKA]
Jak wyglądało revenue w Q2 2025?
```

### Przykład — Zmienne Makroekonomiczne
```
[KONTEKST WIDOKU]
Użytkownik aktualnie przegląda zakładkę: **Zmienne Makroekonomiczne**.
Wybrany wskaźnik na wykresie: Real GDP (gdpc1).
Zakres dat: 2001-04-01 – 2026-05-29.
Wybrane wskaźniki makro: gdpc1, sp500.
Snapshot FRED (file_date): 2026-06-01.

[PYTANIE UŻYTKOWNIKA]
Jaka była wartość sp500 w maju 2025?
```

### Przykład — Ceny Akcji
```
[KONTEKST WIDOKU]
Użytkownik aktualnie przegląda zakładkę: **Ceny Akcji**.
Wybrane spółki: AAPL, NVDA.
Zakres dat: 2022-01-01 – 2026-06-01.

[PYTANIE UŻYTKOWNIKA]
Która spółka miała większy wzrost w 2023?
```

---

## 3. NARZĘDZIA (tools)

| Narzędzie | Parametry | Zwraca | Uwagi |
|---|---|---|---|
| `get_financials` | `ticker`, `columns[]`, `start_date`, `end_date` | lista wierszy kwartalnych | ZAWSZE filtruj |
| `get_features` | `ticker`, `columns[]`, `start_date`, `end_date` | lista wskaźników kwartalnych | ZAWSZE filtruj |
| `get_prices` | `ticker`, `start_date`, `end_date` | lista cen dziennych | ZAWSZE podaj daty |
| `get_macro_data` | `file_date`, `columns[]`, `start_date`, `end_date` | dane FRED | ZAWSZE filtruj |
| `get_latest_features` | `ticker` | 1 wiersz (najnowszy) | Do szybkiego podglądu |
| `get_latest_financial_date` | `ticker` | data string | |
| `get_latest_price_date` | `ticker` | data string | |
| `get_available_file_dates` | — | lista dat snapshotów | |

### Twarda granica rozmiaru wyniku
Każdy wynik narzędzia jest przycinany do **40 000 znaków** (~10k tokenów).
Dla list: max **100 wierszy**, reszta obcięta z komunikatem.

---

## 4. ChatContext — model danych (backend)

```python
class ChatContext(BaseModel):
    page: str                    # nazwa zakładki, np. "Raporty Finansowe"
    tickers: list[str] = []      # wybrane spółki, np. ["MSFT", "AAPL"]
    metric: str | None = None    # klucz kolumny, np. "revenue"
    metric_label: str | None = None  # czytelna nazwa, np. "Revenue"
    tab: str | None = None       # zakładka w Financials, np. "Income Statement"
    date_range: dict | None = None   # {"start": "2020-01-01", "end": "2026-03-31"}
    macro_metrics: list[str] = []    # wybrane metryki FRED, np. ["gdpc1", "sp500"]
    fileDate: str | None = None      # snapshot FRED, np. "2026-06-01"
```

---

## 5. Gdzie co jest w kodzie

| Co | Plik |
|---|---|
| System prompt + `_build_context_prefix` | `backend/services/new_agent_service.py` |
| Definicje narzędzi + TOOL_MAPPING | `backend/services/tools.py` |
| Implementacje narzędzi | `backend/services/edgar_service.py`, `feature_service.py`, `price_service.py`, `fred_service.py` |
| ChatContext model | `backend/services/new_agent_service.py` |
| Router `/api/agent/chat` | `backend/routers/agent.py` |
| Frontend — wysyłanie kontekstu | `frontend/src/components/ChatWidget.tsx` |
| Frontend — budowanie ViewState | `frontend/src/context/ViewContext.tsx` |
| Zakładki ustawiające ViewState | `Overview.tsx`, `Financials.tsx`, `Features.tsx`, `Macro.tsx` |