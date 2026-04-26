import { useEffect, useState } from "react";
import { fetchModelMetrics, fetchFeatureImportance, fetchPrediction } from "../api/client";
import type { ModelMetrics, FeatureImportance, Prediction } from "../api/client";
import {
    BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, Cell,
} from "recharts";

const TICKERS = ["AAPL", "AMZN", "GOOG", "META", "MSFT"];

function MetricCard({ label, value, sub }: { label: string; value: string; sub?: string }) {
    return (
        <div className="bg-slate-700 rounded-xl p-4 flex flex-col gap-1">
            <span className="text-slate-400 text-xs font-medium uppercase tracking-wide">{label}</span>
            <span className="text-white text-2xl font-bold">{value}</span>
            {sub && <span className="text-slate-400 text-xs">{sub}</span>}
        </div>
    );
}

export default function Model() {
    const [metrics, setMetrics] = useState<ModelMetrics | null>(null);
    const [importance, setImportance] = useState<FeatureImportance[]>([]);
    const [ticker, setTicker] = useState("AAPL");
    const [prediction, setPrediction] = useState<Prediction | null>(null);
    const [predicting, setPredicting] = useState(false);
    const [predErr, setPredErr] = useState("");

    useEffect(() => {
        fetchModelMetrics().then(setMetrics);
        fetchFeatureImportance().then((data) => setImportance(data.slice(0, 15)));
    }, []);

    const handlePredict = async () => {
        setPredicting(true);
        setPredErr("");
        setPrediction(null);
        try {
            const p = await fetchPrediction(ticker);
            setPrediction(p);
        } catch {
            setPredErr("Nie udało się pobrać predykcji. Sprawdź czy backend działa.");
        } finally {
            setPredicting(false);
        }
    };

    return (
        <div className="p-6">
            <h1 className="text-2xl font-bold text-white mb-1">Model Predykcji</h1>
            <p className="text-slate-400 text-sm mb-6">
                Random Forest · 30 cech · Target: zwrot po 90 dniach
            </p>

            {/* Metrics */}
            {metrics && (
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-8">
                    <MetricCard label="Hit Rate" value={`${(metrics.hit_rate * 100).toFixed(1)}%`} sub="kierunek UP/DOWN" />
                    <MetricCard label="MAE" value={`${(metrics.mae * 100).toFixed(1)}%`} sub="średni błąd bezwzgl." />
                    <MetricCard label="RMSE" value={`${(metrics.rmse * 100).toFixed(1)}%`} />
                    <MetricCard label="R²" value={metrics.r2.toFixed(3)} sub={`±${metrics.r2_std.toFixed(3)}`} />
                </div>
            )}

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Feature importance */}
                <div>
                    <h2 className="text-lg font-semibold text-white mb-3">Feature Importance (Top 15)</h2>
                    <div className="bg-slate-800 rounded-xl p-4">
                        <ResponsiveContainer width="100%" height={420}>
                            <BarChart data={importance} layout="vertical">
                                <CartesianGrid strokeDasharray="3 3" stroke="#334155" horizontal={false} />
                                <XAxis
                                    type="number"
                                    tick={{ fill: "#94a3b8", fontSize: 10 }}
                                    tickFormatter={(v) => v.toFixed(3)}
                                />
                                <YAxis
                                    type="category"
                                    dataKey="feature"
                                    width={200}
                                    tick={{ fill: "#94a3b8", fontSize: 10 }}
                                />
                                <Tooltip
                                    contentStyle={{ background: "#1e293b", border: "1px solid #334155", borderRadius: 8 }}
                                    formatter={(v) => [Number(v).toFixed(4), "Importance"]}
                                />
                                <Bar dataKey="importance" radius={[0, 3, 3, 0]}>
                                    {importance.map((_, i) => (
                                        <Cell key={i} fill={`hsl(${210 + i * 8}, 70%, ${60 - i * 2}%)`} />
                                    ))}
                                </Bar>
                            </BarChart>
                        </ResponsiveContainer>
                    </div>
                </div>

                {/* Prediction */}
                <div>
                    <h2 className="text-lg font-semibold text-white mb-3">Live Predykcja</h2>
                    <div className="bg-slate-800 rounded-xl p-5">
                        <p className="text-slate-400 text-sm mb-4">
                            Model używa najnowszych danych finansowych spółki do przewidzenia zwrotu w ciągu 90 dni.
                        </p>

                        <div className="flex gap-2 mb-4 flex-wrap">
                            {TICKERS.map((t) => (
                                <button
                                    key={t}
                                    onClick={() => setTicker(t)}
                                    className={`px-3 py-1.5 rounded text-sm font-medium transition-colors ${
                                        ticker === t ? "bg-blue-600 text-white" : "bg-slate-700 text-slate-300 hover:bg-slate-600"
                                    }`}
                                >
                                    {t}
                                </button>
                            ))}
                        </div>

                        <button
                            onClick={handlePredict}
                            disabled={predicting}
                            className="w-full py-2.5 bg-blue-600 hover:bg-blue-500 disabled:bg-slate-600 text-white rounded-lg font-medium transition-colors mb-4"
                        >
                            {predicting ? "Obliczam..." : `Predict ${ticker}`}
                        </button>

                        {predErr && <p className="text-red-400 text-sm">{predErr}</p>}

                        {prediction && (
                            <div className="mt-2">
                                <div className={`rounded-xl p-5 text-center ${
                                    prediction.direction === "UP" ? "bg-emerald-900/40 border border-emerald-700" : "bg-red-900/40 border border-red-700"
                                }`}>
                                    <div className="text-4xl mb-2">
                                        {prediction.direction === "UP" ? "📈" : "📉"}
                                    </div>
                                    <div className={`text-3xl font-bold mb-1 ${
                                        prediction.direction === "UP" ? "text-emerald-400" : "text-red-400"
                                    }`}>
                                        {prediction.direction === "UP" ? "+" : ""}
                                        {(prediction.predicted_return_3m * 100).toFixed(2)}%
                                    </div>
                                    <div className="text-slate-400 text-sm">przewidywany zwrot (90 dni)</div>
                                </div>

                                <div className="mt-3 grid grid-cols-2 gap-2 text-sm">
                                    <div className="bg-slate-700 rounded-lg p-3">
                                        <div className="text-slate-400 text-xs">Aktualna cena</div>
                                        <div className="text-white font-semibold">${prediction.close_price?.toFixed(2)}</div>
                                    </div>
                                    <div className="bg-slate-700 rounded-lg p-3">
                                        <div className="text-slate-400 text-xs">Data danych</div>
                                        <div className="text-white font-semibold">{prediction.date}</div>
                                    </div>
                                </div>
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
}