import React, { useState, useEffect } from 'react';
import { Card, Badge, Button, Modal } from '../components/ui';
import { ShieldCheck, Cpu, Play, Terminal, Settings2, Save, Loader2, CheckCircle2 } from 'lucide-react';

const Agents = () => {
    const [agents, setAgents] = useState([]);
    const [selectedAgent, setSelectedAgent] = useState(null);
    const [isEditModalOpen, setIsEditModalOpen] = useState(false);
    const [isSaving, setIsSaving] = useState(false);
    const [saveSuccess, setSaveSuccess] = useState(false);

    // Form state
    const [editModel, setEditModel] = useState('');

    const fetchAgents = async () => {
        try {
            const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:5656';
            const response = await fetch(`${apiUrl}/api/agents`);
            const data = await response.json();
            setAgents(data);
        } catch (error) {
            console.error("Failed to fetch agents:", error);
        }
    };

    useEffect(() => {
        fetchAgents();
    }, []);

    const handleOpenEdit = (agent) => {
        setSelectedAgent(agent);
        setEditModel(agent.model || 'openai/gpt-4o-mini');
        setIsEditModalOpen(true);
        setSaveSuccess(false);
    };

    const handleSaveAgent = async () => {
        if (!selectedAgent) return;
        setIsSaving(true);
        try {
            const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:5656';
            const response = await fetch(`${apiUrl}/api/agents/update`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    id: selectedAgent.id,
                    model: editModel
                })
            });
            const data = await response.json();
            if (data.status === 'success') {
                setSaveSuccess(true);
                setTimeout(() => {
                    setIsEditModalOpen(false);
                    fetchAgents();
                }, 1500);
            }
        } catch (error) {
            console.error("Failed to save agent:", error);
        } finally {
            setIsSaving(false);
        }
    };

    const handleAction = (agentName, actionName) => {
        // Placeholder for real actions if needed later
        console.log(`Action [${actionName}] triggered for agent: ${agentName}!`);
    };

    return (
        <div className="space-y-6">
            <header className="mb-8">
                <h1 className="text-3xl font-bold text-white tracking-tight mb-1">Agent Fleet</h1>
                <p className="text-gray-400">Manage autonomous workers and LLM model bindings.</p>
            </header>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
                {agents.map(agent => (
                    <Card key={agent.id} className="relative flex flex-col group overflow-hidden border border-gray-800 hover:border-cyan-500/30 transition-all duration-300">
                        <div className="absolute -right-6 -top-6 opacity-5 rotate-12 group-hover:rotate-0 group-hover:opacity-10 transition-all duration-500 text-cyan-500">
                            <Cpu className="w-32 h-32" />
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

                        <div className="space-y-3 mb-4 z-10">
                            <div className="bg-navy-900/80 p-3 rounded-xl border border-gray-800/50">
                                <div className="text-[10px] text-gray-500 font-mono mb-1 uppercase tracking-wider">Model Model</div>
                                <div className="text-xs font-bold text-gray-200 truncate">{agent.model || 'gpt-4o'}</div>
                            </div>

                            <div className="grid grid-cols-2 gap-2">
                                <div className="bg-navy-900/80 p-2 rounded border border-gray-800/50">
                                    <div className="text-[10px] text-gray-500 font-mono mb-1 uppercase tracking-wide">Status</div>
                                    <div className={`text-[10px] font-bold uppercase ${agent.status === 'Executing' ? 'text-cyan-400 animate-pulse' : 'text-emerald-500'}`}>
                                        {agent.status || 'Idle'}
                                    </div>
                                </div>
                                <div className="bg-navy-900/80 p-2 rounded border border-gray-800/50">
                                    <div className="text-[10px] text-gray-500 font-mono mb-1 uppercase tracking-wide">Health</div>
                                    <div className="text-[10px] font-bold text-white">100%</div>
                                </div>
                            </div>
                        </div>

                        <div className="mt-auto pt-4 border-t border-gray-800 grid grid-cols-3 gap-2 z-10">
                            <Button variant="secondary" className="text-[10px] !py-2 flex flex-col items-center gap-1 opacity-60 hover:opacity-100" onClick={() => handleAction(agent.role, 'Prompt')}>
                                <Terminal className="w-3.5 h-3.5" />
                                <span>Prompt</span>
                            </Button>
                            <Button variant="secondary" className="text-[10px] !py-2 flex flex-col items-center gap-1 opacity-60 hover:opacity-100" onClick={() => handleAction(agent.role, 'Test')}>
                                <Play className="w-3.5 h-3.5" />
                                <span>Test</span>
                            </Button>
                            <Button variant="secondary" className="text-[10px] !py-2 flex flex-col items-center gap-1 text-cyan-500 border-cyan-500/20 hover:bg-cyan-500/10" onClick={() => handleOpenEdit(agent)}>
                                <Settings2 className="w-3.5 h-3.5" />
                                <span>Config</span>
                            </Button>
                        </div>
                    </Card>
                ))}
            </div>

            <Modal
                isOpen={isEditModalOpen}
                onClose={() => !isSaving && setIsEditModalOpen(false)}
                title={`Configuration : ${selectedAgent?.name}`}
                footer={
                    <>
                        <Button variant="secondary" onClick={() => setIsEditModalOpen(false)} disabled={isSaving}>Annuler</Button>
                        <Button
                            variant="primary"
                            onClick={handleSaveAgent}
                            disabled={isSaving || saveSuccess}
                            className="bg-cyan-600 hover:bg-cyan-500 min-w-[120px]"
                        >
                            {isSaving ? (
                                <span className="flex items-center gap-2">
                                    <Loader2 className="w-4 h-4 animate-spin" />
                                    Sauvegarde...
                                </span>
                            ) : saveSuccess ? (
                                <span className="flex items-center gap-2">
                                    <CheckCircle2 className="w-4 h-4" />
                                    Enregistré !
                                </span>
                            ) : (
                                <span className="flex items-center gap-2">
                                    <Save className="w-4 h-4" />
                                    Sauvegarder
                                </span>
                            )}
                        </Button>
                    </>
                }
            >
                <div className="space-y-4">
                    <div>
                        <label className="text-xs font-bold text-gray-500 uppercase mb-2 block">Cerveau LLM (Model)</label>
                        <select
                            value={editModel}
                            onChange={(e) => setEditModel(e.target.value)}
                            className="w-full bg-navy-950 border border-gray-700 rounded-xl p-3 text-white focus:ring-2 focus:ring-cyan-500 focus:border-transparent outline-none transition-all"
                        >
                            <option value="openai/gpt-4o-mini">GPT-4o Mini (Économique)</option>
                            <option value="openai/gpt-4o">GPT-4o (Puissant)</option>
                            <option value="openai/o1-mini">O1 Mini (Raisonnement)</option>
                            <option value="google/gemini-1.5-flash">Gemini 1.5 Flash (Rapide)</option>
                            <option value="google/gemini-1.5-pro">Gemini 1.5 Pro (Ultra)</option>
                        </select>
                    </div>

                    <div className="p-4 bg-amber-500/10 border border-amber-500/20 rounded-xl">
                        <p className="text-[10px] text-amber-200 leading-relaxed uppercase font-bold tracking-wider mb-1">Attention Core Engine</p>
                        <p className="text-xs text-amber-100/70">
                            Changer le modèle affecte directement la précision de l'agent et le coût de génération. GPT-4o Mini est recommandé pour la plupart des tâches.
                        </p>
                    </div>
                </div>
            </Modal>
        </div>
    );
};

const BotIcon = ({ role, className }) => {
    if (role?.includes('Risk') || role?.includes('Judge')) return <ShieldCheck className={className} />;
    return <Cpu className={className} />;
};

const Toggle = ({ active }) => (
    <div className={`w-10 h-5 rounded-full p-0.5 transition-colors duration-300 ${active ? 'bg-cyan-500 shadow-[0_0_8px_rgba(6,182,212,0.6)]' : 'bg-gray-700'}`}>
        <div className={`w-4 h-4 rounded-full bg-white transition-transform duration-300 ${active ? 'translate-x-5' : 'translate-x-0'}`}></div>
    </div>
);

export default Agents;
