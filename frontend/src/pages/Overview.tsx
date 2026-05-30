import { useEffect, useState, useMemo } from "react";
import { TrendingUp, TrendingDown, Minus } from "lucide-react";
import { fetchPrices } from "../api/client";
import type { PriceRow } from "../api/client";
import { DateRangeBar } from "../components/DateRangeBar";
import { useViewContext } from "../context/ViewContext";
import {
    LineChart, Line, XAxis, YAxis, Tooltip, Legend,
    ResponsiveContainer, CartesianGrid,
} from "recharts";

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

type GroupedData = { date: string; [ticker: string]: number | string };

const fmt   = (v: number) => `$${v.toFixed(2)}`;
const fmtPct = (v: number) => `${v >= 0 ? "+" : ""}${v.toFixed(2)}%`;

interface OverviewProps {
    selectedTickers: Set<string>;
    onSelectedChange: (s: Set<string>) => void;
}

export default function Overview({ selectedTickers, onSelectedChange: setSelected }: OverviewProps) {
    const { setView } = useViewContext();
    const [rows, setRows]         = useState<PriceRow[]>([]);
    const [loading, setLoading]   = useState(true);
    const [dateRange, setDateRange] = useState({ start: "", end: "" });

    useEffect(() => {
        setView({
            page: "Ceny Akcji",
            tickers: [...selectedTickers],
            dateRange: dateRange.start ? dateRange : undefined,
        });
    }, [selectedTickers, dateRange]);

    useEffect(() => {
        fetchPrices()
            .then((data) => { setRows(data); })
            .catch((err) => { console.error("[Overview] ERROR:", err?.message); })
            .finally(() => setLoading(false));
    }, []);

    const { minDate, maxDate } = useMemo(() => {
        if (!rows.length) return { minDate: "", maxDate: "" };
        const dates = [...new Set(rows.map((r) => r.date))].sort();
        return { minDate: dates[0], maxDate: dates[dates.length - 1] };
    }, [rows]);

    // Init zakres 5Y + zaznacz wszystkie tickery po załadowaniu
    useEffect(() => {
        if (!maxDate) return;
        const d = new Date(maxDate);
        d.setFullYear(d.getFullYear() - 5);
        const candidate = d.toISOString().slice(0, 10);
        setDateRange({ start: candidate < minDate ? minDate : candidate, end: maxDate });
    }, [minDate, maxDate]);

    const allTickers = useMemo(() => [...new Set(rows.map((r) => r.ticker))].sort(), [rows]);

    // Domyślnie zaznacz AAPL, AMZN, ORCL po pierwszym załadowaniu
    useEffect(() => {
        if (allTickers.length && selectedTickers.size === 0) {
            const defaults = new Set(["AAPL", "AMZN", "ORCL"].filter((t) => allTickers.includes(t)));
            setSelected(defaults.size > 0 ? defaults : new Set(allTickers));
        }
    }, [allTickers]);

    const toggleTicker = (t: string) => {
        const next = new Set(selectedTickers);
        next.has(t) ? next.delete(t) : next.add(t);
        setSelected(next);
    };

    const selectAll   = () => setSelected(new Set(allTickers));
    const clearAll    = () => setSelected(new Set());

    // Tylko zaznaczone tickery
    const activeTickers = allTickers.filter((t) => selectedTickers.has(t));

    const chartData = useMemo<GroupedData[]>(() => {
        if (!dateRange.start || !dateRange.end || !activeTickers.length) return [];
        const byDate: Record<string, GroupedData> = {};
        for (const r of rows) {
            if (!selectedTickers.has(r.ticker)) continue;
            if (r.date < dateRange.start || r.date > dateRange.end) continue;
            if (!byDate[r.date]) byDate[r.date] = { date: r.date };
            byDate[r.date][r.ticker] = r.close;
        }
        return Object.values(byDate).sort((a, b) => (a.date < b.date ? -1 : 1));
    }, [rows, dateRange, selectedTickers]);

    const periodStats = useMemo(() => allTickers.map((ticker) => {
        const inRange = rows
            .filter((r) => r.ticker === ticker && r.date >= dateRange.start && r.date <= dateRange.end)
            .sort((a, b) => a.date.localeCompare(b.date));
        if (inRange.length < 2) return { ticker, pct: null, startP: null, endP: null };
        const startP = inRange[0].close;
        const endP   = inRange[inRange.length - 1].close;
        return { ticker, pct: ((endP - startP) / startP) * 100, startP, endP };
    }), [rows, allTickers, dateRange]);

    return (
        <div className="max-w-7xl mx-auto w-full p-6 lg:p-10 space-y-6">
            <div>
                <h1 className="text-2xl font-bold text-white mb-1">Ceny Akcji</h1>
                <p className="text-slate-400 text-sm">Historyczne kursy zamknięcia (daily)</p>
            </div>

            <DateRangeBar
                minDate={minDate}
                maxDate={maxDate}
                start={dateRange.start}
                end={dateRange.end}
                onStartChange={(v) => setDateRange((p) => ({ ...p, start: v }))}
                onEndChange={(v) => setDateRange((p) => ({ ...p, end: v }))}
                dataCount={chartData.length}
                dataLabel="dni"
            />

            {loading ? (
                <div className="flex items-center justify-center h-64 text-slate-400">Ładowanie...</div>
            ) : (
                <>
                    <div className="bg-slate-800 rounded-xl p-4">
                        {activeTickers.length === 0 ? (
                            <div className="flex items-center justify-center h-64 text-slate-500">
                                Zaznacz przynajmniej jedną spółkę
                            </div>
                        ) : (
                            <ResponsiveContainer width="100%" height={420}>
                                <LineChart data={chartData}>
                                    <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                                    <XAxis
                                        dataKey="date"
                                        tick={{ fill: "#94a3b8", fontSize: 11 }}
                                        tickFormatter={(v) => v.slice(0, 7)}
                                        interval="preserveStartEnd"
                                    />
                                    <YAxis
                                        tick={{ fill: "#94a3b8", fontSize: 11 }}
                                        tickFormatter={(v) => `$${v}`}
                                        width={65}
                                    />
                                    <Tooltip
                                        contentStyle={{ background: "#1e293b", border: "1px solid #334155", borderRadius: 8 }}
                                        labelStyle={{ color: "#cbd5e1" }}
                                        formatter={(v, name) => [`$${Number(v).toFixed(2)}`, name]}
                                    />
                                    <Legend wrapperStyle={{ color: "#94a3b8" }} />
                                    {activeTickers.map((t) => (
                                        <Line
                                            key={t}
                                            type="monotone"
                                            dataKey={t}
                                            stroke={COLORS[t] ?? "#94a3b8"}
                                            dot={false}
                                            strokeWidth={1.8}
                                            connectNulls
                                        />
                                    ))}
                                </LineChart>
                            </ResponsiveContainer>
                        )}
                    </div>

                    {/* Karty spółek — klikalne, służą jako selector */}
                    {periodStats.length > 0 && (
                        <div className="space-y-2">
                            <div className="flex items-center gap-2">
                                <span className="text-[10px] font-bold uppercase tracking-widest text-slate-500">
                                    Spółki ({selectedTickers.size}/{allTickers.length})
                                </span>
                                <button onClick={selectAll} className="text-[10px] text-indigo-400 hover:text-indigo-300 font-bold">
                                    Wszystkie
                                </button>
                                <span className="text-slate-700">·</span>
                                <button onClick={clearAll} className="text-[10px] text-slate-500 hover:text-slate-400 font-bold">
                                    Wyczyść
                                </button>
                            </div>

                            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
                                {periodStats.map(({ ticker, pct, startP, endP }) => {
                                    const color  = COLORS[ticker] ?? "#94a3b8";
                                    const active = selectedTickers.has(ticker);
                                    const up     = pct !== null && pct > 0;
                                    const down   = pct !== null && pct < 0;
                                    return (
                                        <button
                                            key={ticker}
                                            onClick={() => toggleTicker(ticker)}
                                            className={`text-left rounded-xl p-3 flex flex-col gap-1 border transition-all ${
                                                active
                                                    ? "bg-slate-800 border-slate-600 shadow-sm"
                                                    : "bg-slate-800/30 border-slate-800 opacity-40 hover:opacity-60"
                                            }`}
                                            style={active ? { borderLeftColor: color, borderLeftWidth: 3 } : {}}
                                        >
                                            <div className="flex items-center justify-between">
                                                <span className="text-xs font-bold font-mono" style={{ color: active ? color : "#64748b" }}>
                                                    {ticker}
                                                </span>
                                                {active && pct !== null && (
                                                    up   ? <TrendingUp  size={13} className="text-emerald-400" />
                                                    : down ? <TrendingDown size={13} className="text-red-400" />
                                                    : <Minus size={13} className="text-slate-500" />
                                                )}
                                            </div>
                                            <div className={`text-base font-bold ${
                                                !active ? "text-slate-600" :
                                                up ? "text-emerald-400" : down ? "text-red-400" : "text-slate-400"
                                            }`}>
                                                {pct !== null ? fmtPct(pct) : "—"}
                                            </div>
                                            <div className="text-[10px] text-slate-500 font-mono">
                                                {startP != null ? fmt(startP) : "—"} → {endP != null ? fmt(endP) : "—"}
                                            </div>
                                        </button>
                                    );
                                })}
                            </div>
                        </div>
                    )}
                </>
            )}
        </div>
    );
}
