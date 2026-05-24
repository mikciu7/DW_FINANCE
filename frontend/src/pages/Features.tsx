import { useEffect, useState, useMemo } from "react";
import { fetchFeatures } from "../api/client";
import type { FeatureRow } from "../api/client";
import { DateRangeBar } from "../components/DateRangeBar";
import {
    ComposedChart, Line, Bar, XAxis, YAxis, Tooltip,
    ResponsiveContainer, CartesianGrid,
} from "recharts";

const TICKERS = ["AAPL", "AMD", "AMZN", "AVGO", "GOOG", "META", "MSFT", "NVDA", "ORCL", "TSLA"];

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
    const [dateRange, setDateRange] = useState({ start: "", end: "" });

    useEffect(() => {
        setLoading(true);
        setDateRange({ start: "", end: "" });
        fetchFeatures(ticker)
            .then(setRows)
            .finally(() => setLoading(false));
    }, [ticker]);

    // Bounds from loaded data
    const { minDate, maxDate } = useMemo(() => {
        if (!rows.length) return { minDate: "", maxDate: "" };
        const dates = rows.map((r: FeatureRow) => r.date).filter(Boolean).sort() as string[];
        return { minDate: dates[0], maxDate: dates[dates.length - 1] };
    }, [rows]);

    // Init to Max on load; reset on ticker change
    useEffect(() => {
        if (minDate && maxDate) setDateRange({ start: minDate, end: maxDate });
    }, [minDate, maxDate]);

    // Filtered + chart-ready data
    const chartData = useMemo(() =>
        rows
            .filter((r: FeatureRow) => {
                if (!dateRange.start || !dateRange.end) return true;
                return r.date >= dateRange.start && r.date <= dateRange.end;
            })
            .map((r: FeatureRow) => ({
                date: (r.date as string)?.slice(0, 7),
                [feature]: r[feature] as number | null,
                price: r.close_price,
            })),
        [rows, feature, dateRange]
    );

    // Stats for selected feature in range
    const featureStats = useMemo(() => {
        const vals = chartData
            .map((d) => d[feature] as number | null)
            .filter((v): v is number => v != null);
        if (!vals.length) return null;
        const min = Math.min(...vals);
        const max = Math.max(...vals);
        const avg = vals.reduce((a, b) => a + b, 0) / vals.length;
        const last = vals[vals.length - 1];
        const first = vals[0];
        const pct = first !== 0 ? ((last - first) / Math.abs(first)) * 100 : null;
        return { min, max, avg, last, first, pct };
    }, [chartData, feature]);

    return (
        <div className="max-w-7xl mx-auto w-full p-6 lg:p-10 space-y-6">
            <div>
                <h1 className="text-2xl font-bold text-white mb-1">Features Modelu</h1>
                <p className="text-slate-400 text-sm">30 zmiennych wejściowych (standaryzowane) vs cena akcji</p>
            </div>

            {/* Ticker selector */}
            <div className="flex gap-2">
                {TICKERS.map((t) => (
                    <button
                        key={t}
                        onClick={() => setTicker(t)}
                        className={`px-4 py-1.5 rounded text-sm font-medium transition-colors ${
                            ticker === t
                                ? "bg-blue-600 text-white"
                                : "bg-slate-700 text-slate-300 hover:bg-slate-600"
                        }`}
                    >
                        {t}
                    </button>
                ))}
            </div>

            {/* OLAP Time Slice — suwaki */}
            <DateRangeBar
                minDate={minDate}
                maxDate={maxDate}
                start={dateRange.start}
                end={dateRange.end}
                onStartChange={(v) => setDateRange((p) => ({ ...p, start: v }))}
                onEndChange={(v) => setDateRange((p) => ({ ...p, end: v }))}
                dataCount={chartData.length}
                dataLabel="kwartały"
            />

            {/* Feature selector + stats row */}
            <div className="flex items-center gap-4 flex-wrap">
                <div className="flex items-center gap-3">
                    <span className="text-slate-400 text-sm shrink-0">Feature:</span>
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

                {featureStats && (
                    <div className="ml-auto flex gap-4 text-xs font-mono">
                        <span className="text-slate-500">
                            min <span className="text-slate-200">{featureStats.min.toFixed(3)}</span>
                        </span>
                        <span className="text-slate-500">
                            avg <span className="text-slate-200">{featureStats.avg.toFixed(3)}</span>
                        </span>
                        <span className="text-slate-500">
                            max <span className="text-slate-200">{featureStats.max.toFixed(3)}</span>
                        </span>
                        {featureStats.pct !== null && (
                            <span className={`font-bold px-2 py-0.5 rounded ${
                                featureStats.pct >= 0
                                    ? "text-emerald-400 bg-emerald-400/10"
                                    : "text-red-400 bg-red-400/10"
                            }`}>
                                {featureStats.pct >= 0 ? "+" : ""}{featureStats.pct.toFixed(1)}%
                            </span>
                        )}
                    </div>
                )}
            </div>

            {loading ? (
                <div className="flex items-center justify-center h-64 text-slate-400">Ładowanie...</div>
            ) : (
                <div className="bg-slate-800 rounded-xl p-4">
                    <div className="flex gap-4 text-xs text-slate-400 mb-2">
                        <span className="flex items-center gap-1">
                            <span className="w-3 h-0.5 bg-blue-400 inline-block" /> {feature}
                        </span>
                        <span className="flex items-center gap-1">
                            <span className="w-3 h-0.5 bg-amber-400 inline-block" /> Cena (prawa oś)
                        </span>
                    </div>
                    <ResponsiveContainer width="100%" height={400}>
                        <ComposedChart data={chartData}>
                            <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                            <XAxis
                                dataKey="date"
                                tick={{ fill: "#94a3b8", fontSize: 10 }}
                                interval="preserveStartEnd"
                            />
                            <YAxis
                                yAxisId="left"
                                tick={{ fill: "#94a3b8", fontSize: 10 }}
                                tickFormatter={(v: number) => v.toFixed(2)}
                            />
                            <YAxis
                                yAxisId="right"
                                orientation="right"
                                tick={{ fill: "#fbbf24", fontSize: 10 }}
                                tickFormatter={(v: number) => `$${v.toFixed(0)}`}
                                width={65}
                            />
                            <Tooltip
                                contentStyle={{ background: "#1e293b", border: "1px solid #334155", borderRadius: 8 }}
                                labelStyle={{ color: "#cbd5e1" }}
                            />
                            <Bar yAxisId="left" dataKey={feature} fill="#3b82f6" opacity={0.7} radius={[2, 2, 0, 0]} />
                            <Line
                                yAxisId="right"
                                type="monotone"
                                dataKey="price"
                                stroke="#fbbf24"
                                dot={false}
                                strokeWidth={2}
                                connectNulls
                            />
                        </ComposedChart>
                    </ResponsiveContainer>
                </div>
            )}
        </div>
    );
}
