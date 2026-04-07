import  { useEffect, useState } from 'react';
import { Activity, Info, Calendar, ChevronRight } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import { fetchMacroFileDates, fetchMacroData, type MacroData } from '../api/client';

const MACRO_METADATA: Record<string, { label: string; desc: string; interval: string }> = {
    // DAILY
    BAMLC0A4CBBB: { label: 'ICE BofA BBB US Corp Index', desc: 'Rentowność obligacji korporacyjnych o ratingu BBB.', interval: 'Daily' },
    BAMLH0A0HYM2: { label: 'ICE BofA US High Yield Index', desc: 'Rentowność obligacji o wysokim ryzyku (High Yield).', interval: 'Daily' },
    DCOILWTICO: { label: 'WTI Oil Price', desc: 'Cena ropy naftowej West Texas Intermediate.', interval: 'Daily' },
    DEXCHUS: { label: 'USD/CNY Exchange Rate', desc: 'Kurs wymiany dolara amerykańskiego na juana chińskiego.', interval: 'Daily' },
    DEXUSEU: { label: 'USD/EUR Exchange Rate', desc: 'Kurs wymiany dolara amerykańskiego na euro.', interval: 'Daily' },
    DEXUSUK: { label: 'USD/GBP Exchange Rate', desc: 'Kurs wymiany dolara amerykańskiego na funta brytyjskiego.', interval: 'Daily' },
    DFF: { label: 'Effective Fed Funds Rate', desc: 'Efektywna stopa funduszy federalnych.', interval: 'Daily' },
    DGS1: { label: '1-Year Treasury Rate', desc: 'Rentowność 1-rocznych obligacji skarbowych USA.', interval: 'Daily' },
    SP500: { label: 'S&P 500 Index', desc: 'Indeks 500 największych spółek giełdowych w USA.', interval: 'Daily' },
    VIXCLS: { label: 'VIX Volatility Index', desc: 'Indeks zmienności rynku S&P 500 (tzw. indeks strachu).', interval: 'Daily' },
    WALCL: { label: 'Fed Total Assets', desc: 'Całkowite aktywa Systemu Rezerwy Federalnej (Bilans Fed).', interval: 'Daily' },

    // MONTHLY
    CSCICP03USM665S: { label: 'Consumer Confidence', desc: 'Wskaźnik zaufania konsumentów w USA.', interval: 'Monthly' },
    FEDFUNDS: { label: 'Monthly Fed Funds Rate', desc: 'Miesięczna średnia stopa funduszy federalnych.', interval: 'Monthly' },
    HOUST: { label: 'Housing Starts', desc: 'Liczba nowych budów domów mieszkalnych.', interval: 'Monthly' },
    M1SL: { label: 'M1 Money Stock', desc: 'Podaż pieniądza M1 (gotówka i depozyty bieżące).', interval: 'Monthly' },
    UMCSENT: { label: 'U. of Michigan Sentiment', desc: 'Indeks nastrojów konsumentów Uniwersytetu Michigan.', interval: 'Monthly' },
    UNRATE: { label: 'Unemployment Rate', desc: 'Stopa bezrobocia w USA.', interval: 'Monthly' },

    // QUARTERLY
    GDPC1: { label: 'Real GDP', desc: 'Realny Produkt Krajowy Brutto USA.', interval: 'Quarterly' },
    GFDEBTN: { label: 'Federal Debt', desc: 'Całkowite zadłużenie rządu federalnego USA.', interval: 'Quarterly' },
    DRSFRMACBS: { label: 'Delinquency Rate on Mortgages', desc: 'Wskaźnik opóźnień w spłatach kredytów hipotecznych.', interval: 'Quarterly' },
};

const Macro = () => {
    const [fileDates, setFileDates] = useState<string[]>([]);
    const [selectedFileDate, setSelectedFileDate] = useState<string>('');
    const [data, setData] = useState<MacroData[]>([]);
    const [activeMetric, setActiveMetric] = useState<string>('GDPC1');
    const [filterType, setFilterType] = useState<'All' | 'Daily' | 'Monthly' | 'Quarterly'>('All');

    useEffect(() => {
        // Zamiast: api.getMacroFileDates()
        fetchMacroFileDates().then(dates => {
            setFileDates(dates);
            if (dates.length > 0) setSelectedFileDate(dates[0]);
        });
    }, []);

    useEffect(() => {
        if (selectedFileDate) {
            // Zamiast: api.getMacroData(selectedFileDate)
            fetchMacroData(selectedFileDate).then(setData);
        }
    }, [selectedFileDate]);

    const filteredMetrics = Object.entries(MACRO_METADATA).filter(
        ([_, info]) => filterType === 'All' || info.interval === filterType
    );

    return (
        <div className="p-6 space-y-6 text-white min-h-screen bg-[#0a0a0a]">
            {/* Header */}
            <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
                <div>
                    <h1 className="text-3xl font-bold flex items-center gap-3">
                        <Activity className="text-indigo-500" /> Macro Indicators
                    </h1>
                    <p className="text-slate-400 text-sm mt-1">FRED Economic Data Visualizer</p>
                </div>

                <div className="flex items-center gap-3 bg-slate-900 border border-slate-800 p-2 rounded-xl">
                    <Calendar className="text-slate-500" size={18} />
                    <select
                        className="bg-transparent text-sm focus:outline-none"
                        value={selectedFileDate}
                        onChange={(e) => setSelectedFileDate(e.target.value)}
                    >
                        {fileDates.map(d => <option key={d} value={d} className="bg-slate-900">Snapshot: {d}</option>)}
                    </select>
                </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
                {/* Sidebar z listą zmiennych */}
                <div className="lg:col-span-1 space-y-4">
                    <div className="flex gap-2 mb-4 overflow-x-auto pb-2">
                        {['All', 'Daily', 'Monthly', 'Quarterly'].map(t => (
                            <button
                                key={t}
                                onClick={() => setFilterType(t as any)}
                                className={`px-3 py-1 rounded-full text-xs font-medium transition-colors ${filterType === t ? 'bg-indigo-600 text-white' : 'bg-slate-800 text-slate-400 hover:bg-slate-700'}`}
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
                                className={`w-full text-left p-3 rounded-xl border transition-all ${activeMetric === symbol ? 'bg-indigo-600/20 border-indigo-500 shadow-[0_0_15px_rgba(79,70,229,0.2)]' : 'bg-slate-900/40 border-slate-800 hover:border-slate-700'}`}
                            >
                                <div className="flex justify-between items-center">
                                    <span className="text-xs font-mono text-indigo-400">{symbol}</span>
                                    <span className="text-[10px] px-1.5 py-0.5 rounded bg-slate-800 text-slate-400 uppercase">{info.interval}</span>
                                </div>
                                <div className="text-sm font-semibold mt-1 truncate">{info.label}</div>
                            </button>
                        ))}
                    </div>
                </div>

                {/* Panel Główny z Wykresem */}
                <div className="lg:col-span-3 space-y-6">
                    <div className="bg-slate-900/50 border border-slate-800 rounded-3xl p-6 backdrop-blur-xl">
                        <div className="flex items-start gap-4 mb-8">
                            <div className="bg-indigo-500/10 p-3 rounded-2xl">
                                <Info className="text-indigo-500" size={24} />
                            </div>
                            <div>
                                <h2 className="text-2xl font-bold">{MACRO_METADATA[activeMetric].label}</h2>
                                <p className="text-slate-400 text-sm mt-1 leading-relaxed">
                                    {MACRO_METADATA[activeMetric].desc}
                                    <span className="ml-2 px-2 py-0.5 bg-slate-800 text-indigo-300 rounded text-xs">Series ID: {activeMetric}</span>
                                </p>
                            </div>
                        </div>

                        <div className="h-[450px] w-full">
                            <ResponsiveContainer width="100%" height="100%">
                                <LineChart data={data.filter(d => d[activeMetric] != null)}>
                                    <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
                                    <XAxis dataKey="date" stroke="#475569" tick={{fontSize: 11}} minTickGap={60} />
                                    <YAxis stroke="#475569" tick={{fontSize: 11}} domain={['auto', 'auto']} />
                                    <Tooltip
                                        contentStyle={{ backgroundColor: '#0f172a', border: '1px solid #1e293b', borderRadius: '12px', fontSize: '12px' }}
                                        itemStyle={{ color: '#6366f1' }}
                                    />
                                    <Line
                                        type="monotone"
                                        dataKey={activeMetric}
                                        stroke="#6366f1"
                                        strokeWidth={2.5}
                                        dot={false}
                                        animationDuration={1000}
                                        name={MACRO_METADATA[activeMetric].label}
                                    />
                                </LineChart>
                            </ResponsiveContainer>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Macro;