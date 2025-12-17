import pandas as pd
import io
import datetime
import os

class SilverMerger:
    #Uniwersalna klasa ETL do łączenia danych w warstwie Silver
    #Kazde źródło (fred, yahoo, edgar) 
    #i częstotliwości (daily, monthly, quarterly)
    

    def __init__(self, s3_handler):
        self.s3_handler = s3_handler
        self.bucket_name = s3_handler.bucket_name
        self.s3_client = s3_handler.s3_client

    def run_merge_from_trigger(self, trigger_key):
        #do metody podajemy  jej klucz pliku, który właśnie wpadł z poprzedniego triggera,
        #a ona sama decyduje co połączyć
        
        #:param trigger_key: np. 'bronze/yahoo/daily/AAPL.csv'
        
        # Parsowanie ścieżki (rozbijamy stringa na kawałki)
        # Oczekiwana struktura: bronze / source / frequency / filename
        parts = trigger_key.split('/')
        
        if len(parts) < 4 or parts[0] != 'bronze':
            print(f"[SKIP] Plik {trigger_key} nie pasuje do schematu bronze/zrodlo/freq/")
            return

        source = parts[1]      # np. 'yahoo' lub 'fred'
        frequency = parts[2]   # np. 'daily' lub 'monthly'
        
        print(f"\n[TRIGGER] Wykryto zmianę w: Źródło='{source}', Freq='{frequency}'")
        
        # zapisujemy w odpowiednie miejsce w Silver
        self.merge_and_save(source, frequency)

    def merge_and_save(self, source, frequency):

        #Pobiera wszystkie pliki z danego źródła i częstotliwości, łączy je i zapisuje w Silver.

        # Dynamiczna ścieżka wejściowa
        prefix = f"bronze/{source}/{frequency}/"
        
        print(f"[MERGE START] Pobieram pliki z: {prefix} ...")
        
        try:
            response = self.s3_client.list_objects_v2(Bucket=self.bucket_name, Prefix=prefix)
        except Exception as e:
            print(f"  [ERROR] Nie udało się wylistować plików: {e}")
            return

        if 'Contents' not in response:
            print(f"  [WARNING] Pusto w folderze {prefix}.")
            return

        data_frames = []
        found_files = []

        for obj in response['Contents']:
            key = obj['Key']
            if key.endswith('/'): continue # Pomiń foldery

            # Wyciągamy nazwę pliku bez rozszerzenia (to będzie ID kolumny)
            file_name = key.split('/')[-1]
            series_id = file_name.replace('.csv', '') # np. 'AAPL' lub 'GDP'
            
            try:
                # Pobranie i wczytanie
                csv_obj = self.s3_client.get_object(Bucket=self.bucket_name, Key=key)
                body = csv_obj['Body'].read()
                
                df = pd.read_csv(io.BytesIO(body), index_col=0, parse_dates=True)
                
                # STANDARYZACJA NAZW KOLUMN
                # Dla Freda plik ma kolumnę 'value'. Dla Yahoo może mieć 'Close', 'Open'.
                # Musimy dodać prefix, żeby wiedzieć co jest czym po złączeniu.
                # Np. zamień 'value' -> 'GDP'  ALBO 'Close' -> 'AAPL_Close'
                
                if source == 'fred':
                    # Fred ma jedna kolumne 'value'
                    if 'value' in df.columns:
                        df.rename(columns={'value': series_id}, inplace=True)
                else:
                    # Yahoo/Edgar mogą mieć wiele kolumn. Dodajemy prefix nazwy pliku do każdej.
                    # np. 'Close' -> 'AAPL_Close', 'Volume' -> 'AAPL_Volume'
                    df = df.add_prefix(f"{series_id}_")

                # Usuwamy duplikaty w indeksie (zabezpieczenie)
                df = df[~df.index.duplicated(keep='first')]
                
                data_frames.append(df)
                found_files.append(series_id)

            except Exception as e:
                print(f"  [ERROR] Błąd pliku {key}: {e}")

        if not data_frames:
            return

        # MERGE (Outer Join po dacie)
        merged_df = pd.concat(data_frames, axis=1)
        merged_df.sort_index(inplace=True)

        # Zapisz dynamicznie do odpowiedniego folderu
        self._save_to_silver_dynamic(merged_df, source, frequency)

    def _save_to_silver_dynamic(self, df, source, frequency):
        """
        Zapisuje wynik w: silver/merged/{source}/{frequency}_merged_{data}.csv
        """
        today_str = datetime.date.today().strftime('%Y-%m-%d')
        file_name = f"{frequency}_merged_{today_str}.csv"
        
        # Dynamiczna ścieżka wyjściowa
        s3_key = f"silver/merged/{source}/{file_name}"
        
        print(f"  [UPLOAD] Zapis scalonego pliku do: {s3_key}")
        
        try:
            csv_buffer = io.StringIO()
            df.to_csv(csv_buffer, index=True)
            
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=csv_buffer.getvalue()
            )
            print(f"  [SUCCESS] Dane dla {source}/{frequency} zaktualizowane.")
            
        except Exception as e:
            print(f"  [CRITICAL] Błąd zapisu Silver: {e}")