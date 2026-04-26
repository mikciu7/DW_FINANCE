import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { fetchPrediction } from "../api/client"; // Używamy Twoich istniejących funkcji z client.ts
import { BrainCircuit } from "lucide-react";

const TICKERS = ["AAPL", "AMZN", "GOOG", "META", "MSFT"];

export default function Agent() {
    const [ticker, setTicker] = useState("AAPL");

    // CACHE: Zapytanie o dane agenta/modelu
    const { data: prediction, isFetching, refetch } = useQuery({
        queryKey: ["agentPrediction", ticker],
        queryFn: () => fetchPrediction(ticker),
        enabled: false, // Odpalamy tylko na żądanie (przycisk)
        staleTime: 1000 * 60 * 10, // 10 minut w pamięci
    });

    return (
        <div className="p-6">
            <h1 className="text-2xl font-bold text-white mb-1 flex items-center gap-2">
                <BrainCircuit className="text-blue-400" /> Agent Makro
            </h1>
            <p className="text-slate-400 text-sm mb-6">Analiza korelacji i raporty geopolityczne</p>

            <div className="bg-slate-800 rounded-xl p-5 mb-6">
                <div className="flex gap-2 mb-4">
                    {TICKERS.map((t) => (
                        <button
                            key={t}
                            onClick={() => setTicker(t)}
                            className={`px-4 py-1.5 rounded text-sm font-medium transition-all ${
                                ticker === t ? "bg-blue-600 text-white" : "bg-slate-700 text-slate-300 hover:bg-slate-600"
                            }`}
                        >
                            {t}
                        </button>
                    ))}
                </div>

                <button
                    onClick={() => refetch()}
                    disabled={isFetching}
                    className="w-full py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg font-medium transition-colors"
                >
                    {isFetching ? "Generowanie..." : `Generuj raport dla ${ticker}`}
                </button>
            </div>

            {/* Tutaj Twój oryginalny widok raportu / danych geopolitycznych */}
            {prediction && (
                <div className={`bg-slate-800 rounded-xl p-6 transition-opacity ${isFetching ? 'opacity-50' : 'opacity-100'}`}>
                    <h2 className="text-xl font-bold text-white mb-4 italic">Raport Geopolityczny i Rynkowy</h2>
                    <div className="text-slate-300 space-y-4">
                        <p>Kierunek: <span className={prediction.direction === 'UP' ? 'text-emerald-400' : 'text-red-400 font-bold'}>
                            {prediction.direction}
                        </span></p>
                        <p>Przewidywany zwrot: {(prediction.predicted_return_3m * 100).toFixed(2)}%</p>
                        {/* Wstaw tutaj ponownie swój kod odpowiedzialny za
                           wyświetlanie opcji raportu geopolitycznego,
                           który miałeś wcześniej.
                        */}
                    </div>
                </div>
            )}
        </div>
    );
}