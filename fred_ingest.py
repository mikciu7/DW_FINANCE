import boto3
import pandas as pd
from fredapi import Fred
from dotenv import load_dotenv
import os
import io
import argparse  # Do parametrów
from botocore.exceptions import ClientError

# --------------------------------------------------------------------------------------------------------------------
# Konfig
load_dotenv()
API_KEY = os.getenv("API_KEY")
S3_BUCKET_NAME = "neo-eye"  
LOCAL_FALLBACK_DIR = "fred_local_data" # Folder na zapis lokalny, gdy nie uruchamiamy skryptu w CloudShellu (C9)


if not API_KEY:
    print("W pliku .env brakuje klucza API_KEY")
    exit(1) 
try:
    fred = Fred(api_key=API_KEY)
    s3_client = boto3.client('s3')
except Exception as e:
    print(f"Błąd podczas inicjalizacji klientów: {e}")
    exit(1)
# --------------------------------------------------------------------------------------------------------------------

def fetch_fred_data(series_id, start_date, end_date):
    #Pobieramy dane z FRED API dla jednej serii. Zwraca DataFrame lub None w przypadku błędu.

    print(f"FETCH: {series_id} (od {start_date} do {end_date})")
    try:
        df = fred.get_series(series_id, 
                             observation_start=start_date, 
                             observation_end=end_date)
        
        if df.empty:
            print(f"Brak danych dla {series_id} w zadanym okresie.")
            return None
        
        # Konwersja na DataFrame i ustawienie nazw kolumn
        df = df.to_frame(name='value')
        df.index.name = 'date'
        print(f" SUCCESS: {len(df)} wierszy dla {series_id}.")
        return df
        
    except Exception as e:
        print(f"Błąd podczas pobierania {series_id}: {e}")
        return None

# --------------------------------------------------------------------------------------------------------------------

def save_to_s3(df, s3_bucket, s3_key):

    # Próbujemy zapisać DataFrame na S3. Zwraca True w przypadku sukcesu, False w przypadku błędu, jesli false to uruchamiamy fallback lokalny.

    print(f"Próba zapisu do: s3://{s3_bucket}/{s3_key}")
    try:
        # Używamy bufora w pamięci, by nie tworzyć plików lokalnie
        csv_buffer = io.StringIO()
        df.to_csv(csv_buffer)
        body = csv_buffer.getvalue()
        
        s3_client.put_object(
            Bucket=s3_bucket,
            Key=s3_key,
            Body=body
        )
        print(f"SUCCESS: Plik zapisany na S3.")
        return True
        
    except ClientError as e:
        # Obsługa błędów uprawnień lub innych błędów Boto3
        print(f"ERROR: Błąd S3 (sprawdź uprawnienia!): {e}")
        return False
    except Exception as e:
        print(f"ERROR: Nieoczekiwany błąd podczas zapisu na S3: {e}")
        return False

# --------------------------------------------------------------------------------------------------------------------

def save_locally(df, file_name, local_dir):

    #Fallback - Zapisuje DataFrame lokalnie, jeśli zapis na S3 się nie powiedzie ( do pracy lokalnej i testów )

    try:
        # Stwórz folder zapasowy, jeśli nie istnieje
        os.makedirs(local_dir, exist_ok=True)
        
        file_path = os.path.join(local_dir, file_name)
        
        df.to_csv(file_path)
        print(f"Zapisano lokalnie (fallback): {file_path}")
        
    except Exception as e:
        print(f"Nie udało się nawet zapisać lokalnie: {e}")

# --------------------------------------------------------------------------------------------------------------------
def fred_ingest(series_list, start_date, end_date):

    for series_id in series_list:
        print(f"\nPrzetwarzanie: {series_id}")
        
        # pobieramy dane z freda
        df = fetch_fred_data(series_id, start_date, end_date)
        

        if df is not None:
            
            start_str = start_date.replace('-', '')
            end_str = end_date.replace('-', '')
            file_name = f"{series_id}_{start_str}_{end_str}.csv"
            
            # Zgodnie ze strukturą medalu w s3, surowe dane ida do bronze/fred/...
            s3_key = f"bronze/fred/{series_id}/{file_name}"
            
            # Spróbuj zapisać na S3
            success = save_to_s3(df, S3_BUCKET_NAME, s3_key)
            
            # Fallback: Jeśli zapis S3 się nie powiódł, zapisz lokalnie
            if not success:
                print("FALLBACK: Zapis na S3 nie powiódł się. Uruchamianie zapisu lokalnego.")
                save_locally(df, file_name, LOCAL_FALLBACK_DIR)
        
    print("\n--- Zakończono cały proces ingestu ---")

# --------------------------------------------------------------------------------------------------------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Pobiera dane z FRED API i ładuje do warstwy Bronze na S3."
    )
    
    # Argument 1: --series (lista)
    parser.add_argument(
        "--series",
        nargs='+',  # akceptuje 1 lub argsow
        required=True,
        help="Lista identyfikatorów serii FRED (np. GDP UNRATE CPIAUCSL)"
    )
    
    # Argument 2: --start
    parser.add_argument(
        "--start",
        type=str,
        required=True,
        help="Data początkowa w formacie YYYY-MM-DD"
    )
    
    # Argument 3: --end
    parser.add_argument(
        "--end",
        type=str,
        required=True,
        help="Data końcowa w formacie YYYY-MM-DD"
    )
    
    # run script with args
    args = parser.parse_args()
    fred_ingest(args.series, args.start, args.end)