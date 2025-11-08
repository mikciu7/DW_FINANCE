from fredapi import Fred
import pandas as pd

class FredDataExtractor:
    
    def __init__(self, max_lag_months: int = 3):
        self.fred = Fred(api_key='ee033b97982fae1cf18e225901b5b180')
        self.max_lag = max_lag_months
        

    def get_latest(self, series_id: str, as_of):
        """Return latest value up to `as_of`, None if older than max_lag_months."""
        as_of = pd.Timestamp(as_of)
        data = self.fred.get_series(series_id)
        data = data[data.index <= as_of]
        if data.empty:
            return None
        date, value = data.index[-1], data.iloc[-1]
        if date < as_of - pd.DateOffset(months=self.max_lag):
            return None
        return float(value)
        

    def print_basic_snapshot(self, as_of):
        """Print a few key indicators as of given date."""
        series = {
            "CPI": "CPIAUCSL",
            "GDP": "GDP",
            "UNRATE": "UNRATE",
            "DGS10": "DGS10",
            "FEDFUNDS": "FEDFUNDS",
            "SP500": "SP500",
        }
        print(f"FRED snapshot as of {as_of}:")
        for name, sid in series.items():
            val = self.get_latest(sid, as_of)
            print(f"  {name:8s}: {val}")

# Example usage
if __name__ == "__main__":
    fredx = FredDataExtractor()
    fredx.print_basic_snapshot("2024-12-31")
