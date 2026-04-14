import os
import time
import feedparser
import requests
from bs4 import BeautifulSoup
from openai import OpenAI
from dotenv import load_dotenv

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

def _pobierz_tekst(url: str) -> str:
    try:
        r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
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

def get_geopolitics() -> str:
    raport = ""
    for url_rss in RSS_GEOPOLITYKA:
        feed = feedparser.parse(url_rss)
        tytul = feed.feed.title if hasattr(feed.feed, 'title') else url_rss
        raport += f"--- {tytul} ---\n"
        for entry in feed.entries[:3]:
            tresc = _pobierz_tekst(entry.link)
            raport += f"TYTUŁ: {entry.title}\nLINK: {entry.link}\nTREŚĆ: {tresc}\n---\n"

    instrukcja = """Jesteś analitykiem makro. Wypunktuj wszystkie wiadomości dotyczące
geopolityki, gospodarki, rynków, wojen, ceł lub surowców.

Format dla każdego wydarzenia:
🌍 [TEMAT/REGION]
- Fakt: [krótki konkret]
- Cytat: "[cytat]" lub "Brak cytatów"
- Źródło: [link]

Bez wstępów i podsumowań."""

    return _analizuj_ai(raport, instrukcja)

def get_stocks(tickers: list[str]) -> str:
    tickers = tickers[:10]
    raport = ""
    for ticker in tickers:
        url_rss = f"https://feeds.finance.yahoo.com/rss/2.0/headline?s={ticker}&region=US&lang=en-US"
        feed = feedparser.parse(url_rss)
        raport += f"--- {ticker} ---\n"
        if not feed.entries:
            raport += "Brak wiadomości.\n\n"
            continue
        for entry in feed.entries[:2]:
            tresc = _pobierz_tekst(entry.link)
            raport += f"LINK: {entry.link}\nTREŚĆ: {tresc}\n---\n"
        raport += "\n"
        time.sleep(1)

    instrukcja = """Jesteś analitykiem rynku. Dla każdej spółki wyciągnij twarde fakty.
Ignoruj spółki z "Brak wiadomości".

Format dla każdej spółki:
🏢 [TICKER]
- Fakt: [najważniejszy konkret]
- Cytat: "[cytat]" - [kto] lub "Brak cytatów"
- Źródło: [link]

Bez wstępów i podsumowań."""

    return _analizuj_ai(raport, instrukcja)