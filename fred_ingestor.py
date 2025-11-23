from fredapi import Fred
import pandas as pd
import time

class FredIngestor:

    #Klasa odpowiedzialna WYŁĄCZNIE za pobieranie danych z FRED API.
    #Nie łączy się z S3. Magazynuje pobrane dane wewnątrz instancji.
    
    #Struktura slownikow:
    #{
    #    'SERIES_ID': DataFrame,
    #    'INNY_ID': DataFrame
    #}
    #

    def __init__(self, api_key):
        
        # parametr - api_key : Klucz API FRED
    
        if not api_key:
            raise ValueError("Wymagany jest klucz API FRED.")
        
        self.fred = Fred(api_key=api_key)
        
        # Wewnętrzne bufory na dane
        self._data_daily = {}
        self._data_monthly = {}
        self._data_quarterly = {}
        
        print("[INIT] FredIngestor gotowy (tryb bezstanowy S3).")

    # --- METODY POMOCNICZE ---

    def _fetch_series(self, series_id, start_date, end_date):
        # Pobiera jedną serię i zwraca DataFrame 
        print(f"[FRED-FETCH] Pobieranie: {series_id}...")
        try:
            data = self.fred.get_series(series_id, 
                                        observation_start=start_date, 
                                        observation_end=end_date)
            if data.empty:
                print(f"[WARNING] Pusto dla {series_id}.")
                return None

            df = data.to_frame(name='value')
            df.index.name = 'date'
            return df
        except Exception as e:
            print(f"[ERROR] Błąd pobierania {series_id}: {e}")
            return None

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
            
            if df is not None:
                self._store_data(df, series_id, frequency)
                count += 1
            
            # Rate limiting
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

    # --- METODY BULK (Odkrywanie kategorii) ---
    
    def ingest_category_bulk(self, category_id, target_frequency, start_date, end_date, limit=20):
        print(f"\n[BULK] Skanowanie kategorii ID: {category_id} (Freq: {target_frequency})...")
        try:
            category_df = self.fred.search_by_category(category_id, limit=limit*2, order_by='popularity', sort_order='desc')
            if category_df is None or category_df.empty: return

            filtered = category_df[category_df['frequency_short'] == target_frequency]
            series_ids = filtered['id'].head(limit).tolist()
            
            freq_map = {'D': 'daily', 'M': 'monthly', 'Q': 'quarterly'}
            target_freq_name = freq_map.get(target_frequency)
            
            if target_freq_name:
                self._process_batch(series_ids, start_date, end_date, target_freq_name)
            else:
                print(f"  [SKIP] Nieobsługiwana częstotliwość: {target_frequency}")

        except Exception as e:
            print(f"  [ERROR] Błąd Bulk: {e}")

    # --- GETTERY  ---

    def get_daily_data(self):
        # Zwraca słownik {series_id: DataFrame} dla danych dziennych
        return self._data_daily

    def get_monthly_data(self):
        # Zwraca słownik {series_id: DataFrame} dla danych miesięcznych
        return self._data_monthly

    def get_quarterly_data(self):
        # Zwraca słownik {series_id: DataFrame} dla danych kwartalnych
        return self._data_quarterly