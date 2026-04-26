import { useEffect, useState, useMemo } from "react";
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
    const [rows, setRows] = useState<FeatureRow[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        setLoading(true);
        fetchFeatures(ticker)
            .then(setRows)
            .finally(() => setLoading(false));
    }, [ticker]);

    const chartData = useMemo(() =>
        rows.map((r) => ({
            date: r.date?.slice(0, 7),
            [feature]: r[feature] as number | null,
            price: r.close_price,
        })), [rows, feature]);

    return (
        <div className="max-w-7xl mx-auto w-full p-6 lg:p-10 space-y-8">
            <h1 className="text-2xl font-bold text-white mb-1">Features Modelu</h1>
            <p className="text-slate-400 text-sm mb-4">30 zmiennych wejściowych (standaryzowane) vs cena akcji</p>

            {/* Ticker selector */}
            <div className="flex gap-2 mb-4">
                {TICKERS.map((t) => (
                    <button
                        key={t}
                        onClick={() => setTicker(t)}
                        className={`px-4 py-1.5 rounded text-sm font-medium transition-colors ${
                            ticker === t ? "bg-blue-600 text-white" : "bg-slate-700 text-slate-300 hover:bg-slate-600"
                        }`}
                    >
                        {t}
                    </button>
                ))}
            </div>

            {/* Feature selector */}
            <div className="flex items-center gap-3 mb-4">
                <span className="text-slate-400 text-sm">Feature:</span>
                <select
                    value={feature}
                    onChange={(e) => setFeature(e.target.value)}
                    className="bg-slate-700 text-slate-200 text-sm rounded px-3 py-1.5 border border-slate-600"
                >
                    {FEATURE_LIST.map((f) => (
                        <option key={f} value={f}>{f}</option>
                    ))}
                </select>
            </div>

            {loading ? (
                <div className="flex items-center justify-center h-64 text-slate-400">Ładowanie...</div>
            ) : (
                <div className="bg-slate-800 rounded-xl p-4">
                    <div className="flex gap-4 text-xs text-slate-400 mb-2">
            <span className="flex items-center gap-1">
              <span className="w-3 h-0.5 bg-blue-400 inline-block"></span> {feature}
            </span>
                        <span className="flex items-center gap-1">
              <span className="w-3 h-0.5 bg-amber-400 inline-block"></span> Cena (prawa oś)
            </span>
                    </div>
                    <ResponsiveContainer width="100%" height={400}>
                        <ComposedChart data={chartData}>
                            <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                            <XAxis dataKey="date" tick={{ fill: "#94a3b8", fontSize: 10 }} interval="preserveStartEnd" />
                            <YAxis
                                yAxisId="left"
                                tick={{ fill: "#94a3b8", fontSize: 10 }}
                                tickFormatter={(v) => v.toFixed(2)}
                            />
                            <YAxis
                                yAxisId="right"
                                orientation="right"
                                tick={{ fill: "#fbbf24", fontSize: 10 }}
                                tickFormatter={(v) => `$${v.toFixed(0)}`}
                                width={65}
                            />
                            <Tooltip
                                contentStyle={{ background: "#1e293b", border: "1px solid #334155", borderRadius: 8 }}
                                labelStyle={{ color: "#cbd5e1" }}
                            />
                            <Bar yAxisId="left" dataKey={feature} fill="#3b82f6" opacity={0.7} radius={[2, 2, 0, 0]} />
                            <Line yAxisId="right" type="monotone" dataKey="price" stroke="#fbbf24" dot={false} strokeWidth={2} />
                        </ComposedChart>
                    </ResponsiveContainer>
                </div>
            )}
        </div>
    );
}