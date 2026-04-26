import { useState, useMemo } from "react";
import { useQuery } from "@tanstack/react-query"; // Importujemy hook do cachowania
import { fetchFeatures } from "../api/client";
import type { FeatureRow } from "../api/client";
import {
    ComposedChart, Line, Bar, XAxis, YAxis, Tooltip,
    ResponsiveContainer, CartesianGrid,
} from "recharts";

const TICKERS = ["AAPL", "AMZN", "GOOG", "META", "MSFT"];

const FEATURE_LIST = [
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
];

export default function Features() {
    const [ticker, setTicker] = useState("AAPL");
    const [feature, setFeature] = useState("revenue_acceleration");

    // Implementacja cachowania danych dla konkretnego tickera
    const { data: rows = [], isLoading } = useQuery({
        queryKey: ["features", ticker], // Unikalny klucz cache per ticker
        queryFn: () => fetchFeatures(ticker),
        // staleTime (5 min) i gcTime (30 min) są dziedziczone z main.tsx
    });

    const chartData = useMemo(() =>
        rows.map((r) => ({
            date: r.date?.slice(0, 7),
            [feature]: r[feature] as number | null,
            price: r.close_price,
        })), [rows, feature]);

    return (
        <div className="p-6">
            <div className="mb-6">
                <h1 className="text-2xl font-bold text-white mb-1">Features Modelu</h1>
                <p className="text-slate-400 text-sm">30 zmiennych wejściowych (standaryzowane) vs cena akcji</p>
            </div>

            {/* Ticker selector */}
            <div className="flex gap-2 mb-6">
                {TICKERS.map((t) => (
                    <button
                        key={t}
                        onClick={() => setTicker(t)}
                        className={`px-4 py-1.5 rounded text-sm font-medium transition-all ${
                            ticker === t
                                ? "bg-blue-600 text-white shadow-lg shadow-blue-500/20"
                                : "bg-slate-700 text-slate-300 hover:bg-slate-600"
                        }`}
                    >
                        {t}
                    </button>
                ))}
            </div>

            {/* Feature selector */}
            <div className="flex items-center gap-3 mb-6 bg-slate-800/50 p-3 rounded-lg border border-slate-700/50 w-fit">
                <span className="text-slate-400 text-sm font-medium">Aktywna cecha:</span>
                <select
                    value={feature}
                    onChange={(e) => setFeature(e.target.value)}
                    className="bg-slate-900 text-blue-400 text-sm rounded px-3 py-1.5 border border-slate-700 focus:outline-none focus:ring-1 focus:ring-blue-500 cursor-pointer"
                >
                    {FEATURE_LIST.map((f) => (
                        <option key={f} value={f}>{f.replace(/_/g, ' ')}</option>
                    ))}
                </select>
            </div>

            {isLoading ? (
                <div className="flex flex-col items-center justify-center h-80 text-slate-400 gap-4">
                    <div className="animate-spin rounded-full h-10 w-10 border-t-2 border-b-2 border-blue-500"></div>
                    <span className="animate-pulse">Analizowanie cech dla {ticker}...</span>
                </div>
            ) : (
                <div className="bg-slate-800 border border-slate-700/50 rounded-2xl p-6 shadow-2xl transition-all">
                    <div className="flex gap-6 text-[11px] font-semibold uppercase tracking-wider mb-6">
                        <div className="flex items-center gap-2">
                            <div className="w-4 h-4 rounded bg-blue-500/80 shadow-[0_0_8px_rgba(59,130,246,0.4)]"></div>
                            <span className="text-blue-400">{feature.replace(/_/g, ' ')}</span>
                        </div>
                        <div className="flex items-center gap-2">
                            <div className="w-4 h-4 rounded bg-amber-400 shadow-[0_0_8px_rgba(251,191,36,0.4)]"></div>
                            <span className="text-amber-400">Cena zamknięcia ($)</span>
                        </div>
                    </div>

                    <div className="h-[450px]">
                        <ResponsiveContainer width="100%" height="100%">
                            <ComposedChart data={chartData}>
                                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
                                <XAxis
                                    dataKey="date"
                                    tick={{ fill: "#64748b", fontSize: 10 }}
                                    interval="preserveStartEnd"
                                    minTickGap={40}
                                />
                                <YAxis
                                    yAxisId="left"
                                    tick={{ fill: "#3b82f6", fontSize: 10 }}
                                    tickFormatter={(v) => v.toFixed(2)}
                                    stroke="#3b82f6"
                                    strokeWidth={0.5}
                                />
                                <YAxis
                                    yAxisId="right"
                                    orientation="right"
                                    tick={{ fill: "#fbbf24", fontSize: 10 }}
                                    tickFormatter={(v) => `$${v.toLocaleString()}`}
                                    width={65}
                                    stroke="#fbbf24"
                                    strokeWidth={0.5}
                                />
                                <Tooltip
                                    contentStyle={{
                                        background: "#0f172a",
                                        border: "1px solid #334155",
                                        borderRadius: 12,
                                        boxShadow: "0 20px 25px -5px rgba(0, 0, 0, 0.3)"
                                    }}
                                    itemStyle={{ fontSize: '12px', padding: '2px 0' }}
                                    labelStyle={{ color: "#94a3b8", marginBottom: '4px', fontWeight: 'bold' }}
                                />
                                <Bar
                                    yAxisId="left"
                                    dataKey={feature}
                                    fill="#3b82f6"
                                    opacity={0.6}
                                    radius={[4, 4, 0, 0]}
                                    animationDuration={1500}
                                />
                                <Line
                                    yAxisId="right"
                                    type="monotone"
                                    dataKey="price"
                                    stroke="#fbbf24"
                                    dot={false}
                                    strokeWidth={3}
                                    animationDuration={2000}
                                />
                            </ComposedChart>
                        </ResponsiveContainer>
                    </div>
                </div>
            )}
        </div>
    );
}