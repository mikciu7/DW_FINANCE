import { useCallback } from "react";

const PRESETS = [
    { label: "1M", months: 1 },
    { label: "3M", months: 3 },
    { label: "6M", months: 6 },
    { label: "1Y", months: 12 },
    { label: "3Y", months: 36 },
    { label: "5Y", months: 60 },
    { label: "Max", months: null },
] as const;

export interface DateRange {
    start: string;
    end: string;
}

function daysBetween(a: string, b: string): number {
    return Math.round((new Date(b).getTime() - new Date(a).getTime()) / 86_400_000);
}

function addDays(dateStr: string, days: number): string {
    const d = new Date(dateStr);
    d.setDate(d.getDate() + days);
    return d.toISOString().slice(0, 10);
}

function formatDate(d: string): string {
    if (!d) return "";
    return new Date(d).toLocaleDateString("pl-PL", { year: "numeric", month: "short", day: "numeric" });
}

interface Props {
    minDate: string;
    maxDate: string;
    start: string;
    end: string;
    onStartChange: (v: string) => void;
    onEndChange: (v: string) => void;
    dataCount?: number;
    dataLabel?: string;
    visiblePresets?: string[];
}

export function DateRangeBar({
    minDate, maxDate, start, end,
    onStartChange, onEndChange,
    dataCount, dataLabel = "records",
    visiblePresets,
}: Props) {
    if (!minDate || !maxDate || !start || !end) return null;

    const totalDays = daysBetween(minDate, maxDate) || 1;
    const startIdx = Math.max(0, daysBetween(minDate, start));
    const endIdx = Math.min(totalDays, daysBetween(minDate, end));

    const leftPct = (startIdx / totalDays) * 100;
    const rightPct = (endIdx / totalDays) * 100;

    const handleStartSlider = useCallback((val: number) => {
        const clamped = Math.min(val, endIdx - 1);
        onStartChange(addDays(minDate, clamped));
    }, [minDate, endIdx, onStartChange]);

    const handleEndSlider = useCallback((val: number) => {
        const clamped = Math.max(val, startIdx + 1);
        onEndChange(addDays(minDate, clamped));
    }, [minDate, startIdx, onEndChange]);

    const handlePreset = (months: number | null) => {
        if (months === null) {
            onStartChange(minDate);
            onEndChange(maxDate);
            return;
        }
        const d = new Date(maxDate);
        d.setMonth(d.getMonth() - months);
        const candidate = d.toISOString().slice(0, 10);
        onStartChange(candidate < minDate ? minDate : candidate);
        onEndChange(maxDate);
    };

    const isPresetActive = (months: number | null) => {
        if (months === null) return start === minDate && end === maxDate;
        const d = new Date(maxDate);
        d.setMonth(d.getMonth() - months);
        const candidate = d.toISOString().slice(0, 10);
        const clipped = candidate < minDate ? minDate : candidate;
        return start === clipped && end === maxDate;
    };

    return (
        <div className="bg-slate-800/60 border border-slate-700/80 rounded-xl px-5 py-4 space-y-3">
            {/* Top row: label + presets + count */}
            <div className="flex items-center gap-3 flex-wrap">
                <span className="text-[9px] font-bold uppercase tracking-[0.15em] text-slate-500 shrink-0">
                    Time Slice
                </span>

                <div className="flex gap-1">
                    {PRESETS.filter((p) => !visiblePresets || visiblePresets.includes(p.label)).map((p) => (
                        <button
                            key={p.label}
                            onClick={() => handlePreset(p.months ?? null)}
                            className={`px-2.5 py-0.5 rounded text-xs font-bold transition-all ${
                                isPresetActive(p.months ?? null)
                                    ? "bg-indigo-600 text-white shadow shadow-indigo-600/40"
                                    : "text-slate-400 hover:text-slate-200 hover:bg-slate-700"
                            }`}
                        >
                            {p.label}
                        </button>
                    ))}
                </div>

                {dataCount !== undefined && (
                    <span className="ml-auto text-[11px] text-slate-400 font-mono">
                        <span className="text-white font-bold">{dataCount.toLocaleString()}</span>{" "}
                        {dataLabel}
                    </span>
                )}
            </div>

            {/* Slider row */}
            <div className="space-y-1.5">
                {/* Date labels above thumbs */}
                <div className="relative h-4 select-none">
                    <span
                        className="absolute text-[10px] font-mono text-indigo-300 -translate-x-1/2 whitespace-nowrap"
                        style={{ left: `${leftPct}%` }}
                    >
                        {formatDate(start)}
                    </span>
                    <span
                        className="absolute text-[10px] font-mono text-indigo-300 -translate-x-1/2 whitespace-nowrap"
                        style={{ left: `${rightPct}%` }}
                    >
                        {formatDate(end)}
                    </span>
                </div>

                {/* Track + thumbs */}
                <div className="dual-range relative h-5 flex items-center">
                    {/* Background track */}
                    <div className="absolute w-full h-1.5 bg-slate-700 rounded-full" />

                    {/* Active fill between thumbs */}
                    <div
                        className="absolute h-1.5 bg-indigo-500 rounded-full"
                        style={{ left: `${leftPct}%`, width: `${rightPct - leftPct}%` }}
                    />

                    {/* Start thumb — lower z-index when close to right edge */}
                    <input
                        type="range"
                        min={0}
                        max={totalDays}
                        step={1}
                        value={startIdx}
                        onChange={(e) => handleStartSlider(Number(e.target.value))}
                        style={{ zIndex: startIdx >= endIdx - 2 ? 5 : 3 }}
                    />

                    {/* End thumb */}
                    <input
                        type="range"
                        min={0}
                        max={totalDays}
                        step={1}
                        value={endIdx}
                        onChange={(e) => handleEndSlider(Number(e.target.value))}
                        style={{ zIndex: 4 }}
                    />
                </div>

                {/* Min/max boundary labels */}
                <div className="flex justify-between text-[10px] text-slate-600 font-mono select-none">
                    <span>{minDate}</span>
                    <span>{maxDate}</span>
                </div>
            </div>
        </div>
    );
}
