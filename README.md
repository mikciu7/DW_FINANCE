# MED — Stock Financial Report Analyzer & Prediction App

Aplikacja webowa do analizy raportów finansowych spółek giełdowych oraz przewidywania 3-miesięcznych zwrotów akcji przy pomocy modelu Random Forest.

## Stack

| Warstwa | Technologie |
|---|---|
| Backend | Python · FastAPI · SQLite · APScheduler |
| ML | scikit-learn (RandomForest) · pandas · numpy |
| Dane | yfinance (ceny) · EDGAR via edgartools (raporty) |
| Frontend | React 18 · TypeScript · Vite · Recharts · TailwindCSS |
| Deploy | AWS EC2 (backend) · AWS S3 + CloudFront (frontend) |

---

## Spółki

`AAPL` · `AMZN` · `GOOG` · `META` · `MSFT`

Dane kwartalne 2010–2025 z raportów 10-Q / 10-K (EDGAR).

---

## Model

- **Algorytm:** Random Forest Regressor (200 drzew, max_depth=8)
- **Target:** zwrot ceny akcji po 90 dniach kalendarzowych (`return_3m`)
- **Features:** 30 zmiennych (standaryzowane wskaźniki finansowe, momentum cenowy, wskaźniki jakości)
- **Walidacja:** TimeSeriesSplit (5 foldów) — bez data leakage
- **Hit Rate kierunku:** ~67% (UP / DOWN)

---

## Struktura projektu

```
MED/
├── backend/
│   ├── main.py               # FastAPI app + APScheduler
│   ├── database.py           # SQLite schema
│   ├── scheduler.py          # codzienne odświeżanie danych
│   ├── init_db.py            # jednorazowa inicjalizacja bazy
│   ├── requirements.txt
│   ├── routers/
│   │   ├── financials.py     # /api/financials/price, /edgar
│   │   ├── features.py       # /api/financials/features
│   │   └── model.py          # /api/model/...
│   └── services/
│       ├── price_service.py  # yfinance → SQLite
│       ├── edgar_service.py  # EDGAR → SQLite
│       ├── feature_service.py # feature engineering (30 cech)
│       └── ml_service.py     # trening + predykcja
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   │   ├── Overview.tsx  # wykresy cen wszystkich spółek
│   │   │   ├── Financials.tsx # Income / Balance / CashFlow
│   │   │   ├── Features.tsx  # feature vs cena (dual-axis)
│   │   │   └── Model.tsx     # predykcja + feature importance
│   │   └── components/
│   └── package.json
├── deploy/
│   ├── ec2_setup.sh          # bootstrap Ubuntu EC2
│   └── s3_deploy.sh          # build + sync do S3
└── data/
    ├── AAPL_2010_2025.csv    # surowe dane finansowe z EDGAR
    ├── AMZN_2010_2025.csv
    └── ...
```

---

## Uruchomienie lokalne

### 1. Wymagania

```bash
cd MED
python -m venv med_env
# Windows:
med_env\Scripts\activate
# Linux/Mac:
source med_env/bin/activate

pip install -r backend/requirements.txt
```

### 2. Inicjalizacja bazy danych (jednorazowo)

```bash
python -m backend.init_db
```

Skrypt:
1. Tworzy schemat SQLite (`backend/med.db`)
2. Pobiera historię cen z yfinance (2010–dziś)
3. Wczytuje dane finansowe z CSV (`data/`)
4. Oblicza 30 cech modelu (feature engineering)
5. Trenuje model i zapisuje `backend/stock_prediction_model.pkl`

### 3. Uruchomienie backendu

```bash
uvicorn backend.main:app --reload
```

API dostępne pod: `http://localhost:8000`
Dokumentacja Swagger: `http://localhost:8000/docs`

### 4. Uruchomienie frontendu

```bash
cd frontend
npm install
npm run dev
```

Frontend dostępny pod: `http://localhost:5173`

---

## API Endpoints

| Metoda | Endpoint | Opis |
|---|---|---|
| GET | `/api/tickers` | Lista dostępnych spółek |
| GET | `/api/financials/price` | Ceny wszystkich spółek (daily) |
| GET | `/api/financials/price/{ticker}` | Ceny jednej spółki |
| GET | `/api/financials/edgar` | Dane finansowe wszystkich spółek (CATS) |
| GET | `/api/financials/edgar/{ticker}` | Dane finansowej jednej spółki |
| GET | `/api/financials/features` | Features wszystkich spółek |
| GET | `/api/financials/features/{ticker}` | Features + cena jednej spółki |
| GET | `/api/model/metrics` | Metryki modelu (R², MAE, Hit Rate) |
| GET | `/api/model/feature_importance` | Ważność zmiennych (top 30) |
| GET | `/api/model/predict/{ticker}` | Predykcja zwrotu na 3 miesiące |
| GET | `/health` | Health check |

---

## Zmienne finansowe (CATS)

Dane bez standaryzacji, bezpośrednio z raportów EDGAR:

**Income Statement:** `revenue`, `operating_income`, `net_income`, `gross_profit`, `cost_of_goods_and_services_sold`, `income_tax_expense`, `nonoperating_income_expense`, `research_and_development_expense`

**Balance Sheet:** `total_assets`, `total_liabilities`, `total_stockholders_equity`, `cash_and_cash_equivalents`, `total_current_assets`, `total_current_liabilities`, `accounts_receivable`, `accounts_payable`, `retained_earnings`, `property_plant_and_equipment`

**Cash Flow:** `net_cash_from_operating_activities`, `net_cash_from_investing_activities`, `net_cash_from_financing_activities`, `net_change_in_cash`

**EPS:** `earnings_per_share_basic_`, `earnings_per_share_diluted_`

---

## Automatyczne odświeżanie danych

APScheduler uruchomiony w tle FastAPI:

- **00:05** — pobranie nowych cen z yfinance (tylko od ostatniego wpisu)
- **01:00** — sprawdzenie nowych raportów 10-Q/10-K w EDGAR → jeśli nowe: feature engineering → retrain modelu

---

## Deploy na AWS

### Backend (EC2)

```bash
chmod +x deploy/ec2_setup.sh
# Na instancji EC2 Ubuntu 22.04:
./deploy/ec2_setup.sh
```

### Frontend (S3 + CloudFront)

```bash
# Ustaw zmienne środowiskowe:
export BUCKET_NAME=med-frontend-bucket
export CF_DISTRIBUTION_ID=XXXXXXXXXXXXX
export VITE_API_URL=http://<EC2-PUBLIC-IP>/api

chmod +x deploy/s3_deploy.sh
./deploy/s3_deploy.sh
```

---

## Autorzy

Projekt roczny — Metody Eksploracji Danych
Mikołaj Ciuba
