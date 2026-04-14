import { useState, lazy, Suspense } from "react";

// Zamiana standardowych importów na Lazy Imports
const Overview = lazy(() => import("./pages/Overview"));
const Financials = lazy(() => import("./pages/Financials"));
const Features = lazy(() => import("./pages/Features"));
const Model = lazy(() => import("./pages/Model"));
const Macro = lazy(() => import("./pages/Macro"));
const Agent = lazy(() => import("./pages/Agent"));

const NAV = [
    { id: "overview", label: "Ceny Akcji" },
    { id: "financials", label: "Raporty Finansowe" },
    { id: "features", label: "Features" },
    { id: "model", label: "Model" },
    { id: "macro", label: "Zmienne Makroekonomiczne" },
    { id: "agent", label: "Agent Makro" },
];

// Prosty komponent ładujący do wyświeetlania podczas pobierania kodu strony
const PageLoader = () => (
    <div className="flex items-center justify-center min-h-[50vh]">
        <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-blue-500"></div>
    </div>
);

export default function App() {
    const [page, setPage] = useState("overview");

    return (
        <div className="min-h-screen bg-slate-900 text-slate-100">
            <header className="bg-slate-800 border-b border-slate-700 sticky top-0 z-10">
                <div className="max-w-7xl mx-auto px-6 flex items-center gap-8 h-14">
                    <div className="flex items-center gap-2">
                        <span className="text-blue-400 font-bold text-lg">Neo Eye</span>
                        <span className="text-slate-400 text-sm">Kompletna analiza giełdowa</span>
                    </div>
                    <nav className="flex gap-1">
                        {NAV.map((n) => (
                            <button
                                key={n.id}
                                onClick={() => setPage(n.id)}
                                className={`px-4 py-2 rounded text-sm font-medium transition-colors ${
                                    page === n.id
                                        ? "bg-blue-600/20 text-blue-400"
                                        : "text-slate-400 hover:text-slate-200 hover:bg-slate-700"
                                }`}
                            >
                                {n.label}
                            </button>
                        ))}
                    </nav>
                </div>
            </header>

            <main className="max-w-7xl mx-auto p-4">
                {/* Suspense dla lazy components*/}
                <Suspense fallback={<PageLoader />}>
                    {page === "overview" && <Overview />}
                    {page === "financials" && <Financials />}
                    {page === "features" && <Features />}
                    {page === "model" && <Model />}
                    {page === "macro" && <Macro />}
                    {page === "agent" && <Agent />}
                </Suspense>
            </main>
        </div>
    );
}