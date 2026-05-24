import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
import os

load_dotenv()



DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")
DB_PORT = os.getenv("DB_PORT")
DB_PATH = os.path.join(os.path.dirname(__file__), "med.db")

TICKERS = ["AAPL", "AMZN", "GOOG", "META", "MSFT"]


CATS = [
    "revenue", "operating_income", "net_income", "gross_profit",
    "cost_of_goods_and_services_sold", "income_tax_expense",
    "nonoperating_income_expense", "research_and_development_expense",
    "total_assets", "total_liabilities", "total_stockholders_equity",
    "cash_and_cash_equivalents", "total_current_assets", "total_current_liabilities",
    "accounts_receivable", "accounts_payable", "retained_earnings",
    "property_plant_and_equipment",
    "net_cash_from_operating_activities", "net_cash_from_investing_activities",
    "net_cash_from_financing_activities", "net_change_in_cash",
    "earnings_per_share_basic_", "earnings_per_share_diluted_",
]



FEATURE_COLS = [
    "revenue_acceleration", "price_ma_4q", "accounts_payable_std_8",
    "net_change_in_cash_std_16", "price_momentum_6m", "quality_score_lag2",
    "revenue_growth_qoq", "profit_margin_lag2", "cash_and_cash_equivalents_std_8",
    "income_tax_expense_std_16", "nonoperating_income_expense_std_16",
    "total_liabilities_std_8", "earnings_volatility", "accounts_receivable_std_16",
    "retained_earnings_std_16", "profit_margin_lag4",
    "net_cash_from_financing_activities_std_8", "roa", "earnings_trend",
    "eps_acceleration", "debt_to_assets", "eps_growth_yoy",
    "total_assets_std_16", "total_current_liabilities_std_8", "cf_to_debt",
    "cost_of_goods_and_services_sold_std_16", "revenue_trend",
    "earnings_per_share_basic__std_8", "eps_surprise", "quality_score_lag4",
]




def get_connection():


    conn = psycopg2.connect(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASS,
        port=DB_PORT

    )

    return conn


def init_db():

    cats_cols = ", ".join(f"{c} DOUBLE PRECISION" for c in CATS)
    feature_cols = ", ".join(f"{c} DOUBLE PRECISION" for c in FEATURE_COLS)

    # W Postgresie używamy DOUBLE PRECISION zamiast REAL dla lepszej precyzji

    # i SERIAL zamiast AUTOINCREMENT
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(f"""

                CREATE TABLE IF NOT EXISTS prices (

                    ticker TEXT NOT NULL,
                    date   DATE NOT NULL,
                    open   DOUBLE PRECISION,
                    high   DOUBLE PRECISION,
                    low    DOUBLE PRECISION,
                    close  DOUBLE PRECISION,
                    volume BIGINT,
                    PRIMARY KEY (ticker, date)
                );

                CREATE TABLE IF NOT EXISTS financials (
                    ticker TEXT NOT NULL,
                    date   DATE NOT NULL,
                    {cats_cols},
                    PRIMARY KEY (ticker, date)
                );

                CREATE TABLE IF NOT EXISTS features (
                    ticker TEXT NOT NULL,
                    date   DATE NOT NULL,
                    close_price DOUBLE PRECISION,
                    {feature_cols},
                    PRIMARY KEY (ticker, date)
                );

                CREATE TABLE IF NOT EXISTS predictions (
                    ticker           TEXT NOT NULL,
                    date             DATE NOT NULL,
                    predicted_return DOUBLE PRECISION,
                    PRIMARY KEY (ticker, date)
                );

                CREATE TABLE IF NOT EXISTS model_metrics (
                    id             SERIAL PRIMARY KEY,
                    trained_at     TEXT,
                    r2             DOUBLE PRECISION,
                    mae            DOUBLE PRECISION,
                    rmse           DOUBLE PRECISION,
                    hit_rate       DOUBLE PRECISION,
                    n_features     INTEGER,
                    n_observations INTEGER
                );
            """)

        conn.commit()