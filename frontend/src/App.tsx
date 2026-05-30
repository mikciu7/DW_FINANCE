import { useState, lazy, Suspense } from "react";
import ChatWidget from "./components/ChatWidget";
import { ViewContextProvider } from "./context/ViewContext";

// Zamiana standardowych importĂłw na Lazy Imports
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

// Prosty komponent Ĺ‚adujÄ…cy do wyĹ›wieetlania podczas pobierania kodu strony
const PageLoader = () => (
    <div className="flex items-center justify-center min-h-[50vh]">
        <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-blue-500"></div>
    </div>
);

export default function App() {
    const [page, setPage] = useState("overview");
    const [selectedTickers, setSelectedTickers] = useState<Set<string>>(new Set());
    const [chatOpen, setChatOpen] = useState(false);

    return (
        <ViewContextProvider>
        <div className="h-screen bg-slate-900 text-slate-100 flex flex-col overflow-hidden">
            <header className="bg-slate-800 border-b border-slate-700 sticky top-0 z-30 h-14">
                <div className="px-6 flex items-center gap-8 h-full">
                    <div className="flex items-center gap-2 shrink-0">
                        <span className="text-blue-400 font-bold text-lg">Neo Eye</span>
                        <span className="text-slate-400 text-sm hidden md:block">Kompletna analiza gieĹ‚dowa</span>
                    </div>
                    <nav className="flex gap-1 flex-1 overflow-x-auto">
                        {NAV.map((n) => (
                            <button
                                key={n.id}
                                onClick={() => setPage(n.id)}
                                className={`px-4 py-2 rounded text-sm font-medium transition-colors whitespace-nowrap ${
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

            <div className="flex flex-1 overflow-hidden">
                {/* Main content â€” zwÄ™ĹĽa siÄ™ gdy chat otwarty */}
                <main className={`flex-1 overflow-y-auto transition-all duration-300 min-w-0`}>
                    <Suspense fallback={<PageLoader />}>
                        {page === "overview" && <Overview selectedTickers={selectedTickers} onSelectedChange={setSelectedTickers} />}
                        {page === "financials" && <Financials />}
                        {page === "features" && <Features />}
                        {page === "model" && <Model />}
                        {page === "macro" && <Macro />}
                        {page === "agent" && <Agent />}
                    </Suspense>
                </main>

                {/* Chat panel â€” prawa poĹ‚owa */}
                {chatOpen && (
                    <div className="w-[44%] shrink-0 border-l border-slate-700 flex flex-col bg-slate-900">
                        <ChatWidget onClose={() => setChatOpen(false)} />
                    </div>
                )}
            </div>

            {/* FAB â€” widoczny tylko gdy chat zamkniÄ™ty */}
            {!chatOpen && (
                <button
                    onClick={() => setChatOpen(true)}
                    className="fixed bottom-6 right-6 w-14 h-14 bg-blue-600 hover:bg-blue-700 text-white rounded-full shadow-lg flex items-center justify-center z-40 hover:scale-110 transition-all"
                    title="OtwĂłrz asystenta AI"
                >
                    <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                            d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"
                        />
                    </svg>
                </button>
            )}
        </div>
        </ViewContextProvider>
    );
}