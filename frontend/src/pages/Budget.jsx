import React, { useState, useEffect } from 'react';
import { Card, Button, Badge } from '../components/ui';
import { DollarSign, Wallet, TrendingDown, Power, Settings2 } from 'lucide-react';

const Budget = () => {
    const [routes, setRoutes] = useState([]);

    useEffect(() => {
        const fetchRoutes = async () => {
            try {
                const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
                const response = await fetch(`${apiUrl}/api/routes`);
                const data = await response.json();
                setRoutes(data);
            } catch (error) {
                console.error("Failed to fetch routes:", error);
            }
        };
        fetchRoutes();
    }, []);

    return (
        <div className="space-y-6">
            <header className="mb-8 flex justify-between items-end">
                <div>
                    <h1 className="text-3xl font-bold text-white tracking-tight mb-1">Budget & Models</h1>
                    <p className="text-gray-400">Control spending limits and LLM routing behaviors.</p>
                </div>
                <div className="flex gap-4">
                    <div className="flex items-center gap-2 bg-navy-800 border border-gray-700 rounded-xl px-4 py-2">
                        <span className="text-sm text-gray-400 font-semibold">DAILY CAP</span>
                        <span className="text-xl font-bold text-white">$15.00</span>
                    </div>
                </div>
            </header>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Limits & Failsafe */}
                <Card className="lg:col-span-1 border-t-4 border-t-cyan-500 flex flex-col gap-6">
                    <h3 className="text-xl font-semibold text-white flex items-center gap-2 border-b border-gray-800 pb-2">
                        <Wallet className="w-5 h-5 text-cyan-400" />
                        Limits & Failsafes
                    </h3>

                    <div className="space-y-4">
                        <div>
                            <div className="flex justify-between text-sm mb-1">
                                <span className="text-gray-400 font-semibold">Today's Spend</span>
                                <span className="text-amber-400 font-bold">$2.45 / $15.00</span>
                            </div>
                            <div className="w-full bg-gray-800 rounded-full h-2">
                                <div className="bg-gradient-to-r from-emerald-400 to-amber-500 h-2 rounded-full w-[16%]"></div>
                            </div>
                        </div>

                        <div className="pt-4 border-t border-gray-800">
                            <div className="flex justify-between items-center mb-2">
                                <div className="text-sm text-gray-200 font-semibold">Auto-stop mechanism</div>
                                <Toggle active={true} />
                            </div>
                            <p className="text-xs text-gray-500 leading-relaxed">System will automatically halt all agent operations and pause current pipeline if daily cap is reached.</p>
                        </div>
                    </div>

                    <div className="mt-auto pt-4 flex gap-2">
                        <Button variant="secondary" className="flex-1">Edit Limits</Button>
                        <Button variant="danger" className="w-12 flex justify-center items-center"><Power className="w-4 h-4" /></Button>
                    </div>
                </Card>

                {/* Model Routing Matrix */}
                <Card className="lg:col-span-2">
                    <h3 className="text-xl font-semibold text-white mb-6 flex items-center gap-2">
                        <Settings2 className="w-5 h-5 text-emerald-400" />
                        LLM Routing Matrix
                    </h3>

                    <div className="space-y-4">
                        {routes.map((route, i) => (
                            <RouteItem
                                key={i}
                                task={route.task}
                                model={route.model}
                                provider={route.provider}
                                cost={route.cost}
                                reason={route.reason}
                                icon={route.icon}
                            />
                        ))}
                    </div>
                </Card>
            </div>

        </div>
    );
};

const Toggle = ({ active }) => (
    <div className={`w-10 h-5 rounded-full p-0.5 transition-colors duration-300 cursor-pointer ${active ? 'bg-amber-500 shadow-[0_0_8px_rgba(245,158,11,0.6)]' : 'bg-gray-700'}`}>
        <div className={`w-4 h-4 rounded-full bg-white transition-transform duration-300 ${active ? 'translate-x-5' : 'translate-x-0'}`}></div>
    </div>
);

const RouteItem = ({ task, model, provider, cost, reason, icon }) => (
    <div className="flex flex-col md:flex-row gap-4 p-4 rounded-xl bg-navy-900/60 border border-gray-800 hover:border-gray-700 transition-colors">
        <div className="w-12 h-12 rounded bg-navy-800 flex items-center justify-center text-2xl shrink-0 border border-gray-700/50">
            {icon}
        </div>
        <div className="flex-1">
            <div className="flex justify-between items-start mb-1">
                <h4 className="font-semibold text-gray-200">{task}</h4>
                <Badge variant="cyber" className="text-[10px]">{provider}</Badge>
            </div>
            <div className="flex items-center gap-3 mb-2">
                <span className="text-sm font-bold text-purple-400">{model}</span>
                <span className="text-xs text-emerald-400 flex items-center gap-1"><TrendingDown className="w-3 h-3" /> {cost}</span>
            </div>
            <p className="text-xs text-gray-500 italic">"{reason}"</p>
        </div>
    </div>
);

export default Budget;
