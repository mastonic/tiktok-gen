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
