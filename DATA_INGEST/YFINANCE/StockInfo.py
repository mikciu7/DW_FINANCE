import yfinance as yf
# Jeśli moduły są w tym samym pakiecie (uruchamiane jako pakiet) — zalecane:
from ...s3_data_handler import S3DataHandler


class YFinancePipeline:
    SOURCE_NAME = 'yfinance'

    def __init__(self, ticker_symbol: str, s3_handler: S3DataHandler):
        self.ticker_symbol = ticker_symbol.upper() 
        self.ticker = yf.Ticker(self.ticker_symbol)
        self.s3 = s3_handler
    def _process_and_save(self, df, frequency: str, file_name: str):
        if df.empty:
            print(f"[WARNING] Nie zapisano. Dane dla {self.ticker_symbol} są puste.")
            return False
        return self.s3.save_data(
            data=df,
            source_name=self.SOURCE_NAME,
            frequency=frequency,
            file_name=file_name
        )
    def fetch_and_save_full_history(self):
        """Pobiera pełną historię cen i zapisuje ją do S3."""
        try:
            df = self.ticker.history(period="max")
        
            frequency = 'daily' 
            file_name = f"{self.ticker_symbol}_full_history.csv"
        
            print(f"Pobrano pełną historię dla {self.ticker_symbol}. Rozmiar: {len(df)} wierszy.")
            return self._process_and_save(df, frequency, file_name)
        except Exception as e:
            print(f"[ERROR] Błąd podczas pobierania pełnej historii dla {self.ticker_symbol}: {e}")
            return False
        


    def fetch_and_save_today_intraday(self):
        """Pobiera dzisiejszą historię minutową i zapisuje ją do S3."""
        try:
            df = self.ticker.history(period="1d", interval="1m")
        
            frequency = 'minute'
            file_name = f"{self.ticker_symbol}_intraday_{self.s3.dzisiaj}.csv" 
        
            print(f"Pobrano dane minutowe dla {self.ticker_symbol}. Rozmiar: {len(df)} wierszy.")
            return self._process_and_save(df, frequency, file_name)
        except Exception as e:
            print(f"[ERROR] Błąd podczas pobierania danych minutowych dla {self.ticker_symbol}: {e}")
            return False
        
        

    def fetch_and_save_monthly_data(self):
        """Pobiera miesięczną historię cen i zapisuje ją do S3."""
        try:
            df = self.ticker.history(period="max", interval="1mo")
            frequency = 'monthly' 
            file_name = f"{self.ticker_symbol}_monthly_history.csv"
        
            print(f"Pobrano miesięczną historię dla {self.ticker_symbol}. Rozmiar: {len(df)} wierszy.")
            return self._process_and_save(df, frequency, file_name)
        except Exception as e:
            print(f"[ERROR] Błąd podczas pobierania miesięcznych danych dla {self.ticker_symbol}: {e}")
            return False
 

    def fetch_and_save_quarterly_data(self):
        """Pobiera kwartalną historię cen i zapisuje ją do S3."""
        try:
            df = self.ticker.history(period="max", interval="3mo")
        
            frequency = 'quarterly' 
            file_name = f"{self.ticker_symbol}_quarterly_history.csv"
            
            print(f"Pobrano kwartalną historię dla {self.ticker_symbol}. Rozmiar: {len(df)} wierszy.")
            return self._process_and_save(df, frequency, file_name)
        except Exception as e:
            print(f"[ERROR] Błąd podczas pobierania kwartalnych danych dla {self.ticker_symbol}: {e}")
            return False
        
        