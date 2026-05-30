import { useState, lazy, Suspense } from "react";
import ChatWidget from "./components/ChatWidget";
import { ViewContextProvider } from "./context/ViewContext";
import { AuthProvider, useAuth } from "./context/AuthContext";
import Login from "./pages/Login";
import Register from "./pages/Register";
import Setup2FA from "./pages/Setup2FA";

const Overview   = lazy(() => import("./pages/Overview"));
const Financials = lazy(() => import("./pages/Financials"));
const Features   = lazy(() => import("./pages/Features"));
const Model      = lazy(() => import("./pages/Model"));
const Macro      = lazy(() => import("./pages/Macro"));
const Agent      = lazy(() => import("./pages/Agent"));

const NAV = [
    { id: "overview",   label: "Ceny Akcji" },
    { id: "financials", label: "Raporty Finansowe" },
    { id: "features",   label: "Features" },
    { id: "model",      label: "Model" },
    { id: "macro",      label: "Zmienne Makroekonomiczne" },
    { id: "agent",      label: "Agent Makro" },
];

const PageLoader = () => (
    <div className="flex items-center justify-center min-h-[50vh]">
        <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-blue-500" />
    </div>
);

function AppShell() {
    const { user, loading, logout, refresh } = useAuth();
    const [page, setPage]           = useState("overview");
    const [selectedTickers, setSelectedTickers] = useState<Set<string>>(new Set());
    const [chatOpen, setChatOpen]   = useState(false);
    const [authView, setAuthView]   = useState<"login" | "register">("login");

    if (loading) return <PageLoader />;

    if (!user) {
        return authView === "login"
            ? <Login
                onSuccess={() => {/* useAuth refresh robi resztę */}}
                onRegister={() => setAuthView("register")}
              />
            : <Register
                onSuccess={() => setAuthView("login")}
                onLogin={() => setAuthView("login")}
              />;
    }

    // Wymuszenie konfiguracji 2FA przed wejściem do aplikacji
    if (!user.totp_enabled) {
        return <Setup2FA onComplete={() => refresh()} />;
    }

    return (
        <ViewContextProvider>
        <div className="h-screen bg-slate-900 text-slate-100 flex flex-col overflow-hidden">
            <header className="bg-slate-800 border-b border-slate-700 sticky top-0 z-30 h-14">
                <div className="px-6 flex items-center gap-8 h-full">
                    <div className="flex items-center gap-2 shrink-0">
                        <span className="text-blue-400 font-bold text-lg">Neo Eye</span>
                        <span className="text-slate-400 text-sm hidden md:block">Kompletna analiza giełdowa</span>
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
                    <div className="flex items-center gap-3 shrink-0">
                        <span className="text-xs text-slate-400 font-mono hidden lg:block">{user.email}</span>
                        {user.role === "admin" && (
                            <span className="text-xs bg-yellow-500/20 text-yellow-400 border border-yellow-500/30 px-2 py-0.5 rounded font-mono">
                                admin
                            </span>
                        )}
                        <button
                            onClick={() => logout()}
                            className="text-xs text-slate-500 hover:text-slate-300 transition px-2 py-1 rounded hover:bg-slate-700"
                        >
                            Wyloguj
                        </button>
                    </div>
                </div>
            </header>

            <div className="flex flex-1 overflow-hidden">
                <main className="flex-1 overflow-y-auto transition-all duration-300 min-w-0">
                    <Suspense fallback={<PageLoader />}>
                        {page === "overview"   && <Overview selectedTickers={selectedTickers} onSelectedChange={setSelectedTickers} />}
                        {page === "financials" && <Financials />}
                        {page === "features"   && <Features />}
                        {page === "model"      && <Model />}
                        {page === "macro"      && <Macro />}
                        {page === "agent"      && <Agent />}
                    </Suspense>
                </main>

                {chatOpen && (
                    <div className="w-[44%] shrink-0 border-l border-slate-700 flex flex-col bg-slate-900">
                        <ChatWidget onClose={() => setChatOpen(false)} />
                    </div>
                )}
            </div>

            {!chatOpen && (
                <button
                    onClick={() => setChatOpen(true)}
                    className="fixed bottom-6 right-6 w-14 h-14 bg-blue-600 hover:bg-blue-700 text-white rounded-full shadow-lg flex items-center justify-center z-40 hover:scale-110 transition-all"
                    title="Otwórz asystenta AI"
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

export default function App() {
    return (
        <AuthProvider>
            <AppShell />
        </AuthProvider>
    );
}