import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { BrainCircuit, Sparkles, Send, FileText, AlertCircle } from "lucide-react";

import { apiClient } from "../api/client";

const TICKERS = ["AAPL", "AMZN", "GOOG", "META", "MSFT"];

export default function Agent() {
    const [ticker, setTicker] = useState("AAPL");

    // Hook useQuery załatwi sprawę "długiego czekania"
    const { data, isLoading, isFetching, error, refetch } = useQuery({
        queryKey: ["agentReport", ticker],
        queryFn: async () => {
            // Przykład zapytania - dostosuj do swojego endpointu
            const r = await apiClient.get(`/agent/report/${ticker}`);
            return r.data;
        },
        // Ważne: Agent to dane "ciężkie", ustawiamy dłuższy staleTime
        staleTime: 1000 * 60 * 15, // 15 minut spokoju
        enabled: false, // Opcjonalnie: raport generuje się tylko po kliknięciu przycisku
    });

    const handleGenerate = () => {
        refetch();
    };

    return (
        <div className="p-6 max-w-4xl mx-auto">
            <div className="flex items-center gap-3 mb-6">
                <div className="bg-indigo-500/20 p-2 rounded-lg">
                    <BrainCircuit className="text-indigo-400" size={28} />
                </div>
                <div>
                    <h1 className="text-2xl font-bold text-white">Agent Makro</h1>
                    <p className="text-slate-400 text-sm">Inteligentna analiza korelacji i trendów rynkowych</p>
                </div>
            </div>

            <div className="bg-slate-800 border border-slate-700 rounded-2xl p-6 shadow-2xl mb-8">
                <div className="flex flex-col md:flex-row gap-4 items-end">
                    <div className="flex-grow">
                        <label className="block text-xs font-semibold text-slate-500 uppercase mb-2 ml-1">Wybierz spółkę do analizy</label>
                        <div className="flex gap-2 flex-wrap">
                            {TICKERS.map((t) => (
                                <button
                                    key={t}
                                    onClick={() => setTicker(t)}
                                    className={`px-4 py-2 rounded-xl text-sm font-bold transition-all ${
                                        ticker === t
                                            ? "bg-indigo-600 text-white ring-2 ring-indigo-400/30"
                                            : "bg-slate-700 text-slate-400 hover:bg-slate-600"
                                    }`}
                                >
                                    {t}
                                </button>
                            ))}
                        </div>
                    </div>
                    <button
                        onClick={handleGenerate}
                        disabled={isLoading || isFetching}
                        className="flex items-center gap-2 px-6 py-2.5 bg-gradient-to-r from-indigo-600 to-blue-600 hover:from-indigo-500 hover:to-blue-500 text-white rounded-xl font-bold transition-all disabled:opacity-50 disabled:cursor-not-allowed shadow-lg shadow-indigo-500/20"
                    >
                        {isLoading || isFetching ? (
                            <div className="animate-spin h-5 w-5 border-2 border-white/30 border-t-white rounded-full" />
                        ) : (
                            <Sparkles size={18} />
                        )}
                        {data ? "Odśwież analizę" : "Generuj raport"}
                    </button>
                </div>
            </div>

            {/* Wyświetlanie wyników */}
            {error && (
                <div className="bg-red-900/20 border border-red-500/50 p-4 rounded-xl flex gap-3 text-red-200">
                    <AlertCircle />
                    <span>Wystąpił błąd podczas generowania raportu. Spróbuj ponownie.</span>
                </div>
            )}

            {(isLoading || isFetching) && !data && (
                <div className="space-y-4 animate-pulse">
                    <div className="h-4 w-1/3 bg-slate-700 rounded" />
                    <div className="h-32 bg-slate-700 rounded-2xl" />
                    <div className="h-32 bg-slate-700 rounded-2xl" />
                </div>
            )}

            {data && (
                <div className={`transition-opacity duration-500 ${(isLoading || isFetching) ? 'opacity-50' : 'opacity-100'}`}>
                    <div className="bg-slate-800/50 border border-slate-700 rounded-2xl p-8 prose prose-invert max-w-none shadow-inner">
                        <div className="flex items-center gap-2 text-indigo-400 mb-4">
                            <FileText size={20} />
                            <span className="font-mono text-sm tracking-widest uppercase">Raport AI Eye dla {ticker}</span>
                        </div>
                        {/* Tutaj renderujesz treść raportu (Markdown lub JSON) */}
                        <div className="text-slate-200 leading-relaxed whitespace-pre-wrap text-lg">
                            {typeof data === 'string' ? data : JSON.stringify(data, null, 2)}
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}