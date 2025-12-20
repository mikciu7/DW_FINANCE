import boto3
import yfinance as yf
import pandas as pd
import io
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

session = boto3.Session(
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY'),
    aws_secret_access_key= os.getenv('AWS_SECRET_ACCES_KEY'),
    aws_session_token=os.getenv('AWS_SESSION_TOKEN'),
    region_name="us-east-1"
)
BUCKET_NAME = "antekpw-data-lake"
s3 = session.client("s3")

class TickerIngestor:
    def __init__(self,s3, period="max",interval="1d"):
        self.s3 = s3
        self.period = period
        self.interval = interval
        self.run_id = datetime.now(datetime.UTC).strftime("%Y%m%dT%H%M%S")
        self.ingestion_time = datetime.now(datetime.UTC).isoformat()
        self.intervals_dict = {
        '1d' : "daily",
        "1mo" : "monthly",
        "3mo" : "quarterly"
        }
    def fetch_history(self,symbol):
        ticker = yf.Ticker(symbol)
        df = ticker.history(period=self.period,interval = self.interval)
        df.reset_index(inplace=True)

        return df

    def _build_prefix(self,symbol):
        date = self.ingestion_time[:10]
        
        prefix = f"YFINANCE/{self.symbol}/"
        f"symbol={symbol}/"
        f"frequency={self.intervals_dict[self.interval]}/"
        f"ingestion_date={date}/"
        f"run_id={self.run_id}/"
        
        return prefix


    def ingest_symbol(self,symbol):
        history_df = self.fetch_history(symbol)

        history_csv = history_df.to_csv()
        prefix = self._build_prefix(symbol=symbol)
        
        s3.put_object(
            Bucket=BUCKET_NAME,
            Key=f"{prefix}.csv",
            Body = history_csv
        )
    def ingest_batch(self, symbols):
        for symbol in symbols:
            try:
                self.ingest_symbol(symbol)
            except Exception as e:
                print(f"[ERROR] {symbol}: {e}")

ingestor  = TickerIngestor(s3)

symbols  = ["AAPL", "MSFT", "GOOGL", "AMZN"]

ingestor.ingest_batch(symbols)



