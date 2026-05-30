import { createContext, useContext, useState, useEffect, useCallback } from "react";
import type { ReactNode } from "react";

interface User {
    id: string;
    email: string;
    role: string;
    totp_enabled: boolean;
}

interface AuthContextType {
    user: User | null;
    loading: boolean;
    login: (email: string, password: string) => Promise<{ requires_2fa: boolean; session_temp?: string }>;
    logout: () => Promise<void>;
    refresh: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType>({
    user: null,
    loading: true,
    login: async () => ({ requires_2fa: false }),
    logout: async () => {},
    refresh: async () => {},
});

const API = (path: string, opts?: RequestInit) =>
    fetch(path, { credentials: "include", ...opts });

export function AuthProvider({ children }: { children: ReactNode }) {
    const [user, setUser] = useState<User | null>(null);
    const [loading, setLoading] = useState(true);

    const refresh = useCallback(async () => {
        try {
            const res = await API("/auth/me");
            if (res.ok) {
                setUser(await res.json());
            } else {
                setUser(null);
            }
        } catch {
            setUser(null);
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => { refresh(); }, [refresh]);

    const login = async (email: string, password: string) => {
        const res = await API("/auth/login", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ email, password }),
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || "Błąd logowania");
        if (!data.requires_2fa) await refresh();
        return { requires_2fa: !!data.requires_2fa, session_temp: data.session_temp };
    };

    const logout = async () => {
        await API("/auth/logout", { method: "POST" });
        setUser(null);
    };

    return (
        <AuthContext.Provider value={{ user, loading, login, logout, refresh }}>
            {children}
        </AuthContext.Provider>
    );
}

export const useAuth = () => useContext(AuthContext);