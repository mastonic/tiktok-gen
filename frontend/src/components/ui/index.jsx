import React from 'react';

export const Card = ({ children, className = '' }) => (
    <div className={`glass-card p-6 ${className}`}>
        {children}
    </div>
);

export const Badge = ({ children, variant = 'info', className = '' }) => {
    const variants = {
        info: 'bg-blue-500/20 text-blue-400 border border-blue-500/30',
        success: 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30',
        warning: 'bg-amber-500/20 text-amber-400 border border-amber-500/30',
        danger: 'bg-red-500/20 text-red-400 border border-red-500/30',
        cyber: 'bg-cyan-500/20 text-cyan-400 border border-cyan-500/30 shadow-[0_0_10px_rgba(6,182,212,0.3)]'
    };

    return (
        <span className={`px-2.5 py-0.5 rounded-full text-xs font-semibold ${variants[variant]} ${className}`}>
            {children}
        </span>
    );
};

export const Button = ({ children, variant = 'primary', onClick, className = '' }) => {
    const variants = {
        primary: 'btn-primary',
        secondary: 'btn-secondary',
        danger: 'btn-danger'
    };

    return (
        <button
            className={`${variants[variant]} ${className}`}
            onClick={onClick}
        >
            {children}
        </button>
    );
};

export const Modal = ({ isOpen, onClose, title, children, footer }) => {
    if (!isOpen) return null;
    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40 backdrop-blur-sm transition-all">
            <div className="bg-navy-900 border border-gray-700/50 rounded-2xl w-full max-w-md overflow-hidden shadow-[0_0_50px_rgba(0,0,0,0.5)] border-t border-t-white/10 animate-in fade-in zoom-in duration-200">
                <div className="p-6 border-b border-gray-800/60 flex justify-between items-center bg-navy-950/50">
                    <h3 className="text-xl font-bold text-white tracking-tight">{title}</h3>
                    <button onClick={onClose} className="text-gray-400 hover:text-white transition-colors p-1 hover:bg-white/5 rounded-lg">
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
                        </svg>
                    </button>
                </div>
                <div className="p-6 text-gray-300">
                    {children}
                </div>
                {footer && (
                    <div className="p-6 border-t border-gray-800/60 bg-navy-950/80 flex justify-end gap-3">
                        {footer}
                    </div>
                )}
            </div>
        </div>
    );
};
