import { API_URL } from '../api';
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
    const [isPromptModalOpen, setIsPromptModalOpen] = useState(false);
    const [isTestingAgent, setIsTestingAgent] = useState(false);
    const [testResult, setTestResult] = useState(null);

    // Form state
    const [editModel, setEditModel] = useState('');
    const [editGoal, setEditGoal] = useState('');
    const [editBackstory, setEditBackstory] = useState('');

    const fetchAgents = async () => {
        try {
            const apiUrl = API_URL;
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
        setEditGoal(agent.goal || '');
        setEditBackstory(agent.backstory || '');
        setIsEditModalOpen(true);
        setSaveSuccess(false);
    };

    const handleOpenPrompt = (agent) => {
        setSelectedAgent(agent);
        setIsPromptModalOpen(true);
    };

    const handleTestAction = (agent) => {
        setSelectedAgent(agent);
        setIsTestingAgent(true);
        setTestResult(null);

        // Simuler un test de connexion au LLM
        setTimeout(() => {
            setTestResult({
                status: 'success',
                latency: '450ms',
                message: 'LLM Connection stable. Model responding.'
            });
        }, 1500);
    };

    const handleSaveAgent = async () => {
        if (!selectedAgent) return;
        setIsSaving(true);
        try {
            const apiUrl = API_URL;
            const response = await fetch(`${apiUrl}/api/agents/update`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    id: selectedAgent.id,
                    model: editModel,
                    goal: editGoal,
                    backstory: editBackstory
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

    const handleResetAgent = async () => {
        if (!selectedAgent || !window.confirm("Réinitialiser cet agent aux paramètres d'usine ?")) return;
        setIsSaving(true);
        try {
            const apiUrl = API_URL;
            const response = await fetch(`${apiUrl}/api/agents/${selectedAgent.id}/reset`, {
                method: 'POST'
            });
            if (response.ok) {
                setSaveSuccess(true);
                setTimeout(() => {
                    setIsEditModalOpen(false);
                    fetchAgents();
                }, 1000);
            }
        } catch (error) {
            console.error("Failed to reset agent:", error);
        } finally {
            setIsSaving(false);
        }
    };

    const handleToggleAgent = async (agent) => {
        try {
            const apiUrl = API_URL;
            const newStatus = !agent.is_active;
            const response = await fetch(`${apiUrl}/api/agents/update`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    id: agent.id,
                    is_active: newStatus
                })
            });
            if (response.ok) {
                fetchAgents();
            }
        } catch (error) {
            console.error("Failed to toggle agent:", error);
        }
    };

    const getAgentDetails = (role) => {
        const details = {
            'TrendRadar': { goal: 'Scanner les flux RSS et GitHub.', backstory: 'Expert en sourcing Open Source.' },
            'ViralJudge': { goal: 'Valider la gratuité et le potentiel viral.', backstory: 'Analyste de tendances impitoyable.' },
            'MonetizationScorer': { goal: 'Attribuer un score de rentabilité ROI.', backstory: 'Consultant en rentabilité focalisé sur le profit.' },
            'ScriptArchitect': { goal: 'Rédiger des scripts TikTok percutants.', backstory: 'Scénariste vedette ironique.' },
            'VisualPromptist': { goal: 'Créer des prompts d\'images pour FLUX.', backstory: 'Directeur artistique de haut vol.' },
            'QualityController': { goal: 'Vérifier la cohérence globale.', backstory: 'Garant final de la qualité iM System.' },
            'TikTokDistributor': { goal: 'Optimiser la distribution et les hashtags.', backstory: 'Expert en algorithmes sociaux.' },
            'ViralGrowthCommander': { goal: 'Piloter l\'attention et le watch-time.', backstory: 'Chef d\'orchestre de la croissance virale.' }
        };
        return details[role] || { goal: 'Mission autonome.', backstory: 'Agent intelligent de la flotte.' };
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
                            <Toggle active={agent.is_active} onClick={() => handleToggleAgent(agent)} />
                        </div>

                        <div className="space-y-3 mb-4 z-10">
                            <div className="bg-navy-900/80 p-3 rounded-xl border border-gray-800/50">
                                <div className="text-[10px] text-gray-500 font-mono mb-1 uppercase tracking-wider">Model Binding</div>
                                <div className="text-xs font-bold text-gray-200 truncate">{agent.model || 'gpt-4o'}</div>
                            </div>

                            <div className="grid grid-cols-2 gap-2">
                                <div className="bg-navy-900/80 p-2 rounded border border-gray-800/50">
                                    <div className="text-[10px] text-gray-500 font-mono mb-1 uppercase tracking-wide">Status</div>
                                    <div className={`text-[10px] font-bold uppercase ${!agent.is_active ? 'text-gray-600' : agent.status === 'Executing' ? 'text-cyan-400 animate-pulse' : 'text-emerald-500'}`}>
                                        {!agent.is_active ? 'Offline' : (agent.status || 'Idle')}
                                    </div>
                                </div>
                                <div className="bg-navy-900/80 p-2 rounded border border-gray-800/50">
                                    <div className="text-[10px] text-gray-500 font-mono mb-1 uppercase tracking-wide">Health</div>
                                    <div className="text-[10px] font-bold text-white">100%</div>
                                </div>
                            </div>
                        </div>

                        <div className="mt-auto pt-4 border-t border-gray-800 grid grid-cols-3 gap-2 z-10">
                            <Button variant="secondary" className="text-[10px] !py-2 flex flex-col items-center gap-1 hover:text-cyan-400" onClick={() => handleOpenPrompt(agent)}>
                                <Terminal className="w-3.5 h-3.5" />
                                <span>Prompt</span>
                            </Button>
                            <Button variant="secondary" className="text-[10px] !py-2 flex flex-col items-center gap-1 hover:text-cyan-400" onClick={() => handleTestAction(agent)}>
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

            {/* Config Modal */}
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
                <div className="space-y-4 max-h-[60vh] overflow-y-auto pr-2 custom-scrollbar">
                    <div className="flex justify-end">
                        <button
                            onClick={handleResetAgent}
                            className="text-[10px] text-pink-500 hover:text-pink-400 font-bold uppercase tracking-wider flex items-center gap-1 border border-pink-500/30 px-2 py-1 rounded hover:bg-pink-500/5 transition-all"
                        >
                            <ShieldCheck className="w-3 h-3" /> Reset to Factory Defaults
                        </button>
                    </div>

                    <div>
                        <label className="text-xs font-bold text-gray-500 uppercase mb-2 block tracking-widest">Cerveau LLM (Model)</label>
                        <select
                            value={editModel}
                            onChange={(e) => setEditModel(e.target.value)}
                            className="w-full bg-navy-950 border border-gray-700 rounded-xl p-4 text-white focus:ring-2 focus:ring-cyan-500 focus:border-transparent outline-none transition-all appearance-none cursor-pointer"
                            style={{ backgroundImage: 'linear-gradient(45deg, transparent 50%, gray 50%), linear-gradient(135deg, gray 50%, transparent 50%)', backgroundPosition: 'calc(100% - 20px) calc(1em + 2px), calc(100% - 15px) calc(1em + 2px)', backgroundSize: '5px 5px, 5px 5px', backgroundRepeat: 'no-repeat' }}
                        >
                            <option value="openai/gpt-4o-mini" className="bg-navy-900 text-white p-2">GPT-4o Mini (Économique)</option>
                            <option value="openai/gpt-4o" className="bg-navy-900 text-white p-2">GPT-4o (Puissant)</option>
                            <option value="openai/o1-mini" className="bg-navy-900 text-white p-2">O1 Mini (Raisonnement)</option>
                            <option value="google/gemini-1.5-flash" className="bg-navy-900 text-white p-2">Gemini 1.5 Flash (Rapide)</option>
                            <option value="google/gemini-1.5-pro" className="bg-navy-900 text-white p-2">Gemini 1.5 Pro (Ultra)</option>
                        </select>
                    </div>

                    <div>
                        <label className="text-xs font-bold text-gray-500 uppercase mb-2 block tracking-widest">Agent Mission (Goal)</label>
                        <textarea
                            value={editGoal}
                            onChange={(e) => setEditGoal(e.target.value)}
                            rows={3}
                            className="w-full bg-navy-950 border border-gray-700 rounded-xl p-4 text-gray-200 text-sm focus:ring-2 focus:ring-cyan-500 focus:border-transparent outline-none transition-all resize-none"
                            placeholder="Définissez la mission principale..."
                        />
                    </div>

                    <div>
                        <label className="text-xs font-bold text-gray-500 uppercase mb-2 block tracking-widest">Psychological Profile (Backstory)</label>
                        <textarea
                            value={editBackstory}
                            onChange={(e) => setEditBackstory(e.target.value)}
                            rows={4}
                            className="w-full bg-navy-950 border border-gray-700 rounded-xl p-4 text-gray-200 text-sm focus:ring-2 focus:ring-cyan-500 focus:border-transparent outline-none transition-all resize-none"
                            placeholder="Définissez le caractère et l'historique de l'agent..."
                        />
                    </div>

                    <div className="p-4 bg-amber-500/10 border border-amber-500/20 rounded-xl">
                        <p className="text-[10px] text-amber-200 leading-relaxed uppercase font-bold tracking-wider mb-1 flex items-center gap-2">
                            <ShieldCheck className="w-3 h-3" /> Attention Core Engine
                        </p>
                        <p className="text-xs text-amber-100/70">
                            Changer le modèle ou le prompt affecte directement la précision de l'agent et le coût de génération.
                        </p>
                    </div>
                </div>
            </Modal>

            {/* Prompt Detail Modal */}
            <Modal
                isOpen={isPromptModalOpen}
                onClose={() => setIsPromptModalOpen(false)}
                title={`Core Directives : ${selectedAgent?.name}`}
            >
                <div className="space-y-5">
                    <div>
                        <h4 className="text-[10px] font-bold text-cyan-400 uppercase tracking-widest mb-2">Agent Mission (Goal)</h4>
                        <div className="p-4 bg-navy-950/50 rounded-xl border border-gray-800 text-sm text-gray-300 italic">
                            "{selectedAgent?.goal || getAgentDetails(selectedAgent?.role).goal}"
                        </div>
                    </div>
                    <div>
                        <h4 className="text-[10px] font-bold text-cyan-400 uppercase tracking-widest mb-2">Psychological Profile (Backstory)</h4>
                        <div className="p-4 bg-navy-950/50 rounded-xl border border-gray-800 text-sm text-gray-300">
                            {selectedAgent?.backstory || getAgentDetails(selectedAgent?.role).backstory}
                        </div>
                    </div>
                </div>
            </Modal>

            {/* Test Connection Modal */}
            <Modal
                isOpen={isTestingAgent}
                onClose={() => setIsTestingAgent(false)}
                title={`Diagnostic : ${selectedAgent?.name}`}
            >
                <div className="flex flex-col items-center justify-center py-8">
                    {!testResult ? (
                        <>
                            <Loader2 className="w-12 h-12 text-cyan-500 animate-spin mb-4" />
                            <p className="text-sm text-gray-400 animate-pulse">Requesting LLM tokens...</p>
                        </>
                    ) : (
                        <div className="w-full space-y-4">
                            <div className="flex justify-center mb-2">
                                <CheckCircle2 className="w-12 h-12 text-emerald-500" />
                            </div>
                            <p className="text-center font-bold text-white tracking-wide">LLM CONNECTION STABLE</p>
                            <div className="grid grid-cols-2 gap-3">
                                <div className="bg-navy-950/50 p-3 rounded-lg border border-gray-800">
                                    <div className="text-[8px] text-gray-500 uppercase mb-1">Latency</div>
                                    <div className="text-xs text-emerald-400 font-mono">{testResult.latency}</div>
                                </div>
                                <div className="bg-navy-950/50 p-3 rounded-lg border border-gray-800">
                                    <div className="text-[8px] text-gray-500 uppercase mb-1">Status</div>
                                    <div className="text-xs text-emerald-400 font-mono">READY</div>
                                </div>
                            </div>
                            <p className="text-[10px] text-gray-500 text-center italic mt-2">"{testResult.message}"</p>
                            <Button variant="secondary" onClick={() => setIsTestingAgent(false)} className="w-full mt-2">Close Diagnostic</Button>
                        </div>
                    )}
                </div>
            </Modal>
        </div>
    );
};

const BotIcon = ({ role, className }) => {
    if (role?.includes('Risk') || role?.includes('Judge')) return <ShieldCheck className={className} />;
    return <Cpu className={className} />;
};

const Toggle = ({ active, onClick }) => (
    <div
        onClick={onClick}
        className={`w-10 h-5 rounded-full p-0.5 transition-colors duration-300 cursor-pointer ${active ? 'bg-cyan-500 shadow-[0_0_8px_rgba(6,182,212,0.6)]' : 'bg-gray-700'}`}
    >
        <div className={`w-4 h-4 rounded-full bg-white transition-transform duration-300 ${active ? 'translate-x-5' : 'translate-x-0'}`}></div>
    </div>
);

export default Agents;
