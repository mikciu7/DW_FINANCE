import boto3
import yfinance as yf
import pandas as pd
import json
import io
from datetime import datetime, timezone
import os
from dotenv import load_dotenv

load_dotenv()

# Konfiguracja sesji (tak jak w Twoim przykładzie)
session = boto3.Session(
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY'),
    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
    region_name="us-east-1"
)
BUCKET_NAME = "neo-eye-prod"
s3 = session.client("s3")

class NewsIngestor:
    def __init__(self, s3_client):
        self.s3 = s3_client
        self.run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
        self.ingestion_time = datetime.now(timezone.utc).isoformat()

    def fetch_news(self, symbol):
        """Pobiera listę wiadomości dla danego symbolu."""
        ticker = yf.Ticker(symbol)
        # ticker.news zwraca listę słowników (dict)
        return ticker.news

    def _build_prefix(self, symbol):
        """Tworzy ścieżkę w S3, zachowując strukturę podobną do TickerIngestor."""
        date = self.ingestion_time[:10]
        prefix = f"bronze/yahoo/news/{symbol}/ingestion_date={date}/run_id={self.run_id}.json"
        return prefix

    def ingest_symbol(self, symbol):
        """Pobiera newsy i wysyła je jako plik JSON do S3."""
        news_data = self.fetch_news(symbol)
        
        if not news_data:
            print(f"[INFO] Brak nowych wiadomości dla {symbol}")
            return

        
        news_json = json.dumps(news_data, ensure_ascii=False, indent=4)
        
        prefix = self._build_prefix(symbol=symbol)
        
        self.s3.put_object(
            Bucket=BUCKET_NAME,
            Key=prefix,
            Body=news_json,
            ContentType='application/json'
        )
        print(f"[SUCCESS] Wysłano newsy dla {symbol} do {prefix}")

    def ingest_batch(self, symbols):
        """Przetwarza listę spółek w pętli."""
        for symbol in symbols:
            try:
                self.ingest_symbol(symbol)
            except Exception as e:
                print(f"[ERROR] {symbol}: {e}")


news_ingestor = NewsIngestor(s3)
symbols = ["AAPL", "MSFT", "GOOGL", "AMZN"]

news_ingestor.ingest_batch(symbols)