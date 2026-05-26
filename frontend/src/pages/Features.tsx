import { useEffect, useState, useMemo, useCallback } from "react";
import { fetchFeatures } from "../api/client";
import type { FeatureRow } from "../api/client";
import { DateRangeBar } from "../components/DateRangeBar";
import {
    LineChart, Line, XAxis, YAxis, Tooltip,
    ResponsiveContainer, CartesianGrid, Legend,
} from "recharts";

const TICKERS = ["AAPL", "AMD", "AMZN", "AVGO", "GOOG", "META", "MSFT", "NVDA", "ORCL", "TSLA"];

const COLORS: Record<string, string> = {
    AAPL: "#60a5fa",
    AMD:  "#fb923c",
    AMZN: "#f59e0b",
    AVGO: "#e879f9",
    GOOG: "#34d399",
    META: "#a78bfa",
    MSFT: "#f87171",
    NVDA: "#4ade80",
    ORCL: "#f43f5e",
    TSLA: "#38bdf8",
};

const FEATURE_DESCRIPTIONS: Record<string, string> = {
    // Rentowność
    profit_margin:       "Ile groszy zysku netto firma zatrzymuje z każdej złotówki przychodu. Im wyższy, tym lepiej zarządza kosztami.",
    gross_margin:        "Marża po odjęciu tylko kosztów produkcji/usług. Pokazuje, ile zostaje zanim firma zapłaci za marketing, R&D czy administrację.",
    operating_margin:    "Marża operacyjna — zysk po wszystkich kosztach operacyjnych, ale przed podatkami i odsetkami.",
    roa:                 "Return on Assets — jak efektywnie firma generuje zysk ze wszystkich swoich aktywów (maszyn, gotówki, itp.).",
    roe:                 "Return on Equity — ile firma zarabia na każdą złotówkę zainwestowaną przez akcjonariuszy. Wysoki ROE = firma dobrze pracuje na kapitał.",
    roic:                "Return on Invested Capital — zwrot z całego kapitału (własnego + długu). Dobra miara tego, czy firma tworzy wartość.",
    operating_cf_margin: "Jaki % przychodów zamienia się w realną gotówkę z działalności operacyjnej. Gotówka nie kłamie — firma może mieć zysk na papierze, ale brak kasy.",
    // Wzrost
    revenue_growth_qoq:  "Zmiana przychodów w porównaniu do poprzedniego kwartału (3 miesiące wcześniej).",
    revenue_growth_yoy:  "Zmiana przychodów w porównaniu do tego samego kwartału rok temu. Eliminuje sezonowość.",
    earnings_growth_qoq: "Zmiana zysku netto kwartał do kwartału.",
    earnings_growth_yoy: "Zmiana zysku netto rok do roku. Kluczowy wskaźnik dla inwestorów.",
    eps_growth_yoy:      "Wzrost zysku na akcję (EPS) rok do roku. Bezpośrednio wpływa na wycenę spółki.",
    // Akceleracja
    revenue_acceleration:  "Czy wzrost przychodów przyspiesza czy zwalnia? Dodatnia wartość = firma rośnie coraz szybciej.",
    earnings_acceleration: "Czy wzrost zysku przyspiesza? Często wyprzedza ruchy ceny akcji.",
    eps_acceleration:      "Przyspieszenie wzrostu EPS — sygnał, że spółka wchodzi w nową fazę ekspansji.",
    // Wycena
    pe_ratio:    "Price/Earnings — ile inwestorzy płacą za 1 zł rocznego zysku. P/E = 20 oznacza, że płacisz 20 zł za 1 zł zysku. Niskie P/E może oznaczać niedowartościowanie.",
    price_ma_4q: "Średnia cena akcji z ostatnich 4 kwartałów (ok. rok). Wygładza wahania i pokazuje trend cenowy.",
    price_vs_ma4q: "Odchylenie aktualnej ceny od jej rocznej średniej. Dodatnie = cena powyżej średniej (może być przewartościowana).",
    // Momentum Cenowe
    price_momentum_3m:  "Zmiana ceny akcji przez ostatni kwartał. Pozytywny momentum często się utrzymuje.",
    price_momentum_6m:  "Zmiana ceny przez pół roku — klasyczny wskaźnik momentum używany w modelach quant.",
    price_momentum_12m: "Zmiana ceny przez ostatni rok. Jeden z najsilniejszych predyktorów przyszłych zwrotów wg badań naukowych.",
    price_volatility_4q: "Jak bardzo cena akcji skacze w górę i w dół przez ostatni rok. Wysokie = ryzykowna, niska = stabilna.",
    // Dźwignia & Płynność
    debt_to_assets:  "Jaki % aktywów firmy jest sfinansowany długiem. 0.8 = 80% aktywów to dług — ryzykowne.",
    current_ratio:   "Czy firma ma wystarczająco gotówki i krótkoterminowych aktywów by spłacić krótkoterminowe zobowiązania. Poniżej 1 = problem z płynnością.",
    cf_to_debt:      "Jak szybko firma mogłaby spłacić cały dług z bieżącej gotówki operacyjnej.",
    asset_turnover:  "Ile przychodów firma generuje na każdą złotówkę aktywów. Wyższy = firma efektywniej wykorzystuje zasoby.",
    // Cash Flow
    fcf_margin:      "Free Cash Flow margin — ile realnej wolnej gotówki (po inwestycjach) zostaje z każdej złotówki przychodu. Najważniejsza miara zdrowej firmy.",
    // Zmienność
    earnings_volatility: "Jak bardzo zyski skaczą między kwartałami. Wysoka = firma nieprzewidywalna, niska = stabilna.",
    revenue_volatility:  "Jak bardzo przychody wahają się między kwartałami. Firmy z niską zmiennością przychodów są bezpieczniejsze.",
    // Niespodzianki
    eps_surprise:       "Czy zysk na akcję był wyższy czy niższy od oczekiwań (średniej z ostatnich 4 kwartałów). Pozytywne niespodzianki często windują cenę akcji.",
    revenue_surprise:   "Odchylenie przychodów od historycznej średniej. Pozytywna niespodzianka = firma rośnie szybciej niż zwykle.",
    earnings_surprise:  "Odchylenie zysku netto od historycznej średniej. Duże pozytywne niespodzianki często poprzedzają wzrosty kursu.",
    // Trendy & Seryjność
    revenue_trend:           "Kierunek trendu przychodów (nachylenie linii regresji przez 4 kwartały). Dodatni = rosnące przychody.",
    earnings_trend:          "Kierunek trendu zysku przez ostatni rok. Kluczowy sygnał dla modelu predykcyjnego.",
    positive_earnings_streak: "Ile z ostatnich 4 kwartałów firma poprawiła zyski. 4/4 = świetna passa.",
    positive_revenue_streak:  "Ile z ostatnich 4 kwartałów firma poprawiła przychody. Mierzy konsekwencję wzrostu.",
    // Zmiany
    profit_margin_change: "Czy marża zysku rośnie czy spada w porównaniu do poprzedniego kwartału. Rosnąca marża = firma staje się bardziej efektywna.",
    roe_change:           "Zmiana ROE kwartał do kwartału. Rosnące ROE = firma coraz lepiej pracuje na kapitał akcjonariuszy.",
    // Wyniki Kompozytowe
    quality_score:   "Ocena jakości firmy (0.4×ROE + 0.3×marża zysku + 0.3×marża CF). Im wyższa, tym firma jest bardziej rentowna i efektywna.",
    growth_score:    "Ocena dynamiki wzrostu (przychody YoY + zysk YoY + passa wzrostów). Wysoka = firma rośnie konsekwentnie i szybko.",
    momentum_score:  "Ocena momentum (cena 12m + EPS YoY + przychody YoY). Łączy momentum cenowe z fundamentami.",
    // Lagi
    quality_score_lag1:  "Quality score sprzed 1 kwartału. Model używa danych z przeszłości by przewidzieć przyszłość.",
    quality_score_lag2:  "Quality score sprzed 2 kwartałów (pół roku temu).",
    quality_score_lag4:  "Quality score sprzed 4 kwartałów (rok temu). Sprawdza czy dobra jakość utrzymuje się długoterminowo.",
    profit_margin_lag1:  "Marża zysku sprzed 1 kwartału.",
    profit_margin_lag2:  "Marża zysku sprzed 2 kwartałów.",
    profit_margin_lag4:  "Marża zysku sprzed roku. Porównaj z aktualną — trend marży jest ważniejszy niż jej poziom.",
    roe_lag1:            "ROE sprzed 1 kwartału.",
    roe_lag2:            "ROE sprzed 2 kwartałów.",
    roe_lag4:            "ROE sprzed roku.",
    // Z-scores
    accounts_payable_std_8:                   "Zobowiązania wobec dostawców standaryzowane — jak bardzo odbiegają od normy z ostatnich 2 lat.",
    net_change_in_cash_std_16:                "Zmiana salda gotówki standaryzowana względem 4-letniej historii.",
    cash_and_cash_equivalents_std_8:          "Poziom gotówki standaryzowany — czy firma ma wyjątkowo dużo lub mało kasy.",
    income_tax_expense_std_16:                "Podatek dochodowy standaryzowany — anomalie mogą sygnalizować jednorazowe zdarzenia.",
    nonoperating_income_expense_std_16:       "Przychody/koszty spoza działalności operacyjnej standaryzowane (np. odsetki, jednorazowe zyski).",
    total_liabilities_std_8:                  "Całkowite zobowiązania standaryzowane — czy firma drastycznie zwiększyła zadłużenie.",
    accounts_receivable_std_16:               "Należności od klientów standaryzowane. Nagły wzrost może oznaczać problemy z windykacją.",
    retained_earnings_std_16:                 "Zatrzymane zyski standaryzowane — jak zmienia się skumulowany zysk firmy.",
    net_cash_from_financing_activities_std_8: "Przepływy z finansowania standaryzowane — emisja akcji, zaciąganie/spłata długu.",
    total_assets_std_16:                      "Suma aktywów standaryzowana — gwałtowny wzrost może oznaczać przejęcia.",
    total_current_liabilities_std_8:          "Zobowiązania krótkoterminowe standaryzowane — gwałtowny wzrost to sygnał ostrzegawczy.",
    cost_of_goods_and_services_sold_std_16:   "Koszty wytworzenia standaryzowane — anomalie wpływają bezpośrednio na marżę.",
    earnings_per_share_basic__std_8:          "EPS standaryzowany — jak bardzo bieżący zysk na akcję odbiega od historycznej normy.",
};

const FEATURE_GROUPS = [
    { group: "Rentowność",       features: ["profit_margin", "gross_margin", "operating_margin", "roa", "roe", "roic", "operating_cf_margin"] },
    { group: "Wzrost",           features: ["revenue_growth_qoq", "revenue_growth_yoy", "earnings_growth_qoq", "earnings_growth_yoy", "eps_growth_yoy"] },
    { group: "Akceleracja",      features: ["revenue_acceleration", "earnings_acceleration", "eps_acceleration"] },
    { group: "Wycena",           features: ["pe_ratio", "price_ma_4q", "price_vs_ma4q"] },
    { group: "Momentum Cenowy",  features: ["price_momentum_3m", "price_momentum_6m", "price_momentum_12m", "price_volatility_4q"] },
    { group: "Dźwignia & Płynność", features: ["debt_to_assets", "current_ratio", "cf_to_debt", "asset_turnover"] },
    { group: "Cash Flow",        features: ["fcf_margin"] },
    { group: "Zmienność",        features: ["earnings_volatility", "revenue_volatility"] },
    { group: "Niespodzianki",    features: ["eps_surprise", "revenue_surprise", "earnings_surprise"] },
    { group: "Trendy & Seryjność", features: ["revenue_trend", "earnings_trend", "positive_earnings_streak", "positive_revenue_streak"] },
    { group: "Zmiany",           features: ["profit_margin_change", "roe_change"] },
    { group: "Wyniki Kompozytowe", features: ["quality_score", "growth_score", "momentum_score"] },
    { group: "Lagi",             features: ["quality_score_lag1", "quality_score_lag2", "quality_score_lag4", "profit_margin_lag1", "profit_margin_lag2", "profit_margin_lag4", "roe_lag1", "roe_lag2", "roe_lag4"] },
    { group: "Z-score",          features: ["accounts_payable_std_8", "net_change_in_cash_std_16", "cash_and_cash_equivalents_std_8", "income_tax_expense_std_16", "nonoperating_income_expense_std_16", "total_liabilities_std_8", "accounts_receivable_std_16", "retained_earnings_std_16", "net_cash_from_financing_activities_std_8", "total_assets_std_16", "total_current_liabilities_std_8", "cost_of_goods_and_services_sold_std_16", "earnings_per_share_basic__std_8"] },
];

export default function Features() {
    const [selectedTickers, setSelected] = useState<Set<string>>(new Set(["AAPL"]));
    const [feature, setFeature]          = useState("revenue_acceleration");
    const [tickerData, setTickerData]    = useState<Map<string, FeatureRow[]>>(new Map());
    const [fetchingSet, setFetchingSet]  = useState<Set<string>>(new Set(["AAPL"]));
    const [dateRange, setDateRange]      = useState({ start: "", end: "" });

    const activeTickers = TICKERS.filter((t) => selectedTickers.has(t));

    const fetchTicker = useCallback((t: string) => {
        setFetchingSet((prev) => new Set(prev).add(t));
        fetchFeatures(t)
            .then((data) => setTickerData((prev) => new Map(prev).set(t, data)))
            .finally(() => setFetchingSet((prev) => { const n = new Set(prev); n.delete(t); return n; }));
    }, []);

    useEffect(() => { fetchTicker("AAPL"); }, []);

    const toggleTicker = (t: string) => {
        setSelected((prev) => {
            const next = new Set(prev);
            if (next.has(t)) {
                next.delete(t);
            } else {
                next.add(t);
                if (!tickerData.has(t)) fetchTicker(t);
            }
            return next;
        });
    };

    const loading = fetchingSet.size > 0;

    // Date bounds: union of all selected tickers
    const { minDate, maxDate } = useMemo(() => {
        const dates: string[] = [];
        for (const t of activeTickers) {
            (tickerData.get(t) ?? []).forEach((r) => { if (r.date) dates.push(r.date as string); });
        }
        if (!dates.length) return { minDate: "", maxDate: "" };
        dates.sort();
        return { minDate: dates[0], maxDate: dates[dates.length - 1] };
    }, [tickerData, activeTickers]);

    useEffect(() => {
        if (minDate && maxDate) setDateRange({ start: minDate, end: maxDate });
    }, [minDate, maxDate]);

    // Chart data: one row per date, one key per ticker
    const chartData = useMemo(() => {
        const byDate: Record<string, Record<string, number | string | null>> = {};
        for (const t of activeTickers) {
            for (const r of tickerData.get(t) ?? []) {
                if (!r.date) continue;
                if (dateRange.start && (r.date as string) < dateRange.start) continue;
                if (dateRange.end && (r.date as string) > dateRange.end) continue;
                const key = (r.date as string).slice(0, 7);
                if (!byDate[key]) byDate[key] = { date: key };
                byDate[key][t] = r[feature] as number | null;
            }
        }
        return Object.values(byDate).sort((a, b) => (a.date as string).localeCompare(b.date as string));
    }, [tickerData, activeTickers, feature, dateRange]);

    // Per-ticker stats for selected feature in range
    const tickerStats = useMemo(() => activeTickers.map((t) => {
        const vals = (tickerData.get(t) ?? [])
            .filter((r) => {
                if (!r.date) return false;
                return (!dateRange.start || (r.date as string) >= dateRange.start)
                    && (!dateRange.end || (r.date as string) <= dateRange.end);
            })
            .map((r) => r[feature] as number | null)
            .filter((v): v is number => v != null);
        if (!vals.length) return { ticker: t, min: null, max: null, avg: null };
        return {
            ticker: t,
            min: Math.min(...vals),
            max: Math.max(...vals),
            avg: vals.reduce((a, b) => a + b, 0) / vals.length,
        };
    }), [tickerData, activeTickers, feature, dateRange]);

    return (
        <div className="max-w-7xl mx-auto w-full p-6 lg:p-10 space-y-6">
            <div>
                <h1 className="text-2xl font-bold text-white mb-1">Features Modelu</h1>
                <p className="text-slate-400 text-sm">30 zmiennych wejściowych (standaryzowane) — porównanie spółek</p>
            </div>

            {/* Multi-select ticker buttons */}
            <div className="flex gap-2 flex-wrap">
                {TICKERS.map((t) => {
                    const active = selectedTickers.has(t);
                    const color  = COLORS[t];
                    return (
                        <button
                            key={t}
                            onClick={() => toggleTicker(t)}
                            className={`px-4 py-1.5 rounded text-sm font-medium transition-all border ${
                                active
                                    ? "shadow-sm"
                                    : "bg-slate-700 text-slate-400 hover:bg-slate-600 border-transparent"
                            }`}
                            style={active ? { backgroundColor: color + "22", borderColor: color, color } : {}}
                        >
                            {t}
                        </button>
                    );
                })}
            </div>

            <DateRangeBar
                minDate={minDate}
                maxDate={maxDate}
                start={dateRange.start}
                end={dateRange.end}
                onStartChange={(v) => setDateRange((p) => ({ ...p, start: v }))}
                onEndChange={(v) => setDateRange((p) => ({ ...p, end: v }))}
                dataCount={chartData.length}
                dataLabel="kwartały"
            />

            {/* Feature selector + opis + per-ticker stats */}
            <div className="space-y-2">
                <div className="flex items-center gap-4 flex-wrap">
                    <div className="flex items-center gap-3">
                        <span className="text-slate-400 text-sm shrink-0">Feature:</span>
                        <select
                            value={feature}
                            onChange={(e) => setFeature(e.target.value)}
                            className="bg-slate-700 text-slate-200 text-sm rounded px-3 py-1.5 border border-slate-600"
                        >
                            {FEATURE_GROUPS.map(({ group, features }) => (
                                <optgroup key={group} label={group}>
                                    {features.map((f) => (
                                        <option key={f} value={f}>{f}</option>
                                    ))}
                                </optgroup>
                            ))}
                        </select>
                    </div>

                    <div className="ml-auto flex gap-3 flex-wrap">
                        {tickerStats.map(({ ticker, avg, min, max }) => avg !== null && (
                            <div key={ticker} className="text-xs font-mono px-2 py-1 rounded border"
                                style={{ color: COLORS[ticker], background: COLORS[ticker] + "11", borderColor: COLORS[ticker] + "44" }}
                            >
                                <span className="font-bold">{ticker}</span>
                                <span className="text-slate-400 ml-2">
                                    avg <span style={{ color: COLORS[ticker] }}>{avg!.toFixed(2)}</span>
                                </span>
                                <span className="text-slate-600 ml-1">
                                    [{min!.toFixed(2)}, {max!.toFixed(2)}]
                                </span>
                            </div>
                        ))}
                    </div>
                </div>

                {FEATURE_DESCRIPTIONS[feature] && (
                    <p className="text-xs text-slate-400 bg-slate-800/50 border border-slate-700/60 rounded-lg px-4 py-2 leading-relaxed">
                        <span className="text-slate-500 font-mono mr-2">{feature}</span>
                        {FEATURE_DESCRIPTIONS[feature]}
                    </p>
                )}
            </div>

            {loading && activeTickers.length === 0 ? (
                <div className="flex items-center justify-center h-64 text-slate-400">Ładowanie...</div>
            ) : (
                <div className="bg-slate-800 rounded-xl p-4">
                    <ResponsiveContainer width="100%" height={420}>
                        <LineChart data={chartData}>
                            <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                            <XAxis
                                dataKey="date"
                                tick={{ fill: "#94a3b8", fontSize: 10 }}
                                interval="preserveStartEnd"
                            />
                            <YAxis
                                tick={{ fill: "#94a3b8", fontSize: 10 }}
                                tickFormatter={(v: number) => v.toFixed(2)}
                                width={55}
                            />
                            <Tooltip
                                contentStyle={{ background: "#1e293b", border: "1px solid #334155", borderRadius: 8 }}
                                labelStyle={{ color: "#cbd5e1" }}
                                formatter={(v, name) => [(v as number).toFixed(3), name]}
                            />
                            <Legend wrapperStyle={{ color: "#94a3b8" }} />
                            {activeTickers.map((t) => (
                                <Line
                                    key={t}
                                    type="monotone"
                                    dataKey={t}
                                    stroke={COLORS[t] ?? "#94a3b8"}
                                    dot={false}
                                    strokeWidth={2}
                                    connectNulls
                                />
                            ))}
                        </LineChart>
                    </ResponsiveContainer>
                </div>
            )}
        </div>
    );
}
