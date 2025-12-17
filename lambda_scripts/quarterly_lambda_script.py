import json
import os
import datetime
from classes.fred_ingestor import FredIngestor
from classes.s3_data_handler import S3DataHandler

# --- KONFIGURACJA ZMIENNYCH KWARTALNYCH ---
QUARTERLY_VARS = [
    'GFDEBTN',      # Dług publiczny
    'GDPC1',        # Real GDP (jeśli chcesz dodać)
    'DRSFRMACBS'    # Delinquency Rate 
]

def lambda_handler(event, context):
    print("--- START: NeoEye Quarterly Ingest ---")
    
    api_key = os.environ.get('API_KEY')
    bucket_name = "neo-eye-prod"
    
    if not api_key or not bucket_name:
        return {'statusCode': 500, 'body': 'Brak zmiennych środowiskowych.'}

    # Inicjalizacja
    try:
        fred = FredIngestor(api_key)
        s3_handler = S3DataHandler(bucket_name)
    except Exception as e:
        return {'statusCode': 500, 'body': f'Init Error: {str(e)}'}

    end_date = datetime.date.today().strftime('%Y-%m-%d')
    start_date = (datetime.date.today() - datetime.timedelta(days=40*365)).strftime('%Y-%m-%d')
    
    print(f"Zakres dat (Quarterly): {start_date} -> {end_date}")

    processed_count = 0

    # ---------------------------------------------------------
    # Pobieranie i Zapis QUARTERLY
    # ---------------------------------------------------------
    print(f">>> Pobieranie {len(QUARTERLY_VARS)} zmiennych QUARTERLY...")
    try:
        fred.ingest_quarterly_data(QUARTERLY_VARS, start_date, end_date)
        q_data = fred.get_quarterly_data()
        
        for series_id, df in q_data.items():
            # Zapis do: bronze/fred/quarterly/SERIES_ID.csv
            s3_handler.save_data(df, 'fred', 'quarterly', f"{series_id}.csv")
            processed_count += 1
            
    except Exception as e:
        print(f"[ERROR] Błąd Quarterly: {e}")
        return {'statusCode': 500, 'body': f'Error: {str(e)}'}

    msg = f"Sukces! Zaktualizowano {processed_count} plików kwartalnych w Bronze."
    print(msg)
    
    return {
        'statusCode': 200,
        'body': json.dumps(msg)
    }