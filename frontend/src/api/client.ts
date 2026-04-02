import axios from "axios";

const BASE = import.meta.env.VITE_API_URL ?? "/api";

const api = axios.create({ baseURL: BASE });

export interface PriceRow {
  ticker: string;
  date: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface FinancialRow {
  ticker: string;
  date: string;
  revenue: number | null;
  operating_income: number | null;
  net_income: number | null;
  gross_profit: number | null;
  cost_of_goods_and_services_sold: number | null;
  income_tax_expense: number | null;
  nonoperating_income_expense: number | null;
  research_and_development_expense: number | null;
  total_assets: number | null;
  total_liabilities: number | null;
  total_stockholders_equity: number | null;
  cash_and_cash_equivalents: number | null;
  total_current_assets: number | null;
  total_current_liabilities: number | null;
  accounts_receivable: number | null;
  accounts_payable: number | null;
  retained_earnings: number | null;
  property_plant_and_equipment: number | null;
  net_cash_from_operating_activities: number | null;
  net_cash_from_investing_activities: number | null;
  net_cash_from_financing_activities: number | null;
  net_change_in_cash: number | null;
  earnings_per_share_basic_: number | null;
  earnings_per_share_diluted_: number | null;
  [key: string]: unknown;
}

export interface FeatureRow {
  ticker: string;
  date: string;
  close_price: number | null;
  [key: string]: unknown;
}

export interface FeatureImportance {
  feature: string;
  importance: number;
}

export interface ModelMetrics {
  r2: number;
  r2_std: number;
  rmse: number;
  mae: number;
  hit_rate: number;
}

export interface Prediction {
  ticker: string;
  date: string;
  predicted_return_3m: number;
  direction: "UP" | "DOWN";
  close_price: number;
}

export const fetchTickers = () => api.get<string[]>("/tickers").then((r) => r.data);
export const fetchPrices = (ticker?: string) =>
  api.get<PriceRow[]>(ticker ? `/financials/price/${ticker}` : "/financials/price").then((r) => r.data);
export const fetchEdgar = (ticker?: string) =>
  api.get<FinancialRow[]>(ticker ? `/financials/edgar/${ticker}` : "/financials/edgar").then((r) => r.data);
export const fetchFeatures = (ticker?: string) =>
  api.get<FeatureRow[]>(ticker ? `/financials/features/${ticker}` : "/financials/features").then((r) => r.data);
export const fetchModelMetrics = () => api.get<ModelMetrics>("/model/metrics").then((r) => r.data);
export const fetchFeatureImportance = () =>
  api.get<FeatureImportance[]>("/model/feature_importance").then((r) => r.data);
export const fetchPrediction = (ticker: string) =>
  api.get<Prediction>(`/model/predict/${ticker}`).then((r) => r.data);
