import { useState, useRef, useEffect } from "react";
import ReactMarkdown from "react-markdown";
import { useViewContext } from "../context/ViewContext";

interface Message {
    role: "user" | "assistant";
    content: string;
}

interface Props {
    onClose: () => void;
}

export default function ChatWidget({ onClose }: Props) {
    const { view } = useViewContext();
    const [messages, setMessages] = useState<Message[]>([]);
    const [input, setInput] = useState("");
    const [isLoading, setIsLoading] = useState(false);
    const messagesEndRef = useRef<HTMLDivElement>(null);
    const sendingRef = useRef(false);

    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [messages]);

    const handleSend = async () => {
        if (!input.trim() || isLoading || sendingRef.current) return;
        sendingRef.current = true;

        const userMessage = input;
        setInput("");
        setMessages((prev: Message[]) => [...prev, { role: "user", content: userMessage }]);
        setIsLoading(true);

        const context = {
            page: view.page,
            tickers: view.tickers,
            metric: view.metric,
            metric_label: view.metricLabel,
            tab: view.tab,
            date_range: view.dateRange,
            fileDate: view.fileDate,
        };

        try {
            const response = await fetch("/api/agent/chat", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ message: userMessage, history: messages, context }),
            });

            if (!response.body) { setIsLoading(false); return; }

            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let assistantMessage = "";

            setMessages((prev) => [...prev, { role: "assistant", content: "" }]);

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;
                const chunk = decoder.decode(value, { stream: true });
                for (const line of chunk.split("\n")) {
                    if (line.startsWith("data: ")) {
                        assistantMessage += line.slice(6);
                        setMessages((prev: Message[]) => {
                            const updated = [...prev];
                            updated[updated.length - 1] = { role: "assistant", content: assistantMessage };
                            return updated;
                        });
                    }
                }
            }
        } catch {
            setMessages((prev) => [
                ...prev,
                { role: "assistant", content: "Błąd przy komunikacji z serwerem. Spróbuj ponownie." },
            ]);
        } finally {
            setIsLoading(false);
            sendingRef.current = false;
        }
    };

    return (
        <div className="flex flex-col h-full">
            {/* Header */}
            <div className="bg-slate-800 border-b border-slate-700 px-5 py-3 flex items-center justify-between shrink-0">
                <div className="flex items-center gap-3">
                    <div className="w-2 h-2 rounded-full bg-blue-400 animate-pulse" />
                    <span className="text-sm font-semibold text-slate-100">Asystent AI</span>
                    {view.page && (
                        <span className="text-xs text-slate-400 bg-slate-700 px-2 py-0.5 rounded">
                            {view.page}
                            {view.metricLabel && ` · ${view.metricLabel}`}
                        </span>
                    )}
                </div>
                <button
                    onClick={onClose}
                    className="text-slate-400 hover:text-slate-200 transition p-1 rounded hover:bg-slate-700"
                    title="Zamknij"
                >
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 5l7 7-7 7M5 5l7 7-7 7" />
                    </svg>
                </button>
            </div>

            {/* Context pill */}
            {view.tickers.length > 0 && (
                <div className="px-5 py-2 border-b border-slate-800 flex gap-2 flex-wrap shrink-0 bg-slate-900/50">
                    {view.tickers.map((t) => (
                        <span key={t} className="text-xs font-mono bg-slate-700 text-slate-300 px-2 py-0.5 rounded">
                            {t}
                        </span>
                    ))}
                    {view.dateRange?.start && (
                        <span className="text-xs text-slate-500 font-mono">
                            {view.dateRange.start} – {view.dateRange.end}
                        </span>
                    )}
                </div>
            )}

            {/* Messages */}
            <div className="flex-1 overflow-y-auto px-5 py-4 space-y-4">
                {messages.length === 0 ? (
                    <div className="flex flex-col items-center justify-center h-full gap-3 text-slate-500">
                        <svg className="w-12 h-12 opacity-30" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
                                d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"
                            />
                        </svg>
                        <p className="text-sm text-center">Pytaj o spółki, wskaźniki i dane finansowe.<br/>Agent widzi co aktualnie przeglądasz.</p>
                    </div>
                ) : (
                    messages.map((msg, idx) => (
                        <div key={idx} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
                            <div className={`max-w-[85%] px-4 py-3 rounded-2xl text-sm ${
                                msg.role === "user"
                                    ? "bg-blue-600 text-white rounded-br-sm"
                                    : "bg-slate-800 text-slate-200 rounded-bl-sm border border-slate-700"
                            }`}>
                                {msg.role === "assistant" ? (
                                    <ReactMarkdown
                                        components={{
                                            h1: ({children}) => <h1 className="text-base font-bold text-white mt-3 mb-1 first:mt-0">{children}</h1>,
                                            h2: ({children}) => <h2 className="text-sm font-bold text-white mt-3 mb-1 first:mt-0">{children}</h2>,
                                            h3: ({children}) => <h3 className="text-sm font-semibold text-blue-300 mt-2 mb-1 first:mt-0">{children}</h3>,
                                            p: ({children}) => <p className="mb-2 last:mb-0 leading-relaxed">{children}</p>,
                                            ul: ({children}) => <ul className="my-1.5 space-y-0.5 pl-1">{children}</ul>,
                                            ol: ({children}) => <ol className="my-1.5 space-y-0.5 pl-1 list-decimal list-inside">{children}</ol>,
                                            li: ({children}) => <li className="flex gap-2 leading-relaxed"><span className="text-blue-400 mt-0.5 shrink-0">•</span><span>{children}</span></li>,
                                            strong: ({children}) => <strong className="font-semibold text-white">{children}</strong>,
                                            em: ({children}) => <em className="italic text-slate-300">{children}</em>,
                                            code: ({children}) => <code className="bg-slate-900 border border-slate-700 rounded px-1.5 py-0.5 text-xs font-mono text-blue-300">{children}</code>,
                                            pre: ({children}) => <pre className="bg-slate-900 border border-slate-700 rounded-lg p-3 mt-2 mb-2 overflow-x-auto text-xs font-mono text-slate-300">{children}</pre>,
                                            hr: () => <hr className="border-slate-600 my-3" />,
                                            blockquote: ({children}) => <blockquote className="border-l-2 border-blue-500 pl-3 my-2 text-slate-400 italic">{children}</blockquote>,
                                            table: ({children}) => <div className="overflow-x-auto my-2"><table className="text-xs border-collapse w-full">{children}</table></div>,
                                            th: ({children}) => <th className="border border-slate-600 px-2 py-1 bg-slate-700 text-white font-semibold text-left">{children}</th>,
                                            td: ({children}) => <td className="border border-slate-700 px-2 py-1 text-slate-300">{children}</td>,
                                        }}
                                    >
                                        {msg.content}
                                    </ReactMarkdown>
                                ) : (
                                    <span className="leading-relaxed">{msg.content}</span>
                                )}
                            </div>
                        </div>
                    ))
                )}
                {isLoading && (
                    <div className="flex justify-start">
                        <div className="bg-slate-800 border border-slate-700 px-4 py-3 rounded-2xl rounded-bl-sm">
                            <div className="flex gap-1.5 items-center">
                                <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: "0ms" }} />
                                <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: "150ms" }} />
                                <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: "300ms" }} />
                            </div>
                        </div>
                    </div>
                )}
                <div ref={messagesEndRef} />
            </div>

            {/* Input */}
            <div className="border-t border-slate-700 px-5 py-4 shrink-0 bg-slate-800/60">
                <div className="flex gap-2">
                    <input
                        type="text"
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        onKeyDown={(e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); handleSend(); } }}
                        placeholder="Zadaj pytanie o dane na wykresie..."
                        disabled={isLoading}
                        className="flex-1 bg-slate-700 text-slate-100 placeholder-slate-500 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50"
                    />
                    <button
                        onClick={handleSend}
                        disabled={isLoading || !input.trim()}
                        className="bg-blue-600 hover:bg-blue-700 disabled:bg-slate-600 text-white rounded-xl px-4 py-2.5 text-sm font-medium transition disabled:cursor-not-allowed shrink-0"
                    >
                        Wyślij
                    </button>
                </div>
            </div>
        </div>
    );
}