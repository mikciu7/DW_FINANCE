import requests
import pandas as pd
import time

class FredIngestor:

    # Klasa odpowiedzialna WYŁĄCZNIE za pobieranie danych z FRED API.
    # Używa biblioteki requests (dostępnej w warstwie AWS), nie wymaga fredapi.

    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://api.stlouisfed.org/fred/series/observations"
        
        # --- POPRAWKA: Inicjalizacja słowników ---
        self._data_daily = {}
        self._data_monthly = {}
        self._data_quarterly = {}

    def _fetch_series(self, series_id, start_date=None, end_date=None):
        """Pobiera dane bezpośrednio z API URL (bez biblioteki fredapi)"""
        params = {
            'series_id': series_id,
            'api_key': self.api_key,
            'file_type': 'json',
            'observation_start': start_date,
            'observation_end': end_date
        }
        
        try:
            response = requests.get(self.base_url, params=params)
            response.raise_for_status()
            data = response.json()
            
            if 'observations' not in data:
                return pd.DataFrame()

            # Tworzymy DataFrame
            df = pd.DataFrame(data['observations'])
            
            if df.empty:
                return pd.DataFrame()

            # Czyszczenie i formatowanie
            df['date'] = pd.to_datetime(df['date'])
            df['value'] = pd.to_numeric(df['value'], errors='coerce')
            df = df[['date', 'value']]
            df.set_index('date', inplace=True)
            df.columns = [series_id] # Nazywamy kolumnę ID serii
            
            return df
            
        except Exception as e:
            print(f"[ERROR] Nie udało się pobrać {series_id}: {e}")
            return pd.DataFrame()

    def _store_data(self, df, series_id, frequency):
        # Zapisuje pobrany DataFrame do odpowiedniego wewnętrznego słownika
        if frequency == 'daily':
            self._data_daily[series_id] = df
        elif frequency == 'monthly':
            self._data_monthly[series_id] = df
        elif frequency == 'quarterly':
            self._data_quarterly[series_id] = df

    def _process_batch(self, series_list, start_date, end_date, frequency):
       # Iteruje po liście i zapisuje wyniki w pamięci instancji 
        count = 0
        for series_id in series_list:
            df = self._fetch_series(series_id, start_date, end_date)
            
            if df is not None and not df.empty:
                self._store_data(df, series_id, frequency)
                count += 1
            
            # Rate limiting (ważne przy requests)
            time.sleep(0.4)
            if count % 5 == 0:
                print(f"[BUFFER] Zbuforowano {count} serii ({frequency})...")

    # --- METODY INGEST ---

    def ingest_daily_data(self, series_list, start_date, end_date):
        print(f"\n--- Pobieranie do bufora DAILY ({len(series_list)} serii) ---")
        self._process_batch(series_list, start_date, end_date, 'daily')

    def ingest_monthly_data(self, series_list, start_date, end_date):
        print(f"\n--- Pobieranie do bufora MONTHLY ({len(series_list)} serii) ---")
        self._process_batch(series_list, start_date, end_date, 'monthly')

    def ingest_quarterly_data(self, series_list, start_date, end_date):
        print(f"\n--- Pobieranie do bufora QUARTERLY ({len(series_list)} serii) ---")
        self._process_batch(series_list, start_date, end_date, 'quarterly')

    # --- GETTERY ---

    def get_daily_data(self):
        return self._data_daily

    def get_monthly_data(self):
        return self._data_monthly

    def get_quarterly_data(self):
        return self._data_quarterly