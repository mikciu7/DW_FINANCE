import { createContext, useContext, useState } from "react";
import type { ReactNode } from "react";

export interface ViewState {
    page: string;
    tickers: string[];
    metric?: string;
    metricLabel?: string;
    tab?: string;
    dateRange?: { start: string; end: string };
    fileDate?: string;
}

interface ViewContextType {
    view: ViewState;
    setView: (v: Partial<ViewState>) => void;
}

const ViewContext = createContext<ViewContextType>({
    view: { page: "overview", tickers: [] },
    setView: () => {},
});

export function ViewContextProvider({ children }: { children: ReactNode }) {
    const [view, setViewState] = useState<ViewState>({ page: "overview", tickers: [] });

    const setView = (update: Partial<ViewState>) =>
        setViewState((prev) => ({ ...prev, ...update }));

    return <ViewContext.Provider value={{ view, setView }}>{children}</ViewContext.Provider>;
}

export const useViewContext = () => useContext(ViewContext);