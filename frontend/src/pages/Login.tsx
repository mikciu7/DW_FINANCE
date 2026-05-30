import { useState } from "react";
import { useAuth } from "../context/AuthContext";

interface Props {
    onSuccess: () => void;
    onRegister: () => void;
}

export default function Login({ onSuccess, onRegister }: Props) {
    const { login } = useAuth();
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [totpCode, setTotpCode] = useState("");
    const [sessionTemp, setSessionTemp] = useState("");
    const [step, setStep] = useState<"credentials" | "totp">("credentials");
    const [error, setError] = useState("");
    const [loading, setLoading] = useState(false);

    const handleCredentials = async (e: React.FormEvent) => {
        e.preventDefault();
        setError("");
        setLoading(true);
        try {
            const result = await login(email, password);
            if (result.requires_2fa && result.session_temp) {
                setSessionTemp(result.session_temp);
                setStep("totp");
            } else {
                onSuccess();
            }
        } catch (err: unknown) {
            setError(err instanceof Error ? err.message : "Błąd logowania");
        } finally {
            setLoading(false);
        }
    };

    const handleTotp = async (e: React.FormEvent) => {
        e.preventDefault();
        setError("");
        setLoading(true);
        try {
            const res = await fetch("/auth/totp/verify", {
                method: "POST",
                credentials: "include",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ session_temp: sessionTemp, code: totpCode }),
            });
            const data = await res.json();
            if (!res.ok) throw new Error(data.detail || "Nieprawidłowy kod");
            onSuccess();
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
                    <p className="text-slate-400 mt-2 text-sm">Kompletna analiza giełdowa</p>
                </div>

                <div className="bg-slate-800 border border-slate-700 rounded-2xl p-8 shadow-2xl">
                    {step === "credentials" ? (
                        <>
                            <h2 className="text-xl font-semibold text-slate-100 mb-6">Zaloguj się</h2>
                            <form onSubmit={handleCredentials} className="space-y-4">
                                <div>
                                    <label className="block text-xs font-medium text-slate-400 mb-1.5">Email</label>
                                    <input
                                        type="email"
                                        value={email}
                                        onChange={(e) => setEmail(e.target.value)}
                                        required
                                        className="w-full bg-slate-700 border border-slate-600 text-slate-100 rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                                        placeholder="adres@email.com"
                                    />
                                </div>
                                <div>
                                    <label className="block text-xs font-medium text-slate-400 mb-1.5">Hasło</label>
                                    <input
                                        type="password"
                                        value={password}
                                        onChange={(e) => setPassword(e.target.value)}
                                        required
                                        className="w-full bg-slate-700 border border-slate-600 text-slate-100 rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                                        placeholder="••••••••"
                                    />
                                </div>
                                {error && (
                                    <p className="text-red-400 text-sm bg-red-400/10 border border-red-400/20 rounded-lg px-3 py-2">
                                        {error}
                                    </p>
                                )}
                                <button
                                    type="submit"
                                    disabled={loading}
                                    className="w-full bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white font-medium rounded-lg py-2.5 text-sm transition"
                                >
                                    {loading ? "Logowanie..." : "Zaloguj się"}
                                </button>
                            </form>
                            <p className="text-center text-slate-500 text-xs mt-6">
                                Nie masz konta?{" "}
                                <button onClick={onRegister} className="text-blue-400 hover:underline">
                                    Zarejestruj się
                                </button>
                            </p>
                        </>
                    ) : (
                        <>
                            <h2 className="text-xl font-semibold text-slate-100 mb-2">Weryfikacja 2FA</h2>
                            <p className="text-slate-400 text-sm mb-6">
                                Wpisz 6-cyfrowy kod z aplikacji uwierzytelniającej.
                            </p>
                            <form onSubmit={handleTotp} className="space-y-4">
                                <input
                                    type="text"
                                    inputMode="numeric"
                                    maxLength={6}
                                    value={totpCode}
                                    onChange={(e) => setTotpCode(e.target.value.replace(/\D/g, ""))}
                                    required
                                    autoFocus
                                    className="w-full bg-slate-700 border border-slate-600 text-slate-100 rounded-lg px-4 py-3 text-2xl text-center tracking-[0.5em] font-mono focus:outline-none focus:ring-2 focus:ring-blue-500"
                                    placeholder="000000"
                                />
                                {error && (
                                    <p className="text-red-400 text-sm bg-red-400/10 border border-red-400/20 rounded-lg px-3 py-2">
                                        {error}
                                    </p>
                                )}
                                <button
                                    type="submit"
                                    disabled={loading || totpCode.length !== 6}
                                    className="w-full bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white font-medium rounded-lg py-2.5 text-sm transition"
                                >
                                    {loading ? "Weryfikacja..." : "Potwierdź"}
                                </button>
                                <button
                                    type="button"
                                    onClick={() => { setStep("credentials"); setError(""); }}
                                    className="w-full text-slate-500 text-sm hover:text-slate-300"
                                >
                                    Wróć
                                </button>
                            </form>
                        </>
                    )}
                </div>
            </div>
        </div>
    );
}