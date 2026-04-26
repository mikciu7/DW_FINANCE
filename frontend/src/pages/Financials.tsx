import { useEffect, useState } from "react";
import { fetchEdgar } from "../api/client";
import type { FinancialRow } from "../api/client";
import {
    BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid,
} from "recharts";

const TICKERS = ["AAPL", "AMZN", "GOOG", "META", "MSFT"];

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
    if (v == null) return "—";
    const abs = Math.abs(v);
    if (abs >= 1e12) return `$${(v / 1e12).toFixed(2)}T`;
    if (abs >= 1e9) return `$${(v / 1e9).toFixed(2)}B`;
    if (abs >= 1e6) return `$${(v / 1e6).toFixed(2)}M`;
    return `$${v.toFixed(0)}`;
};

export default function Financials() {
    const [ticker, setTicker] = useState("AAPL");
    const [tab, setTab] = useState("income");
    const [rows, setRows] = useState<FinancialRow[]>([]);
    const [chartMetric, setChartMetric] = useState("revenue");
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        setLoading(true);
        fetchEdgar(ticker)
            .then(setRows)
            .finally(() => setLoading(false));
    }, [ticker]);

    const activeCols = TABS.find((t) => t.id === tab)?.cols ?? [];
    const chartData = rows.map((r) => ({
        date: r.date?.slice(0, 7),
        value: r[chartMetric] as number | null,
    }));

    return (
        <div className="p-6">
            <h1 className="text-2xl font-bold text-white mb-1">Raporty Finansowe</h1>
            <p className="text-slate-400 text-sm mb-4">Dane kwartalne z EDGAR (bez standaryzacji)</p>

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

            {/* Tab selector */}
            <div className="flex gap-1 mb-4 border-b border-slate-700">
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

            {loading ? (
                <div className="flex items-center justify-center h-40 text-slate-400">Ładowanie...</div>
            ) : (
                <>
                    {/* Bar chart */}
                    <div className="bg-slate-800 rounded-xl p-4 mb-4">
                        <div className="flex items-center gap-2 mb-3 flex-wrap">
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
                        <ResponsiveContainer width="100%" height={260}>
                            <BarChart data={chartData}>
                                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                                <XAxis dataKey="date" tick={{ fill: "#94a3b8", fontSize: 10 }} interval="preserveStartEnd" />
                                <YAxis
                                    tick={{ fill: "#94a3b8", fontSize: 10 }}
                                    tickFormatter={(v) => fmt(v)}
                                    width={70}
                                />
                                <Tooltip
                                    contentStyle={{ background: "#1e293b", border: "1px solid #334155", borderRadius: 8 }}
                                    formatter={(v) => [fmt(Number(v))]}
                                />
                                <Bar dataKey="value" fill="#3b82f6" radius={[3, 3, 0, 0]} />
                            </BarChart>
                        </ResponsiveContainer>
                    </div>

                    {/* Table */}
                    <div className="bg-slate-800 rounded-xl overflow-auto">
                        <table className="w-full text-sm">
                            <thead>
                            <tr className="border-b border-slate-700">
                                <th className="text-left px-4 py-2 text-slate-400 font-medium sticky left-0 bg-slate-800">Quarter</th>
                                {activeCols.map((c) => (
                                    <th key={c.key} className="text-right px-4 py-2 text-slate-400 font-medium whitespace-nowrap">
                                        {c.label}
                                    </th>
                                ))}
                            </tr>
                            </thead>
                            <tbody>
                            {[...rows].reverse().map((r) => (
                                <tr key={r.date} className="border-b border-slate-700/50 hover:bg-slate-700/30 transition-colors">
                                    <td className="px-4 py-2 text-slate-300 font-mono sticky left-0 bg-slate-800">{r.date?.slice(0, 10)}</td>
                                    {activeCols.map((c) => (
                                        <td key={c.key} className={`px-4 py-2 text-right font-mono tabular-nums ${
                                            (r[c.key] as number) < 0 ? "text-red-400" : "text-slate-200"
                                        }`}>
                                            {fmt(r[c.key] as number | null)}
                                        </td>
                                    ))}
                                </tr>
                            ))}
                            </tbody>
                        </table>
                    </div>
                </>
            )}
        </div>
    );
}