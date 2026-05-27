import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backend.services.edgar_service import get_financials, get_latest_financial_date
from backend.services.feature_service import get_features, get_latest_features
from backend.services.price_service import get_prices, get_latest_price_date
from backend.services.fred_service import get_available_file_dates

tools = [
    {
        "type": "function",
        "function": {
            "name": "get_financials",
            "description": "Pobiera dane finansowe spółki (bilans, rachunek wyników, przepływy pieniężne) z bazy danych.",
            "parameters": {
                "type": "object",
                "properties": {
                    "ticker": {
                        "type": "string",
                        "description": "Symbol giełdowy spółki, np. AAPL, MSFT. Jeśli nie podano, zwraca dane wszystkich spółek."
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
            "description": "Pobiera wyliczone wskaźniki finansowe i cechy modelu ML dla spółki (marże, wzrosty, momentum, P/E itp.).",
            "parameters": {
                "type": "object",
                "properties": {
                    "ticker": {
                        "type": "string",
                        "description": "Symbol giełdowy spółki, np. AAPL. Jeśli nie podano, zwraca dane wszystkich spółek."
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
            "description": "Pobiera historię cen akcji (open, high, low, close, volume) dla danej spółki.",
            "parameters": {
                "type": "object",
                "properties": {
                    "ticker": {
                        "type": "string",
                        "description": "Symbol giełdowy spółki, np. AAPL. Jeśli nie podano, zwraca dane wszystkich spółek."
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
]

TOOL_MAPPING = {
    "get_financials": get_financials,
    "get_latest_financial_date": get_latest_financial_date,
    "get_features": get_features,
    "get_latest_features": get_latest_features,
    "get_prices": get_prices,
    "get_latest_price_date": get_latest_price_date,
    "get_available_file_dates": get_available_file_dates,
}
