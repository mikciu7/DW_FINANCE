from apscheduler.schedulers.background import BackgroundScheduler
from backend.database import TICKERS
from backend.services.price_service import fetch_and_store_prices
from backend.services.edgar_service import fetch_new_filings, get_latest_financial_date
from backend.services.feature_service import run_feature_pipeline
from backend.services import ml_service
from backend.services.fred_service import load_fred_data_from_source


def daily_price_refresh():
    print("[scheduler] Running daily price refresh...")
    fetch_and_store_prices(TICKERS)
    print("[scheduler] Price refresh done.")
    #tymczasowo
    #load_fred_data_from_source("DW_FINANCE/backend/data_templates/fred")


def edgar_refresh():
    print("[scheduler] Checking for new EDGAR filings...")
    new_data = False
    for ticker in TICKERS:
        since = get_latest_financial_date(ticker) or "2024-01-01"
        if fetch_new_filings(ticker, since):
            new_data = True
            print(f"[scheduler] New data for {ticker}")

    if new_data:
        print("[scheduler] New filings found — recomputing features and retraining model...")
        run_feature_pipeline(TICKERS)
        ml_service.train_model()


def create_scheduler() -> BackgroundScheduler:
    scheduler = BackgroundScheduler()
    scheduler.add_job(daily_price_refresh, "cron", hour=0, minute=5)
    scheduler.add_job(edgar_refresh, "cron", hour=1, minute=0)
    return scheduler
