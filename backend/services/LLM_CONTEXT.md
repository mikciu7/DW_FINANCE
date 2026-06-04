# Co dokładnie dostaje LLM przy każdym zapytaniu

## Struktura wiadomości wysyłanych do OpenAI

```
messages = [
    { role: "system",    content: SYSTEM_PROMPT },        ← stały, przy każdym zapytaniu
    { role: "user",      content: historia[0] },           ← poprzednie wiadomości
    { role: "assistant", content: historia[1] },
    { role: "tool",      content: wynik_narzedzia },       ← wyniki tool calls z poprzednich tur
    ...
    { role: "user",      content: KONTEKST + PYTANIE },    ← aktualne zapytanie
]
```

---

## 1. SYSTEM PROMPT (stały)

```
Jestes asystentem finansowym aplikacji NeoEye.
Masz dostep do narzedzi pobierajacych dane z bazy. Kiedy uzytkownik pyta o dane, ZAWSZE uzyj narzedzia.
Odpowiadaj zwiezle i konkretnie, w jezyku polskim.

DOSTEPNE KOLUMNY:
  get_financials: revenue, operating_income, net_income, ...
  get_macro_data: sp500, cpiaucsl, unrate, gdpc1, ...
```

**Problem:** Za krótki. Nie wyjaśnia:
- Czym jest NeoEye
- Kiedy używać którego narzędzia
- Że context = widok usera, ale user może pytać o wszystko
- Że dane finansowe są kwartalne (nie miesięczne!)
- Kiedy NIE pobierać danych (pytania o kontekst)

---

## 2. USER MESSAGE (każde zapytanie)

```
[KONTEKST WIDOKU]
Użytkownik aktualnie przegląda zakładkę: **Raporty Finansowe**.
Wybrane spółki: MSFT.
Aktywna sekcja: Income Statement.
Wybrany wskaźnik na wykresie: Revenue (revenue).
Zakres dat: 2009-09-30 – 2026-03-31.
Aktualnie wybrany snapshot danych makro (file_date): 2026-06-01.   ← BUG: wysyłany nawet nie na zakładce Makro

[PYTANIE UŻYTKOWNIKA]
ej a zobacz że microsoft w 2025 w maju nie miał spadków
```

**Problem:** `file_date` jest wysyłany zawsze → LLM myśli że zawsze ma używać `get_macro_data`.

---

## 3. TOOLS (dostępne narzędzia)

| Narzędzie | Do czego | Problem |
|---|---|---|
| `get_financials` | Dane finansowe (revenue, net_income...) | OK, ma filtrowanie |
| `get_features` | Wskaźniki ML (pe_ratio, roe...) | OK |
| `get_prices` | Ceny akcji (daily OHLCV) | OK, wymaga dat |
| `get_macro_data` | Dane FRED (sp500, GDP, CPI...) | Brakuje kolumn w opisie |
| `get_latest_features` | Najnowsze wskaźniki | OK |
| `get_latest_financial_date` | Ostatnia data raportu | OK |
| `get_latest_price_date` | Ostatnia data ceny | OK |
| `get_available_file_dates` | Daty snapshotów FRED | Zwraca listę dat, małe dane |

---

## 4. OBECNE BUGI

1. **LLM pobiera sp500 zamiast danych MSFT** — bo `file_date` jest w kontekście → LLM myśli że ma fetować makro
2. **"co teraz widzisz?"** → LLM pobierał 6225 rekordów — nie powinien nic fetować przy pytaniach o kontekst
3. **"revenue w maju 2025"** → dane finansowe są kwartalne, nie miesięczne — LLM tego nie wie
4. **System prompt nie wyjaśnia architektury danych** → LLM nie wie kiedy użyć którego narzędzia

---

## 5. DOCELOWY SYSTEM PROMPT

Patrz: sekcja "Nowy system prompt" poniżej.