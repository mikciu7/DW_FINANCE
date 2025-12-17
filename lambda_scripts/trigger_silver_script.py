import json
import urllib.parse
from classes.s3_data_handler import S3DataHandler
from classes.s3_silver_merger import SilverMerger

def lambda_handler(event, context):
    print("--- START: Otrzymano zdarzenie z S3 ---")
    
    # Sprawdzamy, czy event zawiera rekordy (czy to faktycznie trigger z S3)
    if 'Records' not in event:
        print("[INFO] Brak rekordów S3 w evencie. Prawdopodobnie test ręczny.")
        return {
            'statusCode': 200,
            'body': json.dumps('Wywołanie ręczne (brak akcji)')
        }

    # Pętla po plikach 
    processed_files = []
    
    for record in event['Records']:
        # Pobieramy nazwę bucketu z triggera 
        bucket_name = record['s3']['bucket']['name']
        
        # Pobieramy nazwę pliku, np. bronze/fred/daily/DGS10.csv
        # unquote_plus jest ważny, bo S3 zamienia spacje na '+' i znaki specjalne na %XX
        file_key = urllib.parse.unquote_plus(record['s3']['object']['key'], encoding='utf-8')
        
        print(f"[TRIGGER] Nowy plik: {file_key} w wiadrze: {bucket_name}")

        try:
            #  Inicjalizacja 
            s3_handler = S3DataHandler(bucket_name)
            merger = SilverMerger(s3_handler)
            
            # Ta metoda sama sprawdzi, czy to daily/monthly i uruchomi odpowiedni merge
            merger.run_merge_from_trigger(file_key)
            
            processed_files.append(file_key)
            
        except Exception as e:
            print(f"[ERROR] Błąd podczas przetwarzania {file_key}: {str(e)}")
            # Nie przerywamy pętli, próbujemy przetworzyć kolejne rekordy
            continue

    print(f"--- KONIEC: Przetworzono {len(processed_files)} plików ---")
    
    return {
        'statusCode': 200,
        'body': json.dumps(f'Sukces! Przetworzono: {processed_files}')
    }