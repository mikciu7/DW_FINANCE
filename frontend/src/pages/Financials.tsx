import { useEffect, useState, useMemo, useCallback } from "react";
import { fetchEdgar } from "../api/client";
import type { FinancialRow } from "../api/client";
import { DateRangeBar } from "../components/DateRangeBar";
import {
    LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid,
    ReferenceLine, Legend,
} from "recharts";

const TICKERS = ["AAPL", "AMD", "AMZN", "AVGO", "GOOG", "META", "MSFT", "NVDA", "ORCL", "TSLA"];

const COLORS: Record<string, string> = {
    AAPL: "#60a5fa",
    AMD:  "#fb923c",
    AMZN: "#f59e0b",
    AVGO: "#e879f9",
    GOOG: "#34d399",
    META: "#a78bfa",
    MSFT: "#f87171",
    NVDA: "#4ade80",
    ORCL: "#f43f5e",
    TSLA: "#38bdf8",
};

const INCOME_COLS = [
    { key: "revenue", label: "Revenue" },
    { key: "gross_profit", label: "Gross Profit" },
    { key: "operating_income", label: "Operating Income" },
    { key: "net_income", label: "Net Income" },
    { key: "cost_of_goods_and_services_sold", label: "COGS" },
    { key: "research_and_development_expense", label: "R&D Expense" },
    { key: "income_tax_expense", label: "Income Tax" },
    { key: "nonoperating_income_expense", label: "Non-Op Income" },
];

const BALANCE_COLS = [
    { key: "total_assets", label: "Total Assets" },
    { key: "total_liabilities", label: "Total Liabilities" },
    { key: "total_stockholders_equity", label: "Equity" },
    { key: "cash_and_cash_equivalents", label: "Cash & Equivalents" },
    { key: "total_current_assets", label: "Current Assets" },
    { key: "total_current_liabilities", label: "Current Liabilities" },
    { key: "accounts_receivable", label: "Accounts Receivable" },
    { key: "accounts_payable", label: "Accounts Payable" },
    { key: "retained_earnings", label: "Retained Earnings" },
    { key: "property_plant_and_equipment", label: "PP&E" },
];

const CASHFLOW_COLS = [
    { key: "net_cash_from_operating_activities", label: "Operating CF" },
    { key: "net_cash_from_investing_activities", label: "Investing CF" },
    { key: "net_cash_from_financing_activities", label: "Financing CF" },
    { key: "net_change_in_cash", label: "Net Change in Cash" },
];

const TABS = [
    { id: "income", label: "Income Statement", cols: INCOME_COLS },
    { id: "balance", label: "Balance Sheet", cols: BALANCE_COLS },
    { id: "cashflow", label: "Cash Flow", cols: CASHFLOW_COLS },
];

const fmt = (v: number | null) => {
    if (v == null || isNaN(v)) return "—";
    const abs = Math.abs(v);
    if (abs >= 1_000_000) return `$${(v / 1_000_000).toFixed(2)}T`;
    if (abs >= 1_000) return `$${(v / 1_000).toFixed(2)}B`;
    if (abs >= 1) return `$${v.toFixed(2)}M`;
    return `$${v.toFixed(4)}`;
};

export default function Financials() {
    const [selectedTickers, setSelected] = useState<Set<string>>(new Set(["AAPL"]));
    const [primaryTicker, setPrimary]    = useState("AAPL");
    const [tab, setTab]                  = useState("income");
    const [chartMetric, setChartMetric]  = useState("revenue");
    const [tickerData, setTickerData]    = useState<Map<string, FinancialRow[]>>(new Map());
    const [fetchingSet, setFetchingSet]  = useState<Set<string>>(new Set(["AAPL"]));
    const [dateRange, setDateRange]      = useState({ start: "", end: "" });

    const activeTickers = TICKERS.filter((t) => selectedTickers.has(t));

    const fetchTicker = useCallback((t: string) => {
        setFetchingSet((prev) => new Set(prev).add(t));
        fetchEdgar(t)
            .then((data) => setTickerData((prev) => new Map(prev).set(t, data)))
            .finally(() => setFetchingSet((prev) => { const n = new Set(prev); n.delete(t); return n; }));
    }, []);

    // Load AAPL on mount
    useEffect(() => { fetchTicker("AAPL"); }, []);

    const toggleTicker = (t: string) => {
        setSelected((prev) => {
            const next = new Set(prev);
            if (next.has(t)) {
                next.delete(t);
                if (primaryTicker === t) {
                    const remaining = TICKERS.filter((x) => next.has(x));
                    setPrimary(remaining[0] ?? "");
                }
            } else {
                next.add(t);
                setPrimary(t);
                if (!tickerData.has(t)) fetchTicker(t);
            }
            return next;
        });
    };

    const loading = fetchingSet.size > 0;

    // Date bounds: union of all selected tickers
    const { minDate, maxDate } = useMemo(() => {
        const dates: string[] = [];
        for (const t of activeTickers) {
            (tickerData.get(t) ?? []).forEach((r) => { if (r.date) dates.push(r.date); });
        }
        if (!dates.length) return { minDate: "", maxDate: "" };
        dates.sort();
        return { minDate: dates[0], maxDate: dates[dates.length - 1] };
    }, [tickerData, activeTickers]);

    useEffect(() => {
        if (minDate && maxDate) setDateRange({ start: minDate, end: maxDate });
    }, [minDate, maxDate]);

    const activeCols = TABS.find((t) => t.id === tab)?.cols ?? [];

    // Chart data: one row per date, one key per ticker
    const chartData = useMemo(() => {
        const byDate: Record<string, Record<string, number | string | null>> = {};
        for (const t of activeTickers) {
            for (const r of tickerData.get(t) ?? []) {
                if (!r.date) continue;
                if (dateRange.start && r.date < dateRange.start) continue;
                if (dateRange.end && r.date > dateRange.end) continue;
                const key = r.date.slice(0, 7);
                if (!byDate[key]) byDate[key] = { date: key };
                byDate[key][t] = r[chartMetric] as number | null;
            }
        }
        return Object.values(byDate).sort((a, b) => (a.date as string).localeCompare(b.date as string));
    }, [tickerData, activeTickers, chartMetric, dateRange]);

    // Table: primary ticker only
    const filteredRows = useMemo(() => {
        const rows = tickerData.get(primaryTicker) ?? [];
        if (!dateRange.start || !dateRange.end) return rows;
        return rows.filter((r) => r.date >= dateRange.start && r.date <= dateRange.end);
    }, [tickerData, primaryTicker, dateRange]);

    // Period delta per ticker for selected metric
    const periodDeltas = useMemo(() => {
        return activeTickers.map((t) => {
            const rows = (tickerData.get(t) ?? [])
                .filter((r) => r.date >= dateRange.start && r.date <= dateRange.end);
            const vals = rows.map((r) => r[chartMetric] as number | null).filter((v): v is number => v != null);
            if (vals.length < 2) return { ticker: t, pct: null, last: null };
            const first = vals[0], last = vals[vals.length - 1];
            return { ticker: t, pct: ((last - first) / Math.abs(first)) * 100, last };
        });
    }, [tickerData, activeTickers, chartMetric, dateRange]);

    return (
        <div className="max-w-7xl mx-auto w-full p-6 lg:p-10 space-y-6">
            <div>
                <h1 className="text-2xl font-bold text-white mb-1">Raporty Finansowe</h1>
                <p className="text-slate-400 text-sm">Dane kwartalne z EDGAR</p>
            </div>

            {/* Multi-select ticker buttons */}
            <div className="flex gap-2 flex-wrap">
                {TICKERS.map((t) => {
                    const active = selectedTickers.has(t);
                    const color  = COLORS[t];
                    return (
                        <button
                            key={t}
                            onClick={() => toggleTicker(t)}
                            className={`px-4 py-1.5 rounded text-sm font-medium transition-all border ${
                                active
                                    ? "shadow-sm"
                                    : "bg-slate-700 text-slate-400 hover:bg-slate-600 border-transparent"
                            }`}
                            style={active ? { backgroundColor: color + "22", borderColor: color, color } : {}}
                        >
                            {t}
                        </button>
                    );
                })}
            </div>

            <DateRangeBar
                minDate={minDate}
                maxDate={maxDate}
                start={dateRange.start}
                end={dateRange.end}
                onStartChange={(v) => setDateRange((p) => ({ ...p, start: v }))}
                onEndChange={(v) => setDateRange((p) => ({ ...p, end: v }))}
                dataCount={chartData.length}
                dataLabel="kwartały"
                visiblePresets={["1Y", "3Y", "5Y", "Max"]}
            />

            {/* Tab selector */}
            <div className="flex gap-1 border-b border-slate-700">
                {TABS.map((t) => (
                    <button
                        key={t.id}
                        onClick={() => { setTab(t.id); setChartMetric(t.cols[0].key); }}
                        className={`px-4 py-2 text-sm font-medium transition-colors ${
                            tab === t.id
                                ? "border-b-2 border-blue-500 text-blue-400"
                                : "text-slate-400 hover:text-slate-200"
                        }`}
                    >
                        {t.label}
                    </button>
                ))}
            </div>

            {loading && activeTickers.length === 0 ? (
                <div className="flex items-center justify-center h-40 text-slate-400">Ładowanie...</div>
            ) : (
                <>
                    {/* Chart */}
                    <div className="bg-slate-800 rounded-xl p-4">
                        <div className="flex items-center gap-4 mb-3 flex-wrap">
                            <div className="flex items-center gap-2">
                                <span className="text-slate-400 text-sm">Metryka:</span>
                                <select
                                    value={chartMetric}
                                    onChange={(e) => setChartMetric(e.target.value)}
                                    className="bg-slate-700 text-slate-200 text-sm rounded px-2 py-1 border border-slate-600"
                                >
                                    {activeCols.map((c) => (
                                        <option key={c.key} value={c.key}>{c.label}</option>
                                    ))}
                                </select>
                            </div>

                            {/* Per-ticker delta badges */}
                            <div className="ml-auto flex gap-2 flex-wrap">
                                {periodDeltas.map(({ ticker, pct }) => pct !== null && (
                                    <span key={ticker} className="text-xs font-mono font-bold px-2 py-0.5 rounded"
                                        style={{
                                            color: COLORS[ticker],
                                            background: COLORS[ticker] + "22",
                                            border: `1px solid ${COLORS[ticker]}44`,
                                        }}
                                    >
                                        {ticker} {pct >= 0 ? "+" : ""}{pct.toFixed(1)}%
                                    </span>
                                ))}
                            </div>
                        </div>

                        <ResponsiveContainer width="100%" height={480}>
                            <LineChart data={chartData}>
                                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                                <XAxis dataKey="date" tick={{ fill: "#94a3b8", fontSize: 10 }} interval="preserveStartEnd" />
                                <YAxis
                                    tick={{ fill: "#94a3b8", fontSize: 10 }}
                                    tickFormatter={fmt}
                                    width={75}
                                />
                                <Tooltip
                                    contentStyle={{ background: "#1e293b", border: "1px solid #334155", borderRadius: 8 }}
                                    labelStyle={{ color: "#cbd5e1" }}
                                    formatter={(v, name) => [fmt(Number(v)), name]}
                                />
                                <ReferenceLine y={0} stroke="#475569" strokeDasharray="4 4" />
                                <Legend wrapperStyle={{ color: "#94a3b8" }} />
                                {activeTickers.map((t) => (
                                    <Line
                                        key={t}
                                        type="monotone"
                                        dataKey={t}
                                        stroke={COLORS[t] ?? "#94a3b8"}
                                        dot={{ r: 3, fill: COLORS[t] ?? "#94a3b8", strokeWidth: 0 }}
                                        activeDot={{ r: 5 }}
                                        strokeWidth={2}
                                        connectNulls
                                    />
                                ))}
                            </LineChart>
                        </ResponsiveContainer>
                    </div>

                    {/* Table with primary ticker selector */}
                    {primaryTicker && (
                        <div className="bg-slate-800 rounded-xl overflow-auto">
                            {activeTickers.length > 1 && (
                                <div className="flex items-center gap-2 px-4 pt-3 pb-1">
                                    <span className="text-xs text-slate-500 uppercase tracking-widest font-bold">Tabela dla:</span>
                                    {activeTickers.map((t) => (
                                        <button
                                            key={t}
                                            onClick={() => setPrimary(t)}
                                            className="px-2.5 py-0.5 rounded text-xs font-bold transition-all border"
                                            style={primaryTicker === t
                                                ? { color: COLORS[t], background: COLORS[t] + "22", borderColor: COLORS[t] + "66" }
                                                : { color: "#64748b", background: "transparent", borderColor: "transparent" }
                                            }
                                        >
                                            {t}
                                        </button>
                                    ))}
                                </div>
                            )}
                            <table className="w-full text-sm">
                                <thead>
                                    <tr className="border-b border-slate-700">
                                        <th className="text-left px-4 py-2 text-slate-400 font-medium sticky left-0 bg-slate-800">
                                            Quarter
                                        </th>
                                        {activeCols.map((c) => (
                                            <th key={c.key} className="text-right px-4 py-2 text-slate-400 font-medium whitespace-nowrap">
                                                {c.label}
                                            </th>
                                        ))}
                                    </tr>
                                </thead>
                                <tbody>
                                    {[...filteredRows].reverse().map((r) => (
                                        <tr key={r.date} className="border-b border-slate-700/50 hover:bg-slate-700/30 transition-colors">
                                            <td className="px-4 py-2 text-slate-300 font-mono sticky left-0 bg-slate-800">
                                                {r.date?.slice(0, 10)}
                                            </td>
                                            {activeCols.map((c) => (
                                                <td
                                                    key={c.key}
                                                    className={`px-4 py-2 text-right font-mono tabular-nums ${
                                                        (r[c.key] as number) < 0 ? "text-red-400" : "text-slate-200"
                                                    }`}
                                                >
                                                    {fmt(r[c.key] as number | null)}
                                                </td>
                                            ))}
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    )}
                </>
            )}
        </div>
    );
}
