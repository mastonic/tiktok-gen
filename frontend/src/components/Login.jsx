import React, { useState } from 'react';
import { Lock, ShieldCheck, AlertCircle, Loader2 } from 'lucide-react';

const Login = ({ onLogin }) => {
    const [password, setPassword] = useState('');
    const [error, setError] = useState(false);
    const [loading, setLoading] = useState(false);

    const handleSubmit = (e) => {
        e.preventDefault();
        setLoading(true);
        setError(false);

        // Simple hardcoded security for the cockpit
        // In a real app, this would be an API call
        // The password can be set via env or default to 'masto972'
        setTimeout(() => {
            if (password === 'masto972') {
                localStorage.setItem('im_auth', 'true');
                onLogin();
            } else {
                setError(true);
                setLoading(false);
            }
        }, 800);
    };

    return (
        <div className="min-h-screen bg-[#050505] flex items-center justify-center px-4 font-['Inter']">
            <div className="max-w-md w-full">
                <div className="text-center mb-10">
                    <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-cyan-500/10 border border-cyan-500/20 mb-6">
                        <ShieldCheck className="w-8 h-8 text-cyan-400" />
                    </div>
                    <h1 className="text-3xl font-black text-white tracking-tight mb-2">ZONE SÉCURISÉE</h1>
                    <p className="text-gray-500">Accès réservé au commandant de bord</p>
                </div>

                <form onSubmit={handleSubmit} className="space-y-4">
                    <div className="relative">
                        <Lock className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-500" />
                        <input
                            type="password"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            placeholder="Code d'accès"
                            className="w-full bg-white/5 border border-white/10 rounded-2xl py-4 pl-12 pr-4 text-white focus:outline-none focus:border-cyan-500/50 focus:ring-1 focus:ring-cyan-500/50 transition-all"
                            required
                            autoFocus
                        />
                    </div>

                    {error && (
                        <div className="flex items-center gap-3 text-red-400 bg-red-400/10 border border-red-400/20 p-4 rounded-xl text-sm animate-shake">
                            <AlertCircle className="w-5 h-5 shrink-0" />
                            Accès refusé. Code incorrect.
                        </div>
                    )}

                    <button
                        type="submit"
                        disabled={loading}
                        className="w-full bg-cyan-500 hover:bg-cyan-600 disabled:opacity-50 text-black font-bold py-4 rounded-2xl transition-all shadow-lg shadow-cyan-500/20 flex items-center justify-center gap-2"
                    >
                        {loading ? (
                            <Loader2 className="w-5 h-5 animate-spin" />
                        ) : (
                            "Déverrouiller le Cockpit"
                        )}
                    </button>
                </form>

                <div className="mt-8 text-center text-gray-600 text-xs uppercase tracking-widest">
                    iM-System Terminal v2.0
                </div>
            </div>
        </div>
    );
};

export default Login;
