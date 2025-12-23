import requests
import pandas as pd
import yfinance as yf
import json
url = "https://bdl.stat.gov.pl/api/v1/data/by-variable/76447"

response = requests.get(url)

data = response.json()


with open("gus.json", "w", encoding="utf-8") as f:
    json.dump(data,f,ensure_ascii=False,indent=4)
    