from fastapi import APIRouter, Query
from fastapi import Depends
from backend.middleware.auth_middleware import require_auth
from backend.database import get_connection
from psycopg2.extras import RealDictCursor
from typing import Optional

router = APIRouter(prefix="/api/macro", tags=["macro"], dependencies=[Depends(require_auth)])

@router.get("/file-dates")
def get_file_dates():
    # Zwraca liste unikalnych dat plikĂłw (wersji danych) dla dropdowna w React
    # w celu tego wybierania np. danych backupowych
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT DISTINCT file_date FROM macro_data ORDER BY file_date DESC")
            return [str(r[0]) for r in cur.fetchall()]

@router.get("/data")
# do wybierania odpowiednich dat plikow
def get_macro_data(
        file_date: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
):
    # Pobiera dane konkretnej wersji z opcjonalnym zakresem dat dla wykresu
    query = "SELECT * FROM macro_data WHERE file_date = %s"
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
            return cur.fetchall()
