# Chat Widget — plan implementacji

## Cel
Pływający widget czatu dostępny na każdej podstronie aplikacji.
Mały przycisk w prawym dolnym rogu → kliknięcie rozwija panel czatu → użytkownik może pytać agenta AI.

---

## Backend

### Nowy endpoint: `POST /api/agent/chat`
- Plik: `backend/routers/agent.py` (dodaj nową trasę)
- Plik: `backend/services/agent_service.py` (dodaj nową funkcję)

**Przyjmuje:**
```json
{
  "message": "treść wiadomości od użytkownika",
  "history": [
    { "role": "user", "content": "..." },
    { "role": "assistant", "content": "..." }
  ],
  "context": {
    "page": "overview",
    "tickers": ["AAPL", "MSFT"]
  }
}
```

**Zwraca (streaming SSE):**
- Odpowiedź modelu jako strumień tokenów (Server-Sent Events)
- FastAPI: użyj `StreamingResponse` z `media_type="text/event-stream"`
- OpenRouter: w `client.chat.completions.create(...)` dodaj `stream=True`

**System prompt do napisania:**
- Model ma wiedzieć że jest asystentem finansowym
- Dostaje w prompcie kontekst strony (np. `"Użytkownik aktualnie ogląda stronę Overview ze spółkami: AAPL, MSFT"`)
- Powinien odpowiadać po polsku

---

## Frontend

### Nowy plik: `src/components/ChatWidget.tsx`

**Stany komponentu:**
- `isOpen: boolean` — czy panel jest rozwinięty
- `messages: { role: "user"|"assistant", content: string }[]` — historia rozmowy
- `input: string` — aktualna wiadomość użytkownika
- `isLoading: boolean` — czy czeka na odpowiedź

**Struktura wizualna:**
```
[zamknięty]
  └── przycisk FAB (fixed, bottom-right) z ikoną czatu

[otwarty]
  └── panel (fixed, bottom-right, ~380px szerokości, ~500px wysokości)
      ├── header: "Asystent AI"  [x]
      ├── lista wiadomości (scrollowalna)
      │    ├── wiadomość użytkownika (wyrównana do prawej)
      │    └── wiadomość asystenta (wyrównana do lewej)
      └── input + przycisk "Wyślij"
```

**Obsługa streamingu:**
- Użyj `fetch()` z `response.body.getReader()` do czytania SSE
- Każdy token doklejaj do ostatniej wiadomości asystenta w stanie `messages`
- Daje efekt pisania na żywo

### Modyfikacja: `src/App.tsx`
- Zaimportuj `ChatWidget`
- Umieść **poza** `<main>` — np. tuż przed zamknięciem głównego `<div>`
- Przekaż jako prop aktualną stronę: `<ChatWidget currentPage={page} />`

### Kontekst strony
Każda podstrona powinna przekazywać do widgetu relevantne dane.
Możliwe podejścia:
- **Props drilling** — `App.tsx` trzyma stan aktywnych tickerów i przekazuje do `ChatWidget`
- **React Context** — lepsze jeśli zależy ci na czystości kodu, ale więcej roboty

Na start wystarczy przekazać samą nazwę strony (`currentPage`), a tickery można dołożyć później.

---

## Kolejność roboty

- [ ] 1. Backend: funkcja `chat_with_agent(message, history, context)` w `agent_service.py`
- [ ] 2. Backend: endpoint `POST /api/agent/chat` ze streamingiem w `agent.py`
- [ ] 3. Backend: przetestuj endpoint przez curl/Postman że streaming działa
- [ ] 4. Frontend: stwórz `ChatWidget.tsx` bez streamingu (najpierw zwykły fetch)
- [ ] 5. Frontend: dodaj widget do `App.tsx`, sprawdź że się otwiera/zamyka
- [ ] 6. Frontend: podmień fetch na streaming (ReadableStream)
- [ ] 7. Frontend: przekaż kontekst strony do widgetu i do backendu

---

## Rzeczy do przemyślenia

- **Reset historii** — czy historia rozmowy kasuje się przy przejściu na inną stronę, czy trwa przez całą sesję?
- **Limit historii** — OpenRouter liczy tokeny, warto przycinać historię do ostatnich np. 10 wiadomości
- **Błędy streamingu** — co wyświetlić użytkownikowi gdy API padnie w połowie odpowiedzi?
- **Model** — obecny `nvidia/nemotron` jest darmowy, ale może być wolny przy czacie; rozważ `openai/gpt-4o-mini` (tani) lub `anthropic/claude-haiku-4-5` (szybki)
