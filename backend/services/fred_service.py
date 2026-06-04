import os
import re
from typing import Optional

import pandas as pd
from psycopg2.extras import RealDictCursor

from backend.database import get_connection, MACRO_COLS


#wersja lokalna
def load_fred_data_from_source(data_source):
    # ladowanie danych docelowo z s3 neo-eye-prod/silver/merged/fred/...


    # do edycji w razie co w lambdzie
    files = [f for f in os.listdir(data_source) if f.endswith(".csv")]


    for file_name in files:
        valid_file = re.match(r"([a-z]+)_merged_(\d{4}-\d{2}-\d{2})\.csv", file_name)
        if not valid_file:
            continue

        data_type = valid_file.group(1) # np. dane daily
        data_date = valid_file.group(2) # zalezy nam na segregowaniu 3 mies wstecz data w formacie YYYY-MM-DD

        path = os.path.join(data_source, file_name)
        df = pd.read_csv(path)

        # stdryzacja kolumn
        df.columns = [c.lower() for c in df.columns]
        df['date'] = pd.to_datetime(df['date']).dt.strftime('%Y-%m-%d')

        df['data_type'] = data_type
        df['file_date'] = data_date

        # Filtrowanie tylko tych kolumn, które mamy w MACRO_COLS + klucze
        available_cols = [c for c in MACRO_COLS if c in df.columns]
        cols_to_insert = ['date', 'data_type', 'file_date'] + available_cols

        rows = df[cols_to_insert].where(pd.notnull(df[cols_to_insert]), None).values.tolist()

        # analogicznie jak w edgar service
        # Upsert logic
        col_names = ", ".join(cols_to_insert)
        placeholders = ", ".join(["%s"] * len(cols_to_insert))
        updates = ", ".join([f"{c} = EXCLUDED.{c}" for c in available_cols])

        query = f"""
            INSERT INTO macro_data ({col_names})
            VALUES ({placeholders})
            ON CONFLICT (date, data_type, file_date) 
            DO UPDATE SET {updates}
        """

        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.executemany(query, rows)
            conn.commit()

        print(f"[fred_service] Processed {file_name} -> {len(df)} rows")


def get_available_file_dates():
    # bedzie zwracac liste unikalnych dat plików dostepnych
    # w bazie dla Reacta, jakbysmy chcieli wyswietlac dane z backupow
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT DISTINCT file_date FROM macro_data ORDER BY file_date DESC")
            return [str(r[0]) for r in cur.fetchall()]

def get_macro_data(file_date: str, start_date: Optional[str] = None, end_date: Optional[str] = None) -> list[dict]:
    """
    Pobiera dane z tabeli macro_data dla podanego snapshotu (file_date).
    Opcjonalnie filtruje po zakresie dat.
    """


    print(f"[DEBUG BAZY] Wywołano get_macro_data z parametrami:")
    print(f"-> file_date: {file_date}")
    print(f"-> start_date: {start_date}")
    print(f"-> end_date: {end_date}")


    # Budujemy dynamiczne zapytanie
    query = "SELECT date, data_type, file_date, " + ", ".join(MACRO_COLS) + " FROM macro_data WHERE file_date = %s"
    params = [file_date]

    if start_date:
        query += " AND date >= %s"
        params.append(start_date)
    if end_date:
        query += " AND date <= %s"
        params.append(end_date)

    query += " ORDER BY date ASC"

    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, params)
            rows = cur.fetchall()

    # Formatowanie daty dla spójności
    result = []
    for r in rows:
        row_dict = dict(r)
        if row_dict.get('date'):
            row_dict['date'] = str(row_dict['date'])
        if row_dict.get('file_date'):
            row_dict['file_date'] = str(row_dict['file_date'])
        result.append(row_dict)

    return result


# kod do lambdy

# import os
# import boto3
# import pandas as pd
# import psycopg2
# from io import StringIO
#
# # Konfiguracja z Environment Variables
# DB_PARAMS = {
#     "host": os.environ['DB_HOST'],
#     "database": os.environ['DB_NAME'],
#     "user": os.environ['DB_USER'],
#     "password": os.environ['DB_PASS'],
#     "port": os.environ.get('DB_PORT', '5432')
# }
#
# MACRO_COLS = ["drsfrmacbs", "gdpc1", "gfdebtn", "mortgage30us", "stlfsi4",
#               "t10y2y", "unrate", "cpiaucsl", "fedfunds", "m2sl"]
#
# s3 = boto3.client('s3')
#
# def lambda_handler(event, context):
#     # 1. Identyfikacja pliku z S3
#     bucket = event['Records'][0]['s3']['bucket']['name']
#     key = event['Records'][0]['s3']['object']['key']
#
#     # Pobranie danych z S3
#     response = s3.get_object(Bucket=bucket, Key=key)
#     df = pd.read_csv(StringIO(response['Body'].read().decode('utf-8')))
#
#     # 2. Standaryzacja (Twoja logika z fred_service)
#     df.columns = [c.lower() for c in df.columns]
#     if 'date' in df.columns:
#         df['date'] = pd.to_datetime(df['date']).dt.strftime('%Y-%m-%d')
#
#     # Przygotowanie wierszy (tylko kolumny które istnieją w pliku i bazie)
#     available_cols = [c for c in MACRO_COLS if c in df.columns]
#     cols_to_insert = ['date'] + available_cols
#     rows = df[cols_to_insert].where(pd.notnull(df[cols_to_insert]), None).values.tolist()
#
#     # 3. Połączenie z RDS i REFRESH (Usuwamy stare, wstawiamy nowe)
#     conn = psycopg2.connect(**DB_PARAMS)
#     try:
#         with conn.cursor() as cur:
#             # CZYSZCZENIE: Usuwamy wszystko, co było wcześniej
#             # Jeśli chcesz czyścić tylko konkretny typ (np. tylko daily), dodaj WHERE
#             cur.execute("TRUNCATE TABLE macro_data;")
#
#             # INSERT: Wstawiamy świeże dane
#             placeholders = ", ".join(["%s"] * len(cols_to_insert))
#             col_names = ", ".join(cols_to_insert)
#             insert_query = f"INSERT INTO macro_data ({col_names}) VALUES ({placeholders})"
#
#             cur.executemany(insert_query, rows)
#
#         conn.commit()
#         return {"status": "success", "msg": f"Table refreshed with {len(rows)} rows from {key}"}
#     except Exception as e:
#         conn.rollback()
#         raise e
#     finally:
#         conn.close()