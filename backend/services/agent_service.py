import os
import time
import feedparser
import requests
from bs4 import BeautifulSoup
from openai import OpenAI
from dotenv import load_dotenv
# przyspieszanie aplikacji
import asyncio
import httpx
from datetime import datetime, timedelta


load_dotenv()

RSS_GEOPOLITYKA = [
    "https://feeds.a.dj.com/rss/RSSWorldNews.xml",
    "https://news.yahoo.com/rss/world",
    "https://www.aljazeera.com/xml/rss/all.xml"
]

def _get_client():
    return OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=os.getenv("OPENROUTER_API_KEY", "")
    )

async def _pobierz_tekst(url: str) -> str:
    async with httpx.AsyncClient() as client:
        try:
            r = await client.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
            if r.status_code == 200:
                soup = BeautifulSoup(r.text, 'html.parser')
                tekst = " ".join(p.get_text() for p in soup.find_all('p'))
                return tekst[:2500] + " [...]" if len(tekst) > 100 else "Brak tekstu."
            return f"Błąd: {r.status_code}"
        except Exception as e:
            return f"Błąd: {e}"

def _analizuj_ai(surowe_dane: str, instrukcja: str) -> str:
    try:
        # Zabezpieczenie 1: Sprawdzenie klucza
        klucz = os.getenv("OPENROUTER_API_KEY", "")
        if not klucz:
            return "Błąd: Brak klucza OPENROUTER_API_KEY w pliku .env!"

        response = _get_client().chat.completions.create(
            model="nvidia/nemotron-3-super-120b-a12b:free",
            messages=[
                {"role": "system", "content": instrukcja},
                {"role": "user", "content": surowe_dane}
            ]
        )
        
        # Zabezpieczenie 2: Ochrona przed pustą odpowiedzią OpenRoutera
        if not response or not hasattr(response, 'choices') or not response.choices:
            return "Błąd API OpenRouter: Serwer zwrócił pustą odpowiedź (model może być przeciążony)."

        return response.choices[0].message.content
        
    except Exception as e:
        return f"Błąd AI: {e}"


# do cachowania by nie musiec pobierac co chwila tego samego
GEO_CACHE = {
    "data": None,
    "expiry": None
}

async def get_geopolitics() -> str:
    # Sprawdź czy mamy ważny cache
    now = datetime.now()
    if GEO_CACHE["data"] and GEO_CACHE["expiry"] > now:
        print("[cache] Zwracam dane z pamięci (ważne do: {})".format(GEO_CACHE["expiry"]))
        return GEO_CACHE["data"]

    # Jeśli nie ma cache, budujemy raport (Twoja oryginalna logika asynchroniczna)
    print("[agent] Cache wygasł lub brak danych. Pobieram nowe dane z RSS...")
    raport = ""
    for url_rss in RSS_GEOPOLITYKA:
        feed = feedparser.parse(url_rss)
        tytul = feed.feed.title if hasattr(feed.feed, 'title') else url_rss
        raport += f"--- {tytul} ---\n"

        # Pobieranie treści 3 newsów naraz
        tasks = [_pobierz_tekst(entry.link) for entry in feed.entries[:3]]
        tresci = await asyncio.gather(*tasks)

        for entry, tresc in zip(feed.entries[:3], tresci):
            raport += f"TYTUŁ: {entry.title}\nLINK: {entry.link}\nTREŚĆ: {tresc}\n---\n"

    instrukcja = """Jesteś analitykiem makro. Wypunktuj wszystkie wiadomości dotyczące
geopolityki, gospodarki, rynków, wojen, ceł lub surowców.

Format dla każdego wydarzenia:
🌍 [TEMAT/REGION]
- Fakt: [krótki konkret]
- Cytat: "[cytat]" lub "Brak cytatów"
- Źródło: [link]

Bez wstępów i podsumowań."""

    # Wywołanie AI
    wynik_finalny = _analizuj_ai(raport, instrukcja)

    #  Zapisz wynik do cache na 15 minut
    GEO_CACHE["data"] = wynik_finalny
    GEO_CACHE["expiry"] = now + timedelta(minutes=15)

    return wynik_finalny

async def get_stocks(tickers: list[str]) -> str:
    tickers = tickers[:10]
    raport = ""
    for ticker in tickers:
        url_rss = f"https://feeds.finance.yahoo.com/rss/2.0/headline?s={ticker}&region=US&lang=en-US"
        feed = feedparser.parse(url_rss)
        raport += f"--- {ticker} ---\n"
        if not feed.entries:
            raport += "Brak wiadomości.\n\n"
            continue

        #  Tutaj też pobieramy 2 newsy naraz (asynchronicznie) dla przyspieszenia
        tasks = [_pobierz_tekst(entry.link) for entry in feed.entries[:2]]
        tresci = await asyncio.gather(*tasks)

        for entry, tresc in zip(feed.entries[:2], tresci):
            raport += f"LINK: {entry.link}\nTREŚĆ: {tresc}\n---\n"
        raport += "\n"

    instrukcja = """Jesteś analitykiem rynku. Dla każdej spółki wyciągnij twarde fakty.
Ignoruj spółki z "Brak wiadomości".

Format dla każdej spółki:
🏢 [TICKER]
- Fakt: [najważniejszy konkret]
- Cytat: "[cytat]" - [kto] lub "Brak cytatów"
- Źródło: [link]

Bez wstępów i podsumowań."""

    return _analizuj_ai(raport, instrukcja)