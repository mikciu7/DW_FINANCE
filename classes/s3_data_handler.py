import boto3
import pandas as pd
import os
import io
from botocore.exceptions import ClientError

class S3DataHandler:

    #Klasa odpowiedzialna za zarządzanie zapisem danych do S3 (lub lokalnie w razie awarii)
    #Obsługuje strukture bronze/source_name/frequency/file_name


    def __init__(self, bucket_name, local_backup_dir='lokalny_backup'):

        #parametr -  bucket_name: Nazwa wiadra S3 
        #parametr -  local_backup_dir: Folder lokalny na wypadek awarii zapisu S3
   
        self.bucket_name = bucket_name
        self.local_backup_dir = local_backup_dir
        self.s3_client = boto3.client('s3')
        
        # Sprawdzamy połączenie przy inicjalizacji 
        try:
            self.s3_client.head_bucket(Bucket=self.bucket_name)
            print(f"[INIT] Połączono z wiadrem S3: {self.bucket_name}")
        except ClientError as e:
            print(f"[WARNING] Nie można połączyć z wiadrem {self.bucket_name}. Sprawdź uprawnienia/nazwę. Będzie używany zapis lokalny")


# -----------------------------------------------------------------------------------

    def _convert_to_dataframe(self, data):
        # Metoda pomocnicza: Zamienia różne typy danych wejściowych na Pandas DataFrame tak jak 
        # bylo to omawiane, potem spowrotem z tego data frame bedziemy w .csv na razie pakowac wszystkie dane

        if isinstance(data, pd.DataFrame):
            return data
        elif isinstance(data, list) or isinstance(data, dict):
            try:
                return pd.DataFrame(data)
            except Exception:
                raise ValueError("Nie udało się przekonwertować słownika/listy na DataFrame")
        else:
            raise TypeError("Dane muszą być typu DataFrame, list lub dict")

# --------------------------------------------------------------------------------------------------------------------

    def save_data(self, data, source_name, frequency, file_name):
        # metoda do zapisywania pożądanych danych
        # działa do tworzenia nowych, jak i nadpisywania starych plików
        # W S3 operacja 'put_object' automatycznie nadpisuje plik, jeśli taki istnieje
        
        #parametr data: Dane (DataFrame, list, dict)
        #parametr source_name: Źródło danych (np. 'fred', 'yahoo', 'edgar')
        #parametr frequency: Częstotliwość danych (np. 'daily', 'monthly', 'quarterly')
        #parametr file_name: Nazwa pliku (np. 'Dane-SektorId22.csv')
        
        # Standaryzujemy dane do DataFrame
        try:
            df = self._convert_to_dataframe(data)
        except Exception as e:
            print(f"[ERROR] Błąd konwersji danych: {e}")
            return False

        # przykladowa struktura --> bronze/fred/monthly/UNRATE.csv
        s3_key = f"bronze/{source_name}/{frequency}/{file_name}"
        
        print(f"[UPLOAD] Próba zapisu: s3://{self.bucket_name}/{s3_key}")

        # Próba wysłania na S3
        try:
            # Konwersja DF do bufora CSV w pamięci (nie tworzymy pliku na dysku)
            csv_buffer = io.StringIO()
            df.to_csv(csv_buffer, index=True) # Zapisujemy z indeksem - data
            
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=csv_buffer.getvalue()
            )
            print(f"[SUCCESS] Plik zapisany/zaktualizowany na S3")
            return True

        except (ClientError, Exception) as e:
            print(f"[ERROR] Błąd zapisu S3: {e}")
            print("[FALLBACK] Uruchamiam zapis lokalny...")
            self._save_locally(df, source_name, frequency, file_name)
            return False

    def _save_locally(self, df, source_name, frequency, file_name):

        # Metoda awaryjna zapisuje na dysku, zachowując strukturę folderów
        # Tworzy: data_backup/fred/monthly/UNRATE.csv

        try:
            # Budowanie lokalnej ścieżki
            local_path = os.path.join(self.local_backup_dir, source_name, frequency)
            
            # Tworzenie folderów jeśli nie istnieją
            os.makedirs(local_path, exist_ok=True)
            
            full_file_path = os.path.join(local_path, file_name)
            df.to_csv(full_file_path, index=True)
            
            print(f"[LOCAL] Zapisano bezpiecznie lokalnie: {full_file_path}")
        except Exception as e:
            print(f"[CRITICAL] Nie udało się zapisać nawet lokalnie: {e}")