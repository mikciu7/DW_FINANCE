import { useEffect, useState, useMemo } from 'react';
import {Calendar, Filter, BarChart3, Info} from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import { fetchMacroFileDates, fetchMacroData, type MacroData } from '../api/client';

// Paleta kolorów dla wielu serii (zgodnie z zasadą spójności)
const COLORS = ['#6366f1', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6'];

// ZMIANA: Klucze w słowniku muszą być MAŁYMI LITERAMI, bo tak zwraca je backend
const MACRO_METADATA: Record<string, { label: string; desc: string; interval: string; usage: string }> = {
    bamlc0a4cbbb: {
        label: 'ICE BofA BBB US Corp Index',
        desc: 'Rentowność obligacji korporacyjnych o ratingu BBB.',
        interval: 'Daily',
        usage: 'Służy do oceny ryzyka kredytowego w sektorze przedsiębiorstw; wzrost rentowności może sygnalizować nadchodzące problemy z płynnością firm.'
    },
    bamlh0a0hym2: {
        label: 'ICE BofA US High Yield Index',
        desc: 'Rentowność obligacji o wysokim ryzyku (High Yield).',
        interval: 'Daily',
        usage: 'Wskaźnik apetytu na ryzyko (risk-on/risk-off); wysokie spready zazwyczaj wyprzedzają spadki na giełdach akcji.'
    },
    dcoilwtico: {
        label: 'WTI Oil Price',
        desc: 'Cena ropy naftowej West Texas Intermediate.',
        interval: 'Daily',
        usage: 'Kluczowy składnik kosztowy dla transportu i produkcji; wzrost cen ropy silnie korluje z presją inflacyjną (CPI).'
    },
    dexchus: {
        label: 'USD/CNY Exchange Rate',
        desc: 'Kurs wymiany dolara amerykańskiego na juana chińskiego.',
        interval: 'Daily',
        usage: 'Odzwierciedla napięcia handlowe między USA a Chinami; osłabienie juana może zwiększać konkurencyjność chińskiego eksportu.'
    },
    dexuseu: {
        label: 'USD/EUR Exchange Rate',
        desc: 'Kurs wymiany dolara amerykańskiego na euro.',
        interval: 'Daily',
        usage: 'Najważniejsza para walutowa świata; silny dolar (spadek kursu) często negatywnie wpływa na wyniki zagraniczne spółek z S&P 500.'
    },
    dexusuk: {
        label: 'USD/GBP Exchange Rate',
        desc: 'Kurs wymiany dolara amerykańskiego na funta brytyjskiego.',
        interval: 'Daily',
        usage: 'Barometr kondycji gospodarczej Wielkiej Brytanii i stabilności politycznej w Europie.'
    },
    dff: {
        label: 'Effective Fed Funds Rate',
        desc: 'Efektywna stopa funduszy federalnych.',
        interval: 'Daily',
        usage: 'Najważniejsza stopa procentowa świata; determinuje koszt pieniądza dla banków i pośrednio wpływa na oprocentowanie wszystkich kredytów.'
    },
    dgs1: {
        label: '1-Year Treasury Rate',
        desc: 'Rentowność 1-rocznych obligacji skarbowych USA.',
        interval: 'Daily',
        usage: 'Benchmark dla krótkoterminowych inwestycji dłużnych; odzwierciedla oczekiwania rynku co do stóp procentowych w skali roku.'
    },
    sp500: {
        label: 'S&P 500 Index',
        desc: 'Indeks 500 największych spółek giełdowych w USA.',
        interval: 'Daily',
        usage: 'Główny wskaźnik kondycji amerykańskiego rynku kapitałowego i ogólnego sentymentu inwestorów.'
    },
    vixcls: {
        label: 'VIX Volatility Index',
        desc: 'Indeks zmienności rynku S&P 500 (tzw. indeks strachu).',
        interval: 'Daily',
        usage: 'Wysokie wartości (>30) oznaczają panikę i strach, niskie (<15) sugerują nadmierny optymizm lub samozadowolenie rynku.'
    },
    walcl: {
        label: 'Fed Total Assets',
        desc: 'Całkowite aktywa Systemu Rezerwy Federalnej (Bilans Fed).',
        interval: 'Daily',
        usage: 'Miara płynności dostarczanej przez bank centralny (QE/QT); wzrost bilansu zazwyczaj wspiera ceny aktywów ryzykownych.'
    },
    cscicp03usm665s: {
        label: 'Consumer Confidence',
        desc: 'Wskaźnik zaufania konsumentów w USA.',
        interval: 'Monthly',
        usage: 'Wskaźnik wyprzedzający dla wydatków konsumenckich, które odpowiadają za ok. 70% PKB USA.'
    },
    fedfunds: {
        label: 'Monthly Fed Funds Rate',
        desc: 'Miesięczna średnia stopa funduszy federalnych.',
        interval: 'Monthly',
        usage: 'Wygładzona wersja dziennej stopy DFF; używana do analiz długoterminowych trendów polityki pieniężnej.'
    },
    houst: {
        label: 'Housing Starts',
        desc: 'Liczba nowych budów domów mieszkalnych.',
        interval: 'Monthly',
        usage: 'Czuły wskaźnik cyklu koniunkturalnego; sektor nieruchomości ma silny efekt mnożnikowy w całej gospodarce.'
    },
    m1sl: {
        label: 'M1 Money Stock',
        desc: 'Podaż pieniądza M1 (gotówka i depozyty bieżące).',
        interval: 'Monthly',
        usage: 'Monitoruje ilość najbardziej płynnego pieniądza w obiegu; nadmierny przyrost może prowadzić do wzrostu inflacji.'
    },
    umcsent: {
        label: 'U. of Michigan Sentiment',
        desc: 'Indeks nastrojów konsumentów Uniwersytetu Michigan.',
        interval: 'Monthly',
        usage: 'Badanie nastrojów gospodarstw domowych; spadek często poprzedza ograniczenie konsumpcji i recesję.'
    },
    unrate: {
        label: 'Unemployment Rate',
        desc: 'Stopa bezrobocia w USA.',
        interval: 'Monthly',
        usage: 'Wskaźnik opóźniony cyklu koniunkturalnego; niskie bezrobocie wywiera presję na wzrost płac i inflacji.'
    },
    gdpc1: {
        label: 'Real GDP',
        desc: 'Realny Produkt Krajowy Brutto USA.',
        interval: 'Quarterly',
        usage: 'Ostateczny miernik wzrostu gospodarczego; kluczowy dla określenia fazy cyklu (ekspansja vs recesja).'
    },
    gfdebtn: {
        label: 'Federal Debt',
        desc: 'Całkowite zadłużenie rządu federalnego USA.',
        interval: 'Quarterly',
        usage: 'Analiza stabilności fiskalnej kraju; wysoki dług w relacji do PKB może ograniczać przyszłe możliwości stymulacji gospodarki.'
    },
    drsfrmacbs: {
        label: 'Delinquency Rate on Mortgages',
        desc: 'Wskaźnik opóźnień w spłatach kredytów hipotecznych.',
        interval: 'Quarterly',
        usage: 'Wczesny sygnał kryzysu w sektorze finansowym i problemów gospodarstw domowych z obsługą zadłużenia.'
    },
};

const Macro = () => {
    const [fileDates, setFileDates] = useState<string[]>([]);
    const [selectedFileDate, setSelectedFileDate] = useState<string>('');
    const [data, setData] = useState<MacroData[]>([]);
    // Domyślny klucz również małą literą
    const [selectedMetrics, setSelectedMetrics] = useState<string[]>(['gdpc1']);
    const [filterType, setFilterType] = useState<'All' | 'Daily' | 'Monthly' | 'Quarterly'>('All');

    // operacja slice and dice pola dateeRange oraz setDateRange typu useState String oraz String
    const [dateRange, setDateRange] = useState<{ start: string; end: string }>({ start: '', end: '' });

    const availableRange = useMemo(() => {
        if (data.length === 0) return { min: '', max: '' };
        const dates = data.map(d => d.date);
        return {
            min: dates[0],
            max: dates[dates.length - 1]
        };
    }, [data]);

    useEffect(() => {
        if (availableRange.min && availableRange.max) {
            setDateRange({ start: availableRange.min, end: availableRange.max });
        }
    }, [availableRange]);

    useEffect(() => {
        fetchMacroFileDates().then(dates => {
            setFileDates(dates);
            if (dates.length > 0) setSelectedFileDate(dates[0]);
        });
    }, []);

    useEffect(() => {
        if (selectedFileDate) {
            fetchMacroData(selectedFileDate).then(setData);
        }
    }, [selectedFileDate]);
    const excluded_metrics = ['vixcls','walcl','unrate'];

    const filteredMetrics = Object.entries(MACRO_METADATA).filter(
        ([symbol, info]) =>
            (filterType === 'All' || info.interval === filterType) && !excluded_metrics.includes(symbol)
    );

    const toggleMetric = (symbol: string) => {
        if (selectedMetrics.includes(symbol)) {
            setSelectedMetrics(selectedMetrics.filter(m => m !== symbol));
        } else if (selectedMetrics.length < 5) {
            setSelectedMetrics([...selectedMetrics, symbol]);
        }
    };

    // Slice & Dice: Dynamiczne filtrowanie danych pod wybrane serie
    const chartData = useMemo(() => {
        return data
            .filter(row => row.date >= dateRange.start && row.date <= dateRange.end) // SLICE
            .map(row => {
                const newRow: any = { date: row.date };
                selectedMetrics.forEach(m => newRow[m] = row[m]); // DICE (wybór kolumn)
                return newRow;
            })
            .filter(row => selectedMetrics.some(m => row[m] !== null));
    }, [data, selectedMetrics, dateRange]);

    return (
        <div className="flex h-[calc(100vh-64px)] bg-[#0a0a0a] text-slate-100 overflow-hidden">
            {/* LEWY PANEL: Nawigacja i Filtry (Reguła F) */}
            <aside className="w-80 border-r border-slate-800 bg-slate-900/50 p-6 flex flex-col gap-6 overflow-y-auto custom-scrollbar">
                <div>
                    <h2 className="text-lg font-bold flex items-center gap-2 mb-4">
                        <Filter size={18} className="text-indigo-500" /> Control Panel
                    </h2>

                    <label className="text-xs text-slate-500 uppercase font-bold tracking-wider">Data Snapshot</label>
                    <div className="mt-2 bg-slate-800 rounded-lg p-2 flex items-center gap-2">
                        <Calendar size={16} className="text-slate-400" />
                        <select
                            className="bg-transparent text-sm w-full outline-none"
                            value={selectedFileDate}
                            onChange={(e) => setSelectedFileDate(e.target.value)}
                        >
                            {fileDates.map(d => <option key={d} value={d} className="bg-slate-900">{d}</option>)}
                        </select>
                    </div>
                </div>
                {/* NOWA SEKCJA: DATE RANGE (SLICE) */}
                {data.length > 0 && (
                    <div className="space-y-4">
                        <label className="text-xs text-slate-500 uppercase font-bold tracking-wider">Time Range (Slice)</label>
                        <div className="grid grid-cols-1 gap-2">
                            <div className="bg-slate-800 p-2 rounded-lg">
                                <span className="text-[10px] text-slate-500 block mb-1 uppercase">From</span>
                                <input
                                    type="date"
                                    min={availableRange.min}
                                    max={dateRange.end}
                                    value={dateRange.start}
                                    onChange={(e) => setDateRange(prev => ({ ...prev, start: e.target.value }))}
                                    className="bg-transparent text-xs w-full outline-none text-indigo-300"
                                />
                            </div>
                            <div className="bg-slate-800 p-2 rounded-lg">
                                <span className="text-[10px] text-slate-500 block mb-1 uppercase">To</span>
                                <input
                                    type="date"
                                    min={dateRange.start}
                                    max={availableRange.max}
                                    value={dateRange.end}
                                    onChange={(e) => setDateRange(prev => ({ ...prev, end: e.target.value }))}
                                    className="bg-transparent text-xs w-full outline-none text-indigo-300"
                                />
                            </div>
                        </div>
                    </div>
                )}
                <div>
                    <div className="flex justify-between items-center mb-2">
                        <label className="text-xs text-slate-500 uppercase font-bold tracking-wider">Metrics ({selectedMetrics.length}/5)</label>
                        <div className="flex gap-1">
                            {['Daily', 'Monthly', 'Quarterly'].map(t => (
                                <button
                                    key={t}
                                    onClick={() => setFilterType(t as any)}
                                    className={`text-[10px] px-2 py-0.5 rounded ${filterType === t ? 'bg-indigo-600' : 'bg-slate-800'}`}
                                >
                                    {t[0]}
                                </button>
                            ))}
                        </div>
                    </div>

                    <div className="space-y-2">
                        {/* ZMIANA: Używamy filteredMetrics zamiast surowego MACRO_METADATA */}
                        {filteredMetrics.map(([symbol, info]) => (
                            <button
                                key={symbol}
                                onClick={() => toggleMetric(symbol)}
                                className={`w-full text-left p-2 rounded-lg border text-xs transition-all ${
                                    selectedMetrics.includes(symbol)
                                        ? 'border-indigo-500 bg-indigo-500/10 shadow-[0_0_10px_rgba(99,102,241,0.1)]'
                                        : 'border-slate-800 hover:border-slate-700'
                                }`}
                            >
                                <div className="flex justify-between items-center">
                                    <span className="font-mono text-indigo-400 uppercase">{symbol}</span>
                                    <span className="text-[9px] px-1 rounded bg-slate-800 text-slate-500">{info.interval[0]}</span>
                                </div>
                                <div className="truncate font-medium mt-1">{info.label}</div>
                            </button>
                        ))}
                    </div>
                </div>
            </aside>

            {/* GŁÓWNY OBSZAR: Wykres i KPI (Reguła Z/F) */}
            <main className="flex-1 p-8 overflow-y-auto bg-grid-pattern">
                <header className="mb-8">
                    <h1 className="text-3xl font-bold tracking-tight">Market Intelligence Dashboard</h1>
                    <p className="text-slate-400">Analiza porównawcza wskaźników makroekonomicznych</p>
                </header>

                {/* Szybkie Spojrzenie (KPI) - Zgodnie z modelem "Pierwsze Spojrzenie" [cite: 506] */}
                <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-5 gap-4 mb-8">
                    {selectedMetrics.map((m, idx) => (
                        <div key={m} className="bg-slate-900 border border-slate-800 p-4 rounded-2xl shadow-sm">
                            <div className="flex items-center justify-between mb-2">
                                <div className="w-2 h-2 rounded-full" style={{ backgroundColor: COLORS[idx] }} />
                                <span className="text-[10px] text-slate-500 uppercase">{m}</span>
                            </div>
                            <div className="text-xl font-bold">
                                {data.length > 0 ? data[data.length-1][m]?.toLocaleString() : '---'}
                            </div>
                            <div className="text-xs text-slate-400 truncate">{MACRO_METADATA[m]?.label}</div>
                        </div>
                    ))}
                </div>

                {/* Wykres - Główny punkt uwagi [cite: 559] */}
                <div className="bg-slate-900/50 border border-slate-800 rounded-3xl p-6 backdrop-blur-md h-[600px]">
                    <div className="flex justify-between items-center mb-6">
                        <h3 className="font-bold flex items-center gap-2">
                            <BarChart3 className="text-indigo-400" /> Historical Performance
                        </h3>
                    </div>
                    <ResponsiveContainer width="100%" height="100%">
                        <LineChart data={chartData}>
                            <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
                            <XAxis dataKey="date" stroke="#475569" tick={{fontSize: 10}} minTickGap={80} />
                            <YAxis stroke="#475569" tick={{fontSize: 10}} domain={['auto', 'auto']} />
                            <Tooltip
                                contentStyle={{ backgroundColor: '#0f172a', border: '1px solid #334155', borderRadius: '12px' }}
                                itemStyle={{ fontSize: '12px' }}
                            />
                            <Legend iconType="circle" wrapperStyle={{ paddingTop: '20px' }} />
                            {selectedMetrics.map((m, idx) => (
                                <Line
                                    key={m}
                                    type="monotone"
                                    dataKey={m}
                                    stroke={COLORS[idx]}
                                    strokeWidth={2}
                                    dot={false}
                                    name={MACRO_METADATA[m]?.label}
                                    animationDuration={500}
                                />
                            ))}
                        </LineChart>
                    </ResponsiveContainer>
                </div>
                {/* Dynamiczna Sekcja Wiedzy (Drugie Spojrzenie) [cite: 559] */}
                {selectedMetrics.length > 0 && (
                    <div className="mt-8 space-y-6">
                        <div className="flex items-center gap-3 border-b border-slate-800 pb-4">
                            <BarChart3 className="text-indigo-500" size={24} />
                            <h2 className="text-xl font-bold">Interpretacja i Zastosowanie Rynkowe</h2>
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                            {selectedMetrics.map((m, idx) => (
                                <div
                                    key={m}
                                    className="p-5 bg-slate-900/40 border border-slate-800 rounded-2xl flex flex-col gap-3 transition-all hover:border-slate-600"
                                >
                                    <div className="flex justify-between items-start">
                                        <div className="flex items-center gap-3">
                                            {/* Kropka w kolorze linii z wykresu dla szybkiej identyfikacji wizualnej  */}
                                            <div className="w-3 h-3 rounded-full" style={{ backgroundColor: COLORS[idx] }} />
                                            <h4 className="font-bold text-lg uppercase font-mono">{m}</h4>
                                        </div>
                                        <span className="text-[10px] px-2 py-0.5 rounded bg-slate-800 text-indigo-400 font-bold uppercase">
                            {MACRO_METADATA[m]?.interval}
                        </span>
                                    </div>

                                    <div>
                                        <h5 className="text-sm font-semibold text-slate-200">{MACRO_METADATA[m]?.label}</h5>
                                        <p className="text-sm text-slate-400 mt-1 leading-relaxed">
                                            {MACRO_METADATA[m]?.desc}
                                        </p>
                                    </div>

                                    <div className="mt-2 pt-4 border-t border-slate-800/50">
                                        <div className="flex items-center gap-2 text-indigo-400 mb-1">
                                            <Info size={14} />
                                            <span className="text-[10px] font-bold uppercase tracking-widest">Zastosowanie BI</span>
                                        </div>
                                        <p className="text-xs text-slate-300 italic leading-relaxed">
                                            {MACRO_METADATA[m]?.usage}
                                        </p>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                )}

            </main>
        </div>
    );
};

export default Macro;