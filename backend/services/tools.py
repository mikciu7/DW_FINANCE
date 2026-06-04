from backend.services.edgar_service import get_financials, get_latest_financial_date
from backend.services.feature_service import get_features, get_latest_features
from backend.services.price_service import get_prices, get_latest_price_date
from backend.services.fred_service import get_available_file_dates, get_macro_data
from backend.services.filing_service import get_filing_text

tools = [
    {
        "type": "function",
        "function": {
            "name": "get_financials",
            "description": "Pobiera dane finansowe spółki (bilans, rachunek wyników, przepływy pieniężne) z bazy danych. Używaj columns i dat żeby ograniczyć ilość danych.",
            "parameters": {
                "type": "object",
                "properties": {
                    "ticker": {
                        "type": "string",
                        "description": "Symbol giełdowy spółki, np. AAPL, MSFT."
                    },
                    "columns": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Lista kolumn do zwrócenia, np. ['revenue', 'net_income']. Pomiń aby zwrócić wszystkie."
                    },
                    "start_date": {
                        "type": "string",
                        "description": "Data początkowa w formacie YYYY-MM-DD."
                    },
                    "end_date": {
                        "type": "string",
                        "description": "Data końcowa w formacie YYYY-MM-DD."
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_latest_financial_date",
            "description": "Zwraca datę ostatniego raportu finansowego dla danej spółki.",
            "parameters": {
                "type": "object",
                "properties": {
                    "ticker": {
                        "type": "string",
                        "description": "Symbol giełdowy spółki, np. AAPL"
                    }
                },
                "required": ["ticker"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_features",
            "description": "Pobiera wyliczone wskaźniki finansowe i cechy modelu ML dla spółki (marże, wzrosty, momentum, P/E itp.). Używaj columns i dat żeby ograniczyć ilość danych.",
            "parameters": {
                "type": "object",
                "properties": {
                    "ticker": {
                        "type": "string",
                        "description": "Symbol giełdowy spółki, np. AAPL."
                    },
                    "columns": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Lista wskaźników do zwrócenia, np. ['profit_margin', 'pe_ratio']. Pomiń aby zwrócić wszystkie."
                    },
                    "start_date": {
                        "type": "string",
                        "description": "Data początkowa w formacie YYYY-MM-DD."
                    },
                    "end_date": {
                        "type": "string",
                        "description": "Data końcowa w formacie YYYY-MM-DD."
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_latest_features",
            "description": "Zwraca najnowszy zestaw wskaźników finansowych dla danej spółki (do predykcji na żywo).",
            "parameters": {
                "type": "object",
                "properties": {
                    "ticker": {
                        "type": "string",
                        "description": "Symbol giełdowy spółki, np. AAPL"
                    }
                },
                "required": ["ticker"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_prices",
            "description": "Pobiera historię cen akcji (open, high, low, close, volume) dla danej spółki. ZAWSZE podawaj start_date i end_date — bez filtrowania zwróci tysiące wierszy dziennych cen.",
            "parameters": {
                "type": "object",
                "properties": {
                    "ticker": {
                        "type": "string",
                        "description": "Symbol giełdowy spółki, np. AAPL."
                    },
                    "start_date": {
                        "type": "string",
                        "description": "Data początkowa w formacie YYYY-MM-DD. Wymagana dla ograniczenia rozmiaru odpowiedzi."
                    },
                    "end_date": {
                        "type": "string",
                        "description": "Data końcowa w formacie YYYY-MM-DD. Wymagana dla ograniczenia rozmiaru odpowiedzi."
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_latest_price_date",
            "description": "Zwraca datę ostatniej dostępnej ceny akcji dla danej spółki.",
            "parameters": {
                "type": "object",
                "properties": {
                    "ticker": {
                        "type": "string",
                        "description": "Symbol giełdowy spółki, np. AAPL"
                    }
                },
                "required": ["ticker"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_available_file_dates",
            "description": "Zwraca listę dostępnych dat plików makroekonomicznych (FRED) w bazie danych.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_macro_data",
            "description": "Pobiera historyczne wartości wskaźników makroekonomicznych (np. sp500, gdpc1, unrate, dcoilwtico). ZAWSZE filtruj columns i daty — bez filtrowania zwróci dziesiątki tysięcy wierszy.",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_date": {
                        "type": "string",
                        "description": "Data snapshotu danych (np. '2026-06-01'). Bierz z kontekstu widoku."
                    },
                    "columns": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Lista zmiennych FRED do zwrócenia, np. ['sp500', 'unrate', 'gdpc1']. ZAWSZE podaj — bez tego zwróci wszystkie 30 zmiennych."
                    },
                    "start_date": {
                        "type": "string",
                        "description": "Data początkowa w formacie YYYY-MM-DD. ZAWSZE podaj."
                    },
                    "end_date": {
                        "type": "string",
                        "description": "Data końcowa w formacie YYYY-MM-DD. ZAWSZE podaj."
                    }
                },
                "required": ["file_date"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_filing_text",
            "description": "Pobiera tekst wybranej sekcji z raportu 10-K lub 10-Q bezpośrednio z EDGAR. KOSZTOWNE — wywołanie trwa 5-15 sekund i zużywa dużo tokenów. Używaj TYLKO gdy użytkownik wprost pyta o treść raportu, strategię, plany, ryzyka, opis działalności lub coś czego nie da się wyliczyć z liczb.",
            "parameters": {
                "type": "object",
                "properties": {
                    "ticker": {
                        "type": "string",
                        "description": "Symbol giełdowy spółki, np. AAPL, NVDA."
                    },
                    "section": {
                        "type": "string",
                        "enum": ["mda", "business", "risks", "governance"],
                        "description": "Sekcja raportu: 'mda' = plany/wyniki/outlook (Item 7), 'business' = opis działalności (Item 1), 'risks' = czynniki ryzyka (Item 1A), 'governance' = zarząd."
                    },
                    "form": {
                        "type": "string",
                        "enum": ["10-K", "10-Q"],
                        "description": "Typ raportu: '10-K' = roczny (pełne sekcje), '10-Q' = kwartalny (tylko mda)."
                    },
                    "period": {
                        "type": "string",
                        "description": "Okres raportu w formacie YYYY-MM lub YYYY-MM-DD, np. '2020-06' lub '2020-06-30'. Pomiń aby pobrać najnowszy raport."
                    },
                    "max_chars": {
                        "type": "integer",
                        "description": "Maksymalna liczba znaków. Domyślnie 6000. Zwiększ tylko gdy użytkownik poprosił o pełną wersję."
                    }
                },
                "required": ["ticker", "section"]
            }
        }
    }
]

TOOL_MAPPING = {
    "get_financials": get_financials,
    "get_latest_financial_date": get_latest_financial_date,
    "get_features": get_features,
    "get_latest_features": get_latest_features,
    "get_prices": get_prices,
    "get_latest_price_date": get_latest_price_date,
    "get_available_file_dates": get_available_file_dates,
    "get_macro_data": get_macro_data,
    "get_filing_text": get_filing_text,
}
