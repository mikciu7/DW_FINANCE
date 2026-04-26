import { useState } from 'react';
import { Activity, Calendar } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { fetchMacroFileDates, fetchMacroData } from '../api/client';
import { useQuery } from '@tanstack/react-query';

const MACRO_METADATA: Record<string, { label: string; desc: string; interval: string }> = {
    bamlc0a4cbbb: { label: 'ICE BofA BBB US Corp Index', desc: 'Rentowność obligacji korporacyjnych o ratingu BBB.', interval: 'Daily' },
    bamlh0a0hym2: { label: 'ICE BofA US High Yield Index', desc: 'Rentowność obligacji o wysokim ryzyku (High Yield).', interval: 'Daily' },
    dcoilwtico: { label: 'WTI Oil Price', desc: 'Cena ropy naftowej West Texas Intermediate.', interval: 'Daily' },
    dexchus: { label: 'USD/CNY Exchange Rate', desc: 'Kurs wymiany dolara amerykańskiego na juana chińskiego.', interval: 'Daily' },
    dexuseu: { label: 'USD/EUR Exchange Rate', desc: 'Kurs wymiany dolara amerykańskiego na euro.', interval: 'Daily' },
    dexusuk: { label: 'USD/GBP Exchange Rate', desc: 'Kurs wymiany dolara amerykańskiego na funta brytyjskiego.', interval: 'Daily' },
    dlretms: { label: 'Retail Sales Growth', desc: 'Dynamika sprzedaży detalicznej w USA.', interval: 'Monthly' },
    exjpnus: { label: 'JPY/USD Exchange Rate', desc: 'Kurs wymiany jena japońskiego na dolara amerykańskiego.', interval: 'Monthly' },
    gasregw: { label: 'US Gas Prices', desc: 'Średnie ceny benzyny w USA.', interval: 'Weekly' },
    gdpc1: { label: 'Real GDP', desc: 'Realny Produkt Krajowy Brutto USA.', interval: 'Quarterly' },
    mich: { label: 'Inflation Expectation', desc: 'Oczekiwania inflacyjne wg Uniwersytetu Michigan.', interval: 'Monthly' },
    pce: { label: 'PCE Expenditures', desc: 'Wydatki na konsumpcję osobistą.', interval: 'Monthly' },
    stlfsi3: { label: 'St. Louis Fed Financial Stress Index', desc: 'Indeks stresu finansowego (St. Louis Fed).', interval: 'Weekly' },
    t10y2y: { label: '10Y-2Y Treasury Spread', desc: 'Różnica między rentownością obligacji 10-letnich i 2-letnich.', interval: 'Daily' },
    unrate: { label: 'Unemployment Rate', desc: 'Stopa bezrobocia w USA.', interval: 'Monthly' },
};

const Macro = () => {
    const [selectedFileDate, setSelectedFileDate] = useState<string>('');
    const [activeMetric, setActiveMetric] = useState<string>('gdpc1');
    const [filterType, setFilterType] = useState<'All' | 'Daily' | 'Monthly' | 'Quarterly'>('All');

    // Pobieranie dostępnych dat plików
    const { data: fileDates = [] } = useQuery({
        queryKey: ['macroFileDates'],
        queryFn: fetchMacroFileDates,
        select: (dates) => {
            if (dates.length > 0 && !selectedFileDate) setSelectedFileDate(dates[0]);
            return dates;
        }
    });

    // Pobieranie danych dla konkretnego pliku
    const { data: rawData = [], isFetching: loadingData } = useQuery({
        queryKey: ['macroData', selectedFileDate],
        queryFn: () => fetchMacroData(selectedFileDate),
        enabled: !!selectedFileDate,
    });

    const filteredMetrics = Object.entries(MACRO_METADATA).filter(([_, meta]) =>
        filterType === 'All' || meta.interval === filterType
    );

    const chartData = rawData
        .filter(d => d[activeMetric] !== null)
        .map(d => ({
            date: d.date.split('T')[0],
            [activeMetric]: d[activeMetric]
        }))
        .sort((a, b) => a.date.localeCompare(b.date));

    return (
        <div className="p-6 space-y-6 text-white min-h-screen bg-[#0a0a0a]">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-6">
                <div>
                    <h1 className="text-3xl font-bold bg-gradient-to-r from-blue-400 to-indigo-400 bg-clip-text text-transparent">
                        Zmienne Makroekonomiczne
                    </h1>
                    <p className="text-slate-400 mt-1 flex items-center gap-2 text-sm">
                        <Calendar size={14} /> Snapshot danych z dnia:
                        <select
                            value={selectedFileDate}
                            onChange={(e) => setSelectedFileDate(e.target.value)}
                            className="bg-slate-900 border border-slate-700 rounded px-2 py-0.5 text-blue-400 focus:outline-none focus:ring-1 focus:ring-blue-500"
                        >
                            {fileDates.map(d => <option key={d} value={d}>{d}</option>)}
                        </select>
                    </p>
                </div>

                <div className="flex bg-slate-900 p-1 rounded-lg border border-slate-800">
                    {['All', 'Daily', 'Monthly', 'Quarterly'].map((type) => (
                        <button
                            key={type}
                            onClick={() => setFilterType(type as any)}
                            className={`px-4 py-1.5 rounded-md text-sm font-medium transition-all ${
                                filterType === type ? 'bg-blue-600 text-white shadow-lg' : 'text-slate-400 hover:text-slate-200'
                            }`}
                        >
                            {type === 'All' ? 'Wszystkie' : type}
                        </button>
                    ))}
                </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
                <div className="lg:col-span-4 space-y-3 max-h-[calc(100vh-200px)] overflow-y-auto pr-2 custom-scrollbar">
                    {filteredMetrics.map(([key, meta]) => (
                        <button
                            key={key}
                            onClick={() => setActiveMetric(key)}
                            className={`w-full text-left p-4 rounded-xl border transition-all duration-200 group ${
                                activeMetric === key
                                    ? 'bg-blue-600/10 border-blue-500/50 shadow-[0_0_15px_rgba(37,99,235,0.1)]'
                                    : 'bg-slate-900/50 border-slate-800 hover:border-slate-700 hover:bg-slate-800/50'
                            }`}
                        >
                            <div className="flex justify-between items-start mb-1">
                                <span className={`font-semibold text-sm ${activeMetric === key ? 'text-blue-400' : 'text-slate-200'}`}>
                                    {meta.label}
                                </span>
                                <span className="text-[10px] px-2 py-0.5 rounded-full bg-slate-800 text-slate-400 border border-slate-700">
                                    {meta.interval}
                                </span>
                            </div>
                            <p className="text-xs text-slate-500 leading-relaxed line-clamp-2">
                                {meta.desc}
                            </p>
                        </button>
                    ))}
                </div>

                <div className="lg:col-span-8 space-y-6">
                    <div className="bg-slate-900/50 border border-slate-800 rounded-2xl p-6 backdrop-blur-sm">
                        <div className="flex items-center gap-3 mb-6">
                            <div className="p-2 bg-blue-600/20 rounded-lg">
                                <Activity className="text-blue-400" size={20} />
                            </div>
                            <div>
                                <h2 className="text-xl font-bold text-slate-100">{MACRO_METADATA[activeMetric]?.label}</h2>
                                <p className="text-sm text-slate-500">{MACRO_METADATA[activeMetric]?.desc}</p>
                            </div>
                        </div>

                        <div className="h-[450px] w-full">
                            {!loadingData ? (
                                <ResponsiveContainer width="100%" height="100%">
                                    <LineChart data={chartData}>
                                        <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
                                        <XAxis
                                            dataKey="date"
                                            stroke="#475569"
                                            fontSize={10}
                                            tickMargin={10}
                                            interval="preserveStartEnd"
                                        />
                                        <YAxis stroke="#475569" fontSize={10} tick={{fill: '#94a3b8', fontSize: 11}} domain={['auto', 'auto']} />
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
                                            name={MACRO_METADATA[activeMetric]?.label}
                                        />
                                    </LineChart>
                                </ResponsiveContainer>
                            ) : (
                                <div className="flex items-center justify-center h-full text-slate-500 italic">
                                    Pobieranie danych dla wersji {selectedFileDate}...
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