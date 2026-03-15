import sqlite3
import os

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
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    cats_cols = ", ".join(f"{c} REAL" for c in CATS)
    feature_cols = ", ".join(f"{c} REAL" for c in FEATURE_COLS)

    with get_connection() as conn:
        conn.executescript(f"""
            CREATE TABLE IF NOT EXISTS prices (
                ticker TEXT NOT NULL,
                date   TEXT NOT NULL,
                open   REAL,
                high   REAL,
                low    REAL,
                close  REAL,
                volume INTEGER,
                PRIMARY KEY (ticker, date)
            );

            CREATE TABLE IF NOT EXISTS financials (
                ticker TEXT NOT NULL,
                date   TEXT NOT NULL,
                {cats_cols},
                PRIMARY KEY (ticker, date)
            );

            CREATE TABLE IF NOT EXISTS features (
                ticker TEXT NOT NULL,
                date   TEXT NOT NULL,
                close_price REAL,
                {feature_cols},
                PRIMARY KEY (ticker, date)
            );

            CREATE TABLE IF NOT EXISTS predictions (
                ticker           TEXT NOT NULL,
                date             TEXT NOT NULL,
                predicted_return REAL,
                PRIMARY KEY (ticker, date)
            );

            CREATE TABLE IF NOT EXISTS model_metrics (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                trained_at   TEXT,
                r2           REAL,
                mae          REAL,
                rmse         REAL,
                hit_rate     REAL,
                n_features   INTEGER,
                n_observations INTEGER
            );
        """)
