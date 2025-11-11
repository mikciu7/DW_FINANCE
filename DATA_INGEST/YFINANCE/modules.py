import yfinance as yf
import pandas as pd


def _get_info(symbol: str) -> dict:
    """Pobiera pełny słownik informacji o spółce."""
    ticker = yf.Ticker(symbol)
    info = ticker.info
    if not info:
        raise ValueError(f"Nie udało się pobrać danych dla symbolu {symbol}")
    return info


#  Informacje o firmie
def get_company_profile(symbol: str) -> pd.DataFrame:
    info = _get_info(symbol)
    keys = [
        "longName", "shortName", "symbol", "address1", "city", "state", "zip",
        "country", "phone", "website", "industry", "sector",
        "longBusinessSummary", "fullTimeEmployees"
    ]
    data = {k: info.get(k, None) for k in keys}
    return pd.DataFrame([data])


#  Dane rynkowe
def get_market_data(symbol: str) -> pd.DataFrame:
    info = _get_info(symbol)
    keys = [
        "currentPrice", "previousClose", "open", "dayLow", "dayHigh",
        "regularMarketDayRange", "fiftyTwoWeekLow", "fiftyTwoWeekHigh",
        "marketCap", "volume", "averageVolume", "beta", "currency"
    ]
    data = {k: info.get(k, None) for k in keys}
    if data.get("marketCap"):
        data["marketCap (mld)"] = data["marketCap"] / 1e9
    return pd.DataFrame([data])


# Wskaźniki fundamentalne
def get_fundamentals(symbol: str) -> pd.DataFrame:
    info = _get_info(symbol)
    keys = [
        "trailingPE", "forwardPE", "priceToBook", "priceToSalesTrailing12Months",
        "trailingEps", "forwardEps", "enterpriseValue", "enterpriseToRevenue",
        "enterpriseToEbitda", "payoutRatio", "bookValue", "52WeekChange", "SandP52WeekChange"
    ]
    data = {k: info.get(k, None) for k in keys}
    return pd.DataFrame([data])


#  Dane finansowe
def get_financials(symbol: str) -> pd.DataFrame:
    info = _get_info(symbol)
    keys = [
        "totalRevenue", "grossProfits", "ebitda", "freeCashflow",
        "operatingCashflow", "totalDebt", "debtToEquity", "returnOnAssets",
        "returnOnEquity", "earningsGrowth", "revenueGrowth",
        "grossMargins", "ebitdaMargins", "operatingMargins"
    ]
    data = {k: info.get(k, None) for k in keys}
    return pd.DataFrame([data])


#  Dywidendy
def get_dividends_info(symbol: str) -> pd.DataFrame:
    info = _get_info(symbol)
    keys = [
        "dividendRate", "dividendYield", "exDividendDate", "payoutRatio",
        "fiveYearAvgDividendYield", "lastDividendValue", "lastDividendDate"
    ]
    data = {k: info.get(k, None) for k in keys}
    return pd.DataFrame([data])


#  Prognozy analityków
def get_analyst_forecasts(symbol: str) -> pd.DataFrame:
    info = _get_info(symbol)
    keys = [
        "targetHighPrice", "targetLowPrice", "targetMeanPrice", "targetMedianPrice",
        "recommendationMean", "recommendationKey", "numberOfAnalystOpinions",
        "averageAnalystRating"
    ]
    data = {k: info.get(k, None) for k in keys}
    return pd.DataFrame([data])


#  Wskaźniki płynności i zadłużenia
def get_liquidity_ratios(symbol: str) -> pd.DataFrame:
    info = _get_info(symbol)
    keys = ["currentRatio", "quickRatio", "debtToEquity"]
    data = {k: info.get(k, None) for k in keys}
    return pd.DataFrame([data])


#  Ryzyka i ESG
def get_risk_governance(symbol: str) -> pd.DataFrame:
    info = _get_info(symbol)
    keys = [
        "auditRisk", "boardRisk", "compensationRisk",
        "shareHolderRightsRisk", "overallRisk", "esgPopulated"
    ]
    data = {k: info.get(k, None) for k in keys}
    return pd.DataFrame([data])


#  Dane o rynku i giełdzie
def get_exchange_info(symbol: str) -> pd.DataFrame:
    info = _get_info(symbol)
    keys = [
        "exchange", "market", "fullExchangeName",
        "financialCurrency", "regularMarketTime", "marketState"
    ]
    data = {k: info.get(k, None) for k in keys}
    return pd.DataFrame([data])


#  Pełny przegląd — łączy wszystkie dane
def get_full_company_snapshot(symbol: str) -> pd.DataFrame:
    """Łączy wszystkie sekcje w jeden DataFrame (po kolumnach)."""
    dfs = [
        get_company_profile(symbol),
        get_market_data(symbol),
        get_fundamentals(symbol),
        get_financials(symbol),
        get_dividends_info(symbol),
        get_analyst_forecasts(symbol),
        get_liquidity_ratios(symbol),
        get_risk_governance(symbol),
        get_exchange_info(symbol)
    ]
    return pd.concat(dfs, axis=1)

print(get_full_company_snapshot("AAPL"))  # Przykład użycia
