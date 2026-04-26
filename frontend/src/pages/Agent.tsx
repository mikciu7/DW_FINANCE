import { useState } from "react";
import { useQuery } from "@tanstack/react-query";

const AVAILABLE_TICKERS = [
    "AAPL","AMZN","GOOGL","META","MSFT",
    "NVDA","TSLA","JPM","V","GS",
    "GIS","MCD","CVX","XOM","LLY"
];

export default function Agent() {
    const [tab, setTab] = useState<"geo" | "stocks">("geo");
    const [selectedTickers, setSelectedTickers] = useState<string[]>(["AAPL"]);

    const { data: result, isFetching: loading, refetch, error } = useQuery({
        queryKey: ["agent", tab, selectedTickers],
        queryFn: async () => {
            const url = tab === "geo"
                ? "/api/agent/geopolitics"
                : `/api/agent/stocks?${selectedTickers.map(t => `tickers=${t}`).join("&")}`;
            const r = await fetch(url);
            const json = await r.json();
            return json.data as string;
        },
        enabled: false, // Uruchamiamy tylko ręcznie przez refetch()
        staleTime: 1000 * 60 * 15, // Cache agenta na 15 min
    });

    const toggleTicker = (t: string) => {
        setSelectedTickers(prev =>
            prev.includes(t)
                ? prev.filter(x => x !== t)
                : prev.length < 10
                    ? [...prev, t]
                    : prev
        );
    };

    return (
        <div className="p-6 max-w-4xl mx-auto">
            <h1 className="text-2xl font-bold text-blue-400 mb-6">Agent Makro</h1>

            <div className="flex gap-2 mb-6">
                {(["geo", "stocks"] as const).map(t => (
                    <button
                        key={t}
                        onClick={() => { setTab(t); }}
                        className={`px-4 py-2 rounded text-sm font-medium transition-colors ${
                            tab === t ? "bg-blue-600 text-white" : "bg-slate-700 text-slate-300 hover:bg-slate-600"
                        }`}
                    >
                        {t === "geo" ? "🌍 Geopolityka" : "📈 Akcje"}
                    </button>
                ))}
            </div>

            {tab === "stocks" && (
                <div className="mb-6">
                    <p className="text-slate-400 text-sm mb-2">
                        Wybierz max 10 spółek ({selectedTickers.length}/10):
                    </p>
                    <div className="flex flex-wrap gap-2">
                        {AVAILABLE_TICKERS.map(t => (
                            <button
                                key={t}
                                onClick={() => toggleTicker(t)}
                                className={`px-3 py-1 rounded text-xs font-mono transition-colors ${
                                    selectedTickers.includes(t) ? "bg-blue-600 text-white" : "bg-slate-700 text-slate-300 hover:bg-slate-600"
                                }`}
                            >
                                {t}
                            </button>
                        ))}
                    </div>
                </div>
            )}

            <button
                onClick={() => refetch()}
                disabled={loading || (tab === "stocks" && selectedTickers.length === 0)}
                className="mb-6 px-6 py-2 bg-blue-600 hover:bg-blue-700 disabled:opacity-40 rounded font-medium text-sm transition-colors"
            >
                {loading ? "⏳ Analizuję, poczekaj..." : "▶ Uruchom analizę"}
            </button>

            {loading && (
                <div className="text-slate-400 text-sm animate-pulse">
                    Agent zbiera dane i analizuje... może potrwać 20–40 sekund.
                </div>
            )}
            {error && <div className="text-red-400 text-sm">Błąd połączenia z backendem.</div>}
            {result && !loading && (
                <div className="bg-slate-800 border border-slate-700 rounded-lg p-5 text-sm text-slate-200 whitespace-pre-wrap leading-relaxed">
                    {result}
                </div>
            )}
        </div>
    );
}