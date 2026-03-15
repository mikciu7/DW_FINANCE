"""
One-time bootstrap script:
  1. Creates SQLite tables
  2. Loads historical prices from yfinance
  3. Loads raw CATS financial data from data/TICKER_2010_2025.csv
  4. Runs feature engineering pipeline
  5. Trains and saves the ML model

Run from the MED/ root:
    python -m backend.init_db
"""
import os, sys

ROOT = os.path.dirname(os.path.dirname(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from backend.database import init_db
from backend.services.price_service import fetch_and_store_prices
from backend.services.edgar_service import load_csv_financials
from backend.services.feature_service import run_feature_pipeline
from backend.services.ml_service import train_model

DATA_DIR = os.path.join(ROOT, "data")


def main():
    print("=== MED Database Initialization ===")

    print("\n[1/4] Initializing SQLite schema...")
    init_db()

    print("\n[2/4] Fetching price history from yfinance (this may take a minute)...")
    fetch_and_store_prices(full_history=True)  # full history on first run

    print("\n[3/4] Loading financial data from CSV files...")
    load_csv_financials(DATA_DIR)

    print("\n[4/4] Running feature engineering pipeline...")
    run_feature_pipeline()

    print("\n[5/5] Training ML model...")
    train_model()

    print("\n=== Initialization complete! ===")
    print("You can now start the backend: uvicorn backend.main:app --reload")


if __name__ == "__main__":
    main()
