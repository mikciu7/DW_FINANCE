import { useState, useMemo } from "react";
import { useQuery } from "@tanstack/react-query"; // Import hooka do cachowania
import { fetchPrices } from "../api/client";
import type { PriceRow } from "../api/client";
import {
    LineChart, Line, XAxis, YAxis, Tooltip, Legend, ResponsiveContainer, CartesianGrid,
} from "recharts";

const COLORS: Record<string, string> = {
    AAPL: "#60a5fa",
    AMZN: "#f59e0b",
    GOOG: "#34d399",
    META: "#a78bfa",
    MSFT: "#f87171",
};

const RANGES = [
    { label: "1Y", days: 365 },
    { label: "3Y", days: 1095 },
    { label: "5Y", days: 1825 },
    { label: "All", days: 99999 },
];

type GroupedData = { date: string; [ticker: string]: number | string };

export default function Overview() {
    const [range, setRange] = useState(1825);

    //  useQuery do cachowania
    const { data: rows = [], isLoading } = useQuery({
        queryKey: ["prices"], // Unikalny klucz w cache dla cen akcji
        queryFn: fetchPrices,   // Funkcja pobierająca dane z pliku client.ts
        // staleTime i gcTime są dziedziczone z QueryClientProvider w main.tsx
    });

    // Logika transformacji danych pozostaje w useMemo dla wydajności
    const chartData = useMemo<GroupedData[]>(() => {
        if (!rows.length) return [];

        const cutoff = new Date();
        cutoff.setDate(cutoff.getDate() - range);

        const byDate: Record<string, GroupedData> = {};
        for (const r of rows) {
            if (new Date(r.date) < cutoff) continue;
            if (!byDate[r.date]) byDate[r.date] = { date: r.date };
            byDate[r.date][r.ticker] = r.close;
        }
        return Object.values(byDate).sort((a, b) => (a.date < b.date ? -1 : 1));
    }, [rows, range]);

    // Wyciąganie unikalnych tickerów z pobranych danych
    const tickers = useMemo(() =>
            [...new Set(rows.map((r) => r.ticker))],
        [rows]);

    return (
        <div className="p-6">
            <h1 className="text-2xl font-bold text-white mb-1">Ceny akcji</h1>
            <p className="text-slate-400 text-sm mb-4">Historyczne kursy zamknięcia (daily)</p>

            {/* Selektor zakresu czasowego */}
            <div className="flex gap-2 mb-6">
                {RANGES.map((r) => (
                    <button
                        key={r.label}
                        onClick={() => setRange(r.days)}
                        className={`px-4 py-1.5 rounded text-sm font-medium transition-colors ${
                            range === r.days
                                ? "bg-blue-600 text-white"
                                : "bg-slate-700 text-slate-300 hover:bg-slate-600"
                        }`}
                    >
                        {r.label}
                    </button>
                ))}
            </div>

            {isLoading ? (
                // Wyświetlane tylko przy pierwszym ładowaniu (gdy cache jest pusty)
                <div className="flex items-center justify-center h-64 text-slate-400">
                    <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-blue-500 mr-3"></div>
                    Pobieranie danych...
                </div>
            ) : (
                <div className="bg-slate-800 rounded-xl p-4 border border-slate-700/50 shadow-xl">
                    <ResponsiveContainer width="100%" height={420}>
                        <LineChart data={chartData}>
                            <CartesianGrid strokeDasharray="3 3" stroke="#334155" vertical={false} />
                            <XAxis
                                dataKey="date"
                                tick={{ fill: "#94a3b8", fontSize: 11 }}
                                tickFormatter={(v) => v.slice(0, 7)}
                                interval="preserveStartEnd"
                                minTickGap={50}
                            />
                            <YAxis
                                tick={{ fill: "#94a3b8", fontSize: 11 }}
                                tickFormatter={(v) => `$${v}`}
                                width={60}
                                domain={['auto', 'auto']}
                            />
                            <Tooltip
                                contentStyle={{
                                    background: "#1e293b",
                                    border: "1px solid #334155",
                                    borderRadius: 8,
                                    boxShadow: "0 10px 15px -3px rgba(0, 0, 0, 0.5)"
                                }}
                                labelStyle={{ color: "#cbd5e1", fontWeight: 'bold', marginBottom: '4px' }}
                                formatter={(v) => [`$${Number(v).toFixed(2)}`]}
                            />
                            <Legend
                                wrapperStyle={{ paddingTop: "20px", color: "#94a3b8" }}
                                iconType="circle"
                            />
                            {tickers.map((t) => (
                                <Line
                                    key={t}
                                    type="monotone"
                                    dataKey={t}
                                    stroke={COLORS[t] ?? "#94a3b8"}
                                    dot={false}
                                    strokeWidth={2}
                                    activeDot={{ r: 4, strokeWidth: 0 }}
                                    animationDuration={1000}
                                />
                            ))}
                        </LineChart>
                    </ResponsiveContainer>
                </div>
            )}
        </div>
    );
}