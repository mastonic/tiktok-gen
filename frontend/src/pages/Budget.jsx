import { API_URL } from '../api';
import React, { useState, useEffect } from 'react';
import { Card, Button, Badge } from '../components/ui';
import { DollarSign, Wallet, TrendingDown, Power, Settings2 } from 'lucide-react';

const Budget = () => {
    const [routes, setRoutes] = useState([]);
    const [config, setConfig] = useState({ daily_cap: 15.0, today_spend: 0, auto_stop: true, is_active: true });
    const [isEditModalOpen, setIsEditModalOpen] = useState(false);
    const [editCap, setEditCap] = useState(15.0);
    const [isSaving, setIsSaving] = useState(false);

    const fetchConfig = async () => {
        try {
            const apiUrl = API_URL;
            const response = await fetch(`${apiUrl}/api/system/config`);
            const data = await response.json();
            setConfig(data);
            setEditCap(data.daily_cap);
        } catch (error) {
            console.error("Failed to fetch config:", error);
        }
    };

    const fetchRoutes = async () => {
        try {
            const apiUrl = API_URL;
            const response = await fetch(`${apiUrl}/api/routes`);
            const data = await response.json();
            setRoutes(data);
        } catch (error) {
            console.error("Failed to fetch routes:", error);
        }
    };

    useEffect(() => {
        fetchConfig();
        fetchRoutes();
    }, []);

    const handleSaveConfig = async () => {
        setIsSaving(true);
        try {
            const apiUrl = API_URL;
            await fetch(`${apiUrl}/api/system/config`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ daily_cap: parseFloat(editCap) })
            });
            await fetchConfig();
            setIsEditModalOpen(false);
        } catch (error) {
            console.error("Failed to save config:", error);
        } finally {
            setIsSaving(false);
        }
    };

    const handleToggleAutoStop = async () => {
        try {
            const apiUrl = API_URL;
            await fetch(`${apiUrl}/api/system/config`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ auto_stop: !config.auto_stop })
            });
            await fetchConfig();
        } catch (error) {
            console.error("Failed to toggle auto-stop:", error);
        }
    };

    const handleToggleSystemPower = async () => {
        try {
            const apiUrl = API_URL;
            await fetch(`${apiUrl}/api/system/config`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ is_active: !config.is_active })
            });
            await fetchConfig();
            await fetchRoutes();
        } catch (error) {
            console.error("Failed to toggle system power:", error);
        }
    };

    const spendPercent = Math.min(100, (config.today_spend / config.daily_cap) * 100);

    return (
        <div className="space-y-6">
            <header className="mb-8 flex justify-between items-end">
                <div>
                    <h1 className="text-3xl font-bold text-white tracking-tight mb-1">Budget & Models</h1>
                    <p className="text-gray-400">Control spending limits and LLM routing behaviors.</p>
                </div>
                <div className="flex gap-4">
                    <div className="flex items-center gap-2 bg-navy-800 border border-gray-700 rounded-xl px-4 py-2">
                        <span className="text-sm text-gray-400 font-semibold uppercase tracking-wider">Daily Cap</span>
                        <span className="text-xl font-bold text-white">${parseFloat(config.daily_cap).toFixed(2)}</span>
                    </div>
                </div>
            </header>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Limits & Failsafe */}
                <Card className="lg:col-span-1 border-t-4 border-t-cyan-500 flex flex-col gap-6 bg-navy-900/40 backdrop-blur-sm">
                    <h3 className="text-xl font-semibold text-white flex items-center gap-2 border-b border-gray-800 pb-4">
                        <Wallet className="w-5 h-5 text-cyan-400" />
                        Limits & Failsafes
                    </h3>

                    <div className="space-y-6">
                        <div>
                            <div className="flex justify-between text-sm mb-2">
                                <span className="text-gray-400 font-medium">Daily Consumption</span>
                                <span className={`${spendPercent > 80 ? 'text-amber-400' : 'text-emerald-400'} font-bold`}>
                                    ${parseFloat(config.today_spend).toFixed(2)} / ${parseFloat(config.daily_cap).toFixed(2)}
                                </span>
                            </div>
                            <div className="w-full bg-gray-800 rounded-full h-3 overflow-hidden">
                                <div
                                    className={`h-full rounded-full transition-all duration-500 bg-gradient-to-r ${spendPercent > 80 ? 'from-amber-500 to-red-500' : 'from-emerald-400 to-cyan-500'}`}
                                    style={{ width: `${spendPercent}%` }}
                                ></div>
                            </div>
                        </div>

                        <div className="pt-6 border-t border-gray-800">
                            <div className="flex justify-between items-center mb-3">
                                <div className="text-sm text-gray-200 font-semibold flex items-center gap-2">
                                    <TrendingDown className="w-4 h-4 text-amber-500" />
                                    Auto-stop mechanism
                                </div>
                                <Toggle active={config.auto_stop} onClick={handleToggleAutoStop} />
                            </div>
                            <p className="text-xs text-gray-500 leading-relaxed">
                                The hybrid engine will automatically halt all agent operations and pause current pipeline if daily cap is reached to prevent budget overflow.
                            </p>
                        </div>
                    </div>

                    <div className="mt-auto pt-6 flex gap-3">
                        <Button
                            variant="secondary"
                            className="flex-1 border-gray-700 hover:border-cyan-500/50 transition-colors"
                            onClick={() => setIsEditModalOpen(true)}
                        >
                            <Settings2 className="w-4 h-4 mr-2" />
                            Adjust Limit
                        </Button>
                        <Button
                            variant={config.is_active ? "danger" : "success"}
                            className={`w-12 flex justify-center items-center shadow-lg ${config.is_active ? 'shadow-red-900/20' : 'shadow-emerald-900/20 active:scale-95'}`}
                            onClick={handleToggleSystemPower}
                        >
                            <Power className="w-4 h-4" />
                        </Button>
                    </div>
                </Card>

                {/* Model Routing Matrix */}
                <Card className="lg:col-span-2 bg-navy-900/40 backdrop-blur-sm relative overflow-hidden">
                    <div className="absolute top-0 right-0 w-64 h-64 bg-emerald-500/5 blur-3xl rounded-full -mr-32 -mt-32"></div>

                    <h3 className="text-xl font-semibold text-white mb-6 flex items-center gap-2 relative z-10">
                        <Settings2 className="w-5 h-5 text-emerald-400" />
                        LLM Routing Matrix
                        <span className="ml-auto text-[10px] font-mono text-gray-500 uppercase tracking-widest border border-gray-800 px-2 py-0.5 rounded">Real-time Routing</span>
                    </h3>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 relative z-10">
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

            {/* Edit Limit Modal */}
            {isEditModalOpen && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4">
                    <Card className="w-full max-w-md border-gray-700 shadow-2xl animate-in zoom-in duration-200">
                        <h2 className="text-xl font-bold text-white mb-2 flex items-center gap-2">
                            <DollarSign className="w-5 h-5 text-emerald-400" />
                            Adjust Daily Cap
                        </h2>
                        <p className="text-sm text-gray-400 mb-6 font-medium italic">Configure the safety threshold for LLM consumption.</p>

                        <div className="space-y-4">
                            <div>
                                <label className="block text-xs font-mono text-gray-500 uppercase tracking-wider mb-2">Max Spent per Day ($)</label>
                                <div className="relative">
                                    <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                                        <DollarSign className="h-4 h-4 text-gray-400" />
                                    </div>
                                    <input
                                        type="number"
                                        value={editCap}
                                        onChange={(e) => setEditCap(e.target.value)}
                                        className="block w-full pl-10 pr-4 py-3 bg-navy-900 border border-gray-700 rounded-xl text-white focus:ring-2 focus:ring-emerald-500/50 focus:border-emerald-500 transition-all outline-none"
                                        placeholder="0.00"
                                    />
                                </div>
                            </div>

                            <div className="p-4 rounded-xl bg-emerald-500/5 border border-emerald-500/10">
                                <p className="text-[10px] text-emerald-400 leading-relaxed font-medium">
                                    TIP: A cap of $15.00 is usually enough for ~300 high-quality script generations with Gemini Flash.
                                </p>
                            </div>
                        </div>

                        <div className="flex gap-3 mt-8">
                            <Button
                                variant="secondary"
                                className="flex-1 h-12"
                                onClick={() => setIsEditModalOpen(false)}
                                disabled={isSaving}
                            >
                                Cancel
                            </Button>
                            <Button
                                className="flex-1 bg-emerald-500 hover:bg-emerald-400 text-navy-950 font-bold h-12"
                                onClick={handleSaveConfig}
                                loading={isSaving}
                            >
                                Save Changes
                            </Button>
                        </div>
                    </Card>
                </div>
            )}
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
