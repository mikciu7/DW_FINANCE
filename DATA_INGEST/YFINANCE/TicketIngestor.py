import boto3
import yfinance as yf

session = boto3.Session(
    aws_access_key_id=AWS_ACCES_KEY_ID,
    aws_secret_access_key= AWS_SECRET_ACCES_KEY,
    aws_session_token=AWS_SESSION_TOKEN,
    region_name="us-east-1"
)
s3 = session.client("s3")

class TickerIngestor:
    def __init__(self,name,s3, period="max",interval="1d"):
        self.name = name
        self.s3 = s3
        self.period = period
        self.interval = interval
        self.ticker = yf.Ticker(self.name)
        self.history = self.ticker.history(period=self.period, interval = self.interval)
    
    intervals_dict = {
        '1d' : "daily",
        "1mo" : "monthly",
        "3mo" : "quarterly"
    }
    def send(self):
        csv = self.history.to_csv()
        frequency =self.intervals_dict[self.interval]
        s3.put_object(
            Bucket="antekpw-data-lake",
            Key=f"{self.name}/{frequency}/{self.name + "_" + frequency +"_data"}.csv",
            Body = csv
        )





