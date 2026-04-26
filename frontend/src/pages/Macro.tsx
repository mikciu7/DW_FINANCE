import { useState } from 'react';
import { Activity, Info, Calendar } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { useQuery } from '@tanstack/react-query'; // Import TanStack Query
import { fetchMacroFileDates, fetchMacroData, type MacroData } from '../api/client';

const MACRO_METADATA: Record<string, { label: string; desc: string; interval: string }> = {
    bamlc0a4cbbb: { label: 'ICE BofA BBB US Corp Index', desc: 'Rentowność obligacji korporacyjnych o ratingu BBB.', interval: 'Daily' },
    bamlh0a0hym2: { label: 'ICE BofA US High Yield Index', desc: 'Rentowność obligacji o wysokim ryzyku (High Yield).', interval: 'Daily' },
    dcoilwtico: { label: 'WTI Oil Price', desc: 'Cena ropy naftowej West Texas Intermediate.', interval: 'Daily' },
    dexchus: { label: 'USD/CNY Exchange Rate', desc: 'Kurs wymiany dolara amerykańskiego na juana chińskiego.', interval: 'Daily' },
    dexuseu: { label: 'USD/EUR Exchange Rate', desc: 'Kurs wymiany dolara amerykańskiego na euro.', interval: 'Daily' },
    dexusuk: { label: 'USD/GBP Exchange Rate', desc: 'Kurs wymiany dolara amerykańskiego na funta brytyjskiego.', interval: 'Daily' },
    dff: { label: 'Effective Fed Funds Rate', desc: 'Efektywna stopa funduszy federalnych.', interval: 'Daily' },
    dgs1: { label: '1-Year Treasury Rate', desc: 'Rentowność 1-rocznych obligacji skarbowych USA.', interval: 'Daily' },
    sp500: { label: 'S&P 500 Index', desc: 'Indeks 500 największych spółek giełdowych w USA.', interval: 'Daily' },
    vixcls: { label: 'VIX Volatility Index', desc: 'Indeks zmienności rynku S&P 500 (tzw. indeks strachu).', interval: 'Daily' },
    walcl: { label: 'Fed Total Assets', desc: 'Całkowite aktywa Systemu Rezerwy Federalnej (Bilans Fed).', interval: 'Daily' },
    cscicp03usm665s: { label: 'Consumer Confidence', desc: 'Wskaźnik zaufania konsumentów w USA.', interval: 'Monthly' },
    fedfunds: { label: 'Monthly Fed Funds Rate', desc: 'Miesięczna średnia stopa funduszy federalnych.', interval: 'Monthly' },
    houst: { label: 'Housing Starts', desc: 'Liczba nowych budów domów mieszkalnych.', interval: 'Monthly' },
    m1sl: { label: 'M1 Money Stock', desc: 'Podaż pieniądza M1 (gotówka i depozyty bieżące).', interval: 'Monthly' },
    umcsent: { label: 'U. of Michigan Sentiment', desc: 'Indeks nastrojów konsumentów Uniwersytetu Michigan.', interval: 'Monthly' },
    unrate: { label: 'Unemployment Rate', desc: 'Stopa bezrobocia w USA.', interval: 'Monthly' },
    gdpc1: { label: 'Real GDP', desc: 'Realny Produkt Krajowy Brutto USA.', interval: 'Quarterly' },
    gfdebtn: { label: 'Federal Debt', desc: 'Całkowite zadłużenie rządu federalnego USA.', interval: 'Quarterly' },
    drsfrmacbs: { label: 'Delinquency Rate on Mortgages', desc: 'Wskaźnik opóźnień w spłatach kredytów hipotecznych.', interval: 'Quarterly' },
};

const Macro = () => {
    const [selectedFileDate, setSelectedFileDate] = useState<string>('');
    const [activeMetric, setActiveMetric] = useState<string>('gdpc1');
    const [filterType, setFilterType] = useState<'All' | 'Daily' | 'Monthly' | 'Quarterly'>('All');

    // 1. Pobieranie dostępnych dat snapshotów (cachowane)
    const { data: fileDates = [] } = useQuery({
        queryKey: ['macroFileDates'],
        queryFn: fetchMacroFileDates,
        // Po załadowaniu dat, ustawiamy pierwszą jako domyślną, jeśli żadna nie jest wybrana
        select: (dates) => {
            if (dates.length > 0 && !selectedFileDate) {
                setSelectedFileDate(dates[0]);
            }
            return dates;
        }
    });

    // 2. Pobieranie danych dla konkretnego snapshota (cachowane na podstawie daty)
    const { data: macroData = [], isLoading: isLoadingData } = useQuery({
        queryKey: ['macroData', selectedFileDate],
        queryFn: () => fetchMacroData(selectedFileDate),
        enabled: !!selectedFileDate, // Zapytanie uruchomi się tylko, gdy mamy datę
    });

    const excluded_metrics = ['vixcls', 'walcl', 'unrate'];

    const filteredMetrics = Object.entries(MACRO_METADATA).filter(
        ([symbol, info]) =>
            (filterType === 'All' || info.interval === filterType) && !excluded_metrics.includes(symbol)
    );

    return (
        <div className="p-6 space-y-6 text-white min-h-screen bg-[#0a0a0a]">
            <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
                <div>
                    <h1 className="text-3xl font-bold flex items-center gap-3">
                        <Activity className="text-indigo-500" /> Macro Indicators
                    </h1>
                    <p className="text-slate-400 text-sm mt-1">FRED Economic Data Visualizer</p>
                </div>

                <div className="flex items-center gap-3 bg-slate-900 border border-slate-800 p-2 rounded-xl shadow-lg">
                    <Calendar className="text-slate-500" size={18} />
                    <select
                        className="bg-transparent text-sm focus:outline-none cursor-pointer"
                        value={selectedFileDate}
                        onChange={(e) => setSelectedFileDate(e.target.value)}
                    >
                        {fileDates.map(d => (
                            <option key={d} value={d} className="bg-slate-900">Snapshot: {d}</option>
                        ))}
                    </select>
                </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
                <div className="lg:col-span-1 space-y-4">
                    <div className="flex gap-2 mb-4 overflow-x-auto pb-2 custom-scrollbar">
                        {['All', 'Daily', 'Monthly', 'Quarterly'].map(t => (
                            <button
                                key={t}
                                onClick={() => setFilterType(t as any)}
                                className={`px-3 py-1 rounded-full text-xs font-medium transition-all whitespace-nowrap ${
                                    filterType === t
                                        ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-500/20'
                                        : 'bg-slate-800 text-slate-400 hover:bg-slate-700'
                                }`}
                            >
                                {t}
                            </button>
                        ))}
                    </div>

                    <div className="max-h-[600px] overflow-y-auto space-y-2 pr-2 custom-scrollbar">
                        {filteredMetrics.map(([symbol, info]) => (
                            <button
                                key={symbol}
                                onClick={() => setActiveMetric(symbol)}
                                className={`w-full text-left p-3 rounded-xl border transition-all duration-200 ${
                                    activeMetric === symbol
                                        ? 'bg-indigo-600/20 border-indigo-500 shadow-[0_0_15px_rgba(79,70,229,0.15)]'
                                        : 'bg-slate-900/40 border-slate-800 hover:border-slate-700'
                                }`}
                            >
                                <div className="flex justify-between items-center">
                                    <span className="text-[10px] font-mono text-indigo-400 uppercase tracking-wider">{symbol}</span>
                                    <span className="text-[9px] px-1.5 py-0.5 rounded bg-slate-800 text-slate-500 uppercase font-bold">{info.interval}</span>
                                </div>
                                <div className="text-sm font-semibold mt-1 truncate">{info.label}</div>
                            </button>
                        ))}
                    </div>
                </div>

                <div className="lg:col-span-3 space-y-6">
                    <div className="bg-slate-900/50 border border-slate-800 rounded-3xl p-6 backdrop-blur-xl shadow-2xl">
                        {MACRO_METADATA[activeMetric] && (
                            <div className="flex items-start gap-4 mb-8">
                                <div className="bg-indigo-500/10 p-3 rounded-2xl">
                                    <Info className="text-indigo-500" size={24} />
                                </div>
                                <div>
                                    <h2 className="text-2xl font-bold tracking-tight">{MACRO_METADATA[activeMetric].label}</h2>
                                    <p className="text-slate-400 text-sm mt-1 leading-relaxed max-w-2xl">
                                        {MACRO_METADATA[activeMetric].desc}
                                        <span className="ml-3 px-2 py-0.5 bg-slate-800/80 text-indigo-300 rounded text-[10px] uppercase font-mono">ID: {activeMetric}</span>
                                    </p>
                                </div>
                            </div>
                        )}

                        <div className="h-[450px] w-full min-h-[400px]">
                            {isLoadingData ? (
                                <div className="flex flex-col items-center justify-center h-full text-slate-500 space-y-4">
                                    <div className="animate-spin rounded-full h-10 w-10 border-t-2 border-b-2 border-indigo-500"></div>
                                    <span className="text-sm animate-pulse">Inicjalizacja danych makro...</span>
                                </div>
                            ) : macroData.length > 0 ? (
                                <ResponsiveContainer width="100%" height="100%">
                                    <LineChart data={macroData.filter(d => d[activeMetric] != null)}>
                                        <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
                                        <XAxis
                                            dataKey="date"
                                            stroke="#475569"
                                            tick={{fontSize: 11}}
                                            minTickGap={60}
                                            tickFormatter={(val) => val.split('-')[0]} // Pokazuj tylko rok dla czytelności
                                        />
                                        <YAxis
                                            stroke="#475569"
                                            tick={{fontSize: 11}}
                                            domain={['auto', 'auto']}
                                            tickFormatter={(val) => val.toLocaleString()}
                                        />
                                        <Tooltip
                                            contentStyle={{
                                                backgroundColor: '#0f172a',
                                                border: '1px solid #1e293b',
                                                borderRadius: '12px',
                                                fontSize: '12px',
                                                boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.3)'
                                            }}
                                            itemStyle={{ color: '#6366f1' }}
                                        />
                                        <Line
                                            type="monotone"
                                            dataKey={activeMetric}
                                            stroke="#6366f1"
                                            strokeWidth={2.5}
                                            dot={false}
                                            activeDot={{ r: 6, strokeWidth: 0 }}
                                            animationDuration={1200}
                                            name={MACRO_METADATA[activeMetric]?.label}
                                        />
                                    </LineChart>
                                </ResponsiveContainer>
                            ) : (
                                <div className="flex items-center justify-center h-full text-slate-600 italic">
                                    Brak danych dla wybranego okresu.
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Macro;