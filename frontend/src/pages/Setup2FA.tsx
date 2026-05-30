import { useState, useEffect } from "react";
import { useAuth } from "../context/AuthContext";

interface Props {
    onComplete: () => void;
}

export default function Setup2FA({ onComplete }: Props) {
    const { refresh } = useAuth();
    const [qrCode, setQrCode]   = useState("");
    const [secret, setSecret]   = useState("");
    const [code, setCode]       = useState("");
    const [error, setError]     = useState("");
    const [loading, setLoading] = useState(false);
    const [step, setStep]       = useState<"qr" | "done">("qr");

    useEffect(() => {
        fetch("/auth/totp/setup", { credentials: "include" })
            .then(r => r.json())
            .then(d => { setQrCode(d.qr_code); setSecret(d.secret); })
            .catch(() => setError("Nie udało się załadować kodu QR"));
    }, []);

    const handleConfirm = async (e: React.FormEvent) => {
        e.preventDefault();
        setError("");
        setLoading(true);
        try {
            const res = await fetch("/auth/totp/confirm", {
                method: "POST",
                credentials: "include",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ code }),
            });
            const data = await res.json();
            if (!res.ok) throw new Error(data.detail || "Nieprawidłowy kod");
            setStep("done");
            await refresh();
        } catch (err: unknown) {
            setError(err instanceof Error ? err.message : "Błąd weryfikacji");
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen bg-slate-900 flex items-center justify-center px-4">
            <div className="w-full max-w-md">
                <div className="text-center mb-8">
                    <span className="text-blue-400 font-bold text-3xl">Neo Eye</span>
                    <p className="text-slate-400 mt-2 text-sm">Konfiguracja uwierzytelniania dwuskładnikowego</p>
                </div>

                <div className="bg-slate-800 border border-slate-700 rounded-2xl p-8 shadow-2xl">
                    {step === "qr" ? (
                        <>
                            <h2 className="text-xl font-semibold text-slate-100 mb-2">Aktywuj 2FA</h2>
                            <p className="text-slate-400 text-sm mb-6">
                                Zeskanuj kod QR aplikacją <strong className="text-slate-300">Google Authenticator</strong> lub <strong className="text-slate-300">Authy</strong>, a następnie wpisz wygenerowany kod.
                            </p>

                            {qrCode ? (
                                <div className="flex justify-center mb-4">
                                    <img src={qrCode} alt="QR Code 2FA" className="rounded-xl border-4 border-white w-48 h-48" />
                                </div>
                            ) : (
                                <div className="flex justify-center mb-4">
                                    <div className="w-48 h-48 bg-slate-700 rounded-xl animate-pulse" />
                                </div>
                            )}

                            {secret && (
                                <div className="mb-6 bg-slate-900 border border-slate-600 rounded-lg px-4 py-3">
                                    <p className="text-xs text-slate-500 mb-1">Kod ręczny (jeśli nie możesz zeskanować):</p>
                                    <p className="font-mono text-sm text-slate-300 break-all">{secret}</p>
                                </div>
                            )}

                            <form onSubmit={handleConfirm} className="space-y-4">
                                <div>
                                    <label className="block text-xs font-medium text-slate-400 mb-1.5">Kod weryfikacyjny</label>
                                    <input
                                        type="text"
                                        inputMode="numeric"
                                        maxLength={6}
                                        value={code}
                                        onChange={(e) => setCode(e.target.value.replace(/\D/g, ""))}
                                        required
                                        autoFocus
                                        className="w-full bg-slate-700 border border-slate-600 text-slate-100 rounded-lg px-4 py-3 text-2xl text-center tracking-[0.5em] font-mono focus:outline-none focus:ring-2 focus:ring-blue-500"
                                        placeholder="000000"
                                    />
                                </div>
                                {error && (
                                    <p className="text-red-400 text-sm bg-red-400/10 border border-red-400/20 rounded-lg px-3 py-2">
                                        {error}
                                    </p>
                                )}
                                <button
                                    type="submit"
                                    disabled={loading || code.length !== 6}
                                    className="w-full bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white font-medium rounded-lg py-2.5 text-sm transition"
                                >
                                    {loading ? "Weryfikacja..." : "Aktywuj 2FA"}
                                </button>
                            </form>
                        </>
                    ) : (
                        <div className="text-center py-4">
                            <div className="w-16 h-16 bg-green-500/20 rounded-full flex items-center justify-center mx-auto mb-4">
                                <svg className="w-8 h-8 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                                </svg>
                            </div>
                            <h2 className="text-xl font-semibold text-slate-100 mb-2">2FA aktywowane!</h2>
                            <p className="text-slate-400 text-sm mb-6">
                                Twoje konto jest teraz chronione uwierzytelnianiem dwuskładnikowym.
                            </p>
                            <button
                                onClick={onComplete}
                                className="w-full bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-lg py-2.5 text-sm transition"
                            >
                                Przejdź do aplikacji
                            </button>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}