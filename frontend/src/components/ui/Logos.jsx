import React from 'react';

export const LogoFull = ({ className = "" }) => (
    <svg
        width="400"
        height="120"
        viewBox="0 0 400 120"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        className={className}
    >
        {/* ICON PART */}
        <g transform="translate(10, 10)">
            {/* Hexagon Structure */}
            <path d="M50 5L89.5 27.5V72.5L50 95L10.5 72.5V27.5L50 5Z" stroke="#3B82F6" strokeWidth="2" strokeDasharray="4 2" />
            {/* Brackets */}
            <path d="M35 40L25 50L35 60" stroke="white" strokeWidth="6" strokeLinecap="round" strokeLinejoin="round" />
            <path d="M65 40L75 50L65 60" stroke="white" strokeWidth="6" strokeLinecap="round" strokeLinejoin="round" />
            {/* AI Core */}
            <circle cx="50" cy="50" r="8" fill="#3B82F6" />
            {/* Network Lines */}
            <line x1="50" y1="50" x2="50" y2="20" stroke="#3B82F6" strokeWidth="1.5" />
            <line x1="50" y1="50" x2="75" y2="35" stroke="#3B82F6" strokeWidth="1.5" />
            <line x1="50" y1="50" x2="25" y2="65" stroke="#3B82F6" strokeWidth="1.5" />
        </g>

        {/* TEXT PART */}
        <text x="120" y="75" fill="white" style={{ fontFamily: 'Arial, sans-serif', fontWeight: 900, fontSize: '48px', letterSpacing: '-2px' }}>CREWAI<tspan fill="#3B82F6">972</tspan></text>
        <text x="122" y="95" fill="#666" style={{ fontFamily: 'Arial, sans-serif', fontWeight: 'bold', fontSize: '10px', letterSpacing: '4px', textTransform: 'uppercase' }}>Open Source Intelligence</text>
    </svg>
);

export const LogoIcon = ({ className = "" }) => (
    <svg
        width="100"
        height="100"
        viewBox="0 0 100 100"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        className={className}
    >
        {/* Hexagon Structure */}
        <path d="M50 5L89.5 27.5V72.5L50 95L10.5 72.5V27.5L50 5Z" stroke="#3B82F6" strokeWidth="2" strokeDasharray="4 2" />

        {/* Brackets (Code / Open Source) */}
        <path d="M35 40L25 50L35 60" stroke="white" strokeWidth="6" strokeLinecap="round" strokeLinejoin="round" />
        <path d="M65 40L75 50L65 60" stroke="white" strokeWidth="6" strokeLinecap="round" strokeLinejoin="round" />

        {/* AI Central Node */}
        <circle cx="50" cy="50" r="8" fill="#3B82F6" />

        {/* Neuronal Connections */}
        <line x1="50" y1="50" x2="50" y2="20" stroke="#3B82F6" strokeWidth="1.5" />
        <line x1="50" y1="50" x2="75" y2="35" stroke="#3B82F6" strokeWidth="1.5" />
        <line x1="50" y1="50" x2="25" y2="65" stroke="#3B82F6" strokeWidth="1.5" />
    </svg>
);
