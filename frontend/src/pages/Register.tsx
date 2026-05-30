import { useState } from "react";

interface Props {
    onSuccess: () => void;
    onLogin: () => void;
}

export default function Register({ onSuccess, onLogin }: Props) {
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [confirm, setConfirm] = useState("");
    const [error, setError] = useState("");
    const [loading, setLoading] = useState(false);

    const validate = () => {
        if (password !== confirm) return "Hasła nie są identyczne";
        if (password.length < 8) return "Hasło musi mieć min. 8 znaków";
        if (!/[A-Z]/.test(password)) return "Hasło musi zawierać wielką literę";
        if (!/\d/.test(password)) return "Hasło musi zawierać cyfrę";
        return null;
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        const err = validate();
        if (err) { setError(err); return; }
        setError("");
        setLoading(true);
        try {
            const res = await fetch("/auth/register", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ email, password }),
            });
            const data = await res.json();
            if (!res.ok) throw new Error(data.detail || "Błąd rejestracji");
            onSuccess();
        } catch (err: unknown) {
            setError(err instanceof Error ? err.message : "Błąd rejestracji");
        } finally {
            setLoading(false);
        }
    };

    const strength = () => {
        let s = 0;
        if (password.length >= 8) s++;
        if (/[A-Z]/.test(password)) s++;
        if (/\d/.test(password)) s++;
        if (/[^A-Za-z0-9]/.test(password)) s++;
        return s;
    };
    const strengthColors = ["bg-red-500", "bg-orange-500", "bg-yellow-500", "bg-green-500"];
    const strengthLabels = ["Słabe", "Słabe", "Średnie", "Silne"];

    return (
        <div className="min-h-screen bg-slate-900 flex items-center justify-center px-4">
            <div className="w-full max-w-md">
                <div className="text-center mb-8">
                    <span className="text-blue-400 font-bold text-3xl">Neo Eye</span>
                    <p className="text-slate-400 mt-2 text-sm">Utwórz konto</p>
                </div>

                <div className="bg-slate-800 border border-slate-700 rounded-2xl p-8 shadow-2xl">
                    <h2 className="text-xl font-semibold text-slate-100 mb-6">Rejestracja</h2>
                    <form onSubmit={handleSubmit} className="space-y-4">
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
                                placeholder="Min. 8 znaków, wielka litera, cyfra"
                            />
                            {password && (
                                <div className="mt-2 flex items-center gap-2">
                                    <div className="flex gap-1 flex-1">
                                        {[0,1,2,3].map(i => (
                                            <div key={i} className={`h-1 flex-1 rounded-full transition-all ${i < strength() ? strengthColors[strength()-1] : "bg-slate-600"}`} />
                                        ))}
                                    </div>
                                    <span className="text-xs text-slate-400">{strengthLabels[Math.max(0, strength()-1)]}</span>
                                </div>
                            )}
                        </div>
                        <div>
                            <label className="block text-xs font-medium text-slate-400 mb-1.5">Potwierdź hasło</label>
                            <input
                                type="password"
                                value={confirm}
                                onChange={(e) => setConfirm(e.target.value)}
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
                            {loading ? "Tworzenie konta..." : "Utwórz konto"}
                        </button>
                    </form>
                    <p className="text-center text-slate-500 text-xs mt-6">
                        Masz już konto?{" "}
                        <button onClick={onLogin} className="text-blue-400 hover:underline">
                            Zaloguj się
                        </button>
                    </p>
                </div>
            </div>
        </div>
    );
}