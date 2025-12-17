import json
import os
import datetime
from classes.fred_ingestor import FredIngestor
from classes.s3_data_handler import S3DataHandler

# --- KONFIGURACJA LIST ZMIENNYCH ---
# Wklejamy je tutaj na sztywno, bo to najprostsza metoda w Lambdzie.

# 1. Zmienne codzienne (pobierane przy okazji miesięcznego runu)
DAILY_VARS = [
    'BAMLC0A4CBBB', 'VIXCLS', 'DGS2', 'BAMLH0A0HYM2', 'DCOILWTICO', 
    'DEXCHUS', 'DGS6MO', 'WALCL', 'DGS3MO', 'DGS1MO', 'DFF', 
    'DGS1', 'T5YIE', 'DEXUSUK', 'DEXUSEU'
]

# 2. Zmienne miesięczne
MONTHLY_VARS = [
    'PSAVERT', 'CSCICP03USM665S', 'M1SL', 'TCU', 
    'DRSFRMACBS', 'UMCSENT', 'HOUST', 'PERMIT', 'FEDFUNDS'
]

def lambda_handler(event, context):
    print("--- START: NeoEye Monthly Ingest ---")
    
    # 1. Pobieranie konfiguracji ze Zmiennych Środowiskowych Lambdy
    # (Pamiętaj, żeby ustawić je w zakładce Configuration -> Environment variables)
    api_key = os.environ.get('API_KEY')
    bucket_name = "neo-eye-prod"
    
    if not api_key or not bucket_name:
        print("[CRITICAL] Brak zmiennych środowiskowych API_KEY lub BUCKET_NAME")
        return {
            'statusCode': 500,
            'body': json.dumps('Błąd konfiguracji: Brak kluczy.')
        }

    # 2. Inicjalizacja klas
    try:
        fred = FredIngestor(api_key)
        s3_handler = S3DataHandler(bucket_name)
    except Exception as e:
        print(f"[ERROR] Błąd inicjalizacji klas: {e}")
        return {'statusCode': 500, 'body': json.dumps(f'Init Error: {str(e)}')}

    # 3. Ustawienie zakresu dat (np. ostatnie 25 lat do dzisiaj)
    end_date = datetime.date.today().strftime('%Y-%m-%d')
    start_date = (datetime.date.today() - datetime.timedelta(days=25*365)).strftime('%Y-%m-%d')
    
    print(f"Zakres dat: {start_date} -> {end_date}")

    processed_count = 0

    # ---------------------------------------------------------
    # 4. Pobieranie i Zapis DAILY
    # ---------------------------------------------------------
    print(f">>> Pobieranie {len(DAILY_VARS)} zmiennych DAILY...")
    try:
        fred.ingest_daily_data(DAILY_VARS, start_date, end_date)
        daily_data = fred.get_daily_data()
        
        for series_id, df in daily_data.items():
            # Zapis do: bronze/fred/daily/SERIES_ID.csv
            s3_handler.save_data(df, 'fred', 'daily', f"{series_id}.csv")
            processed_count += 1
            
    except Exception as e:
        print(f"[ERROR] Błąd przy przetwarzaniu Daily: {e}")

    # ---------------------------------------------------------
    # 5. Pobieranie i Zapis MONTHLY
    # ---------------------------------------------------------
    print(f">>> Pobieranie {len(MONTHLY_VARS)} zmiennych MONTHLY...")
    try:
        fred.ingest_monthly_data(MONTHLY_VARS, start_date, end_date)
        monthly_data = fred.get_monthly_data()
        
        for series_id, df in monthly_data.items():
            # Zapis do: bronze/fred/monthly/SERIES_ID.csv
            s3_handler.save_data(df, 'fred', 'monthly', f"{series_id}.csv")
            processed_count += 1
            
    except Exception as e:
        print(f"[ERROR] Błąd przy przetwarzaniu Monthly: {e}")

    # ---------------------------------------------------------
    # 6. Podsumowanie
    # ---------------------------------------------------------
    msg = f"Sukces! Zaktualizowano {processed_count} plików w Bronze."
    print(msg)
    
    return {
        'statusCode': 200,
        'body': json.dumps(msg)
    }