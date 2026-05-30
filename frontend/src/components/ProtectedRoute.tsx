import { useAuth } from "../context/AuthContext";

interface Props {
    children: React.ReactNode;
    onShowLogin: () => void;
}

export default function ProtectedRoute({ children, onShowLogin }: Props) {
    const { user, loading } = useAuth();

    if (loading) {
        return (
            <div className="flex items-center justify-center min-h-screen bg-slate-900">
                <div className="animate-spin rounded-full h-10 w-10 border-t-2 border-b-2 border-blue-500" />
            </div>
        );
    }

    if (!user) {
        onShowLogin();
        return null;
    }

    return <>{children}</>;
}