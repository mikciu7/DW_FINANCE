import { useState } from "react";
import Overview from "./pages/Overview";
import Financials from "./pages/Financials";
import Features from "./pages/Features";
import Model from "./pages/Model";
import Macro from "./pages/Macro";
import Agent from "./pages/Agent";

const NAV = [
  { id: "overview", label: "Ceny Akcji" },
  { id: "financials", label: "Raporty Finansowe" },
  { id: "features", label: "Features" },
  { id: "model", label: "Model" },
    { id: "macro", label: "Zmienne Makroekonomiczne" },
    { id: "agent", label: "Agent Makro" },
];

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

      <main className="max-w-7xl mx-auto">
        {page === "overview" && <Overview />}
        {page === "financials" && <Financials />}
        {page === "features" && <Features />}
        {page === "model" && <Model />}
          {page === "macro" && <Macro />}
          {page === "agent" && <Agent />}
      </main>
    </div>
  );
}
