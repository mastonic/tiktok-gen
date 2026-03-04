import React, { useState, useEffect } from 'react';
import { Card, Badge, Button } from '../components/ui';
import { ShieldCheck, ShieldAlert, Cpu, Activity, Play, Terminal } from 'lucide-react';

const Agents = () => {
    const [agents, setAgents] = useState([]);

    useEffect(() => {
        const fetchAgents = async () => {
            try {
                const response = await fetch('http://localhost:8000/api/agents');
                const data = await response.json();
                setAgents(data);
            } catch (error) {
                console.error("Failed to fetch agents:", error);
            }
        };
        fetchAgents();
    }, []);
    const handleAction = (agentName, actionName) => {
        alert(`Action [${actionName}] triggered for agent: ${agentName}! (Feature in development)`);
    };

    return (
        <div className="space-y-6">
            <header className="mb-8">
                <h1 className="text-3xl font-bold text-white tracking-tight mb-1">Agent Fleet</h1>
                <p className="text-gray-400">Manage autonomous workers and LLM model bindings.</p>
            </header>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
                {agents.map(agent => (
                    <Card key={agent.id} className="relative flex flex-col group overflow-hidden">
                        <div className="absolute -right-6 -top-6 opacity-5 rotate-12 group-hover:rotate-0 group-hover:opacity-10 transition-all duration-500">
                            <Cpu className="w-32 h-32 text-cyan-500" />
                        </div>

                        <div className="flex justify-between items-start mb-4 z-10">
                            <div className="flex items-center gap-2">
                                <div className="w-8 h-8 rounded bg-cyan-900/40 border border-cyan-500/50 flex items-center justify-center shadow-[0_0_10px_rgba(6,182,212,0.2)]">
                                    <BotIcon role={agent.role} className="w-4 h-4 text-cyan-400" />
                                </div>
                                <h3 className="font-semibold text-gray-100">{agent.name}</h3>
                            </div>
                            <Toggle active={agent.status === "Executing"} />
                        </div>

                        <div className="grid grid-cols-2 gap-2 mb-4 z-10">
                            <div className="bg-navy-900/80 p-2 rounded border border-gray-800">
                                <div className="text-[10px] text-gray-500 font-mono mb-1 uppercase tracking-wide">Status</div>
                                <div className="text-xs font-medium text-emerald-400 capitalize">{agent.status || 'Idle'}</div>
                            </div>
                            <div className="bg-navy-900/80 p-2 rounded border border-gray-800">
                                <div className="text-[10px] text-gray-500 font-mono mb-1 uppercase tracking-wide">Performance</div>
                                <div className="text-xs font-medium text-cyan-400">{agent.performance || 100}%</div>
                            </div>
                        </div>

                        <div className="mt-auto pt-4 border-t border-gray-800 grid grid-cols-2 gap-2 z-10">
                            <Button variant="secondary" className="text-xs !py-1.5 flex justify-center items-center gap-1.5 hover:text-cyan-400" onClick={() => handleAction(agent.role, 'Prompt')}>
                                <Terminal className="w-3 h-3" /> Prompt
                            </Button>
                            <Button variant="secondary" className="text-xs !py-1.5 flex justify-center items-center gap-1.5 hover:text-emerald-400" onClick={() => handleAction(agent.role, 'Test')}>
                                <Play className="w-3 h-3" /> Test
                            </Button>
                        </div>
                    </Card>
                ))}
            </div>
        </div>
    );
};

const BotIcon = ({ role, className }) => {
    // Simplified icon selection
    if (role.includes('Risk') || role.includes('Judge')) return <ShieldCheck className={className} />;
    return <Cpu className={className} />;
};

const Toggle = ({ active }) => (
    <div className={`w-10 h-5 rounded-full p-0.5 transition-colors duration-300 ${active ? 'bg-cyan-500 shadow-[0_0_8px_rgba(6,182,212,0.6)]' : 'bg-gray-700'}`}>
        <div className={`w-4 h-4 rounded-full bg-white transition-transform duration-300 ${active ? 'translate-x-5' : 'translate-x-0'}`}></div>
    </div>
);

export default Agents;
