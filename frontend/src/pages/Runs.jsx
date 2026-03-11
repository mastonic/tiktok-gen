import { API_URL } from '../api';
import React, { useState, useEffect } from 'react';
import { Modal, Card, Badge, Button } from '../components/ui';
import { Clock, DollarSign, Activity, Play, ChevronDown, RotateCcw, Eye, Zap, AlertCircle } from 'lucide-react';

const Runs = ({ setPath }) => {
    const [runs, setRuns] = useState([]);
    const [expandedRun, setExpandedRun] = useState(null);
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [pendingRunType, setPendingRunType] = useState(null);
    const [isLoading, setIsLoading] = useState(false);

    const handleOpenModal = (type) => {
        setPendingRunType(type);
        setIsModalOpen(true);
    };

    const triggerRun = async () => {
        if (!pendingRunType) return;
        setIsLoading(true);
        try {
            const apiUrl = API_URL;
            await fetch(`${apiUrl}/api/run/${pendingRunType}`, { method: 'POST' });
            setIsModalOpen(false);
        } catch (error) {
            console.error("Failed to trigger run:", error);
        } finally {
            setIsLoading(false);
        }
    };

    const handleStopRun = async (runId) => {
        setIsLoading(true);
        try {
            await fetch(`${API_URL}/api/run/${runId}/stop`, { method: 'POST' });
        } catch (error) {
            console.error("Failed to stop run:", error);
        } finally {
            setIsLoading(false);
        }
    };

    useEffect(() => {
        const fetchRuns = async () => {
            try {
                const apiUrl = API_URL;
                const response = await fetch(`${apiUrl}/api/runs`);
                const data = await response.json();
                setRuns(data);
                if (data.length > 0 && !expandedRun) setExpandedRun(data[0].id);
            } catch (error) {
                console.error("Failed to fetch runs:", error);
            }
        };
        fetchRuns();
        const intervalId = setInterval(fetchRuns, 3000);
        return () => clearInterval(intervalId);
    }, [expandedRun]);

    return (
        <div className="space-y-6 h-full flex flex-col">
            <header className="mb-8">
                <div className="flex justify-between items-end">
                    <div>
                        <h1 className="text-3xl font-bold text-white tracking-tight mb-1">Cycles d'Exécution</h1>
                        <p className="text-gray-400">Surveillez les lancements automatiques du système (matin et soir).</p>
                    </div>
                    <div className="flex gap-3">
                        <Button
                            onClick={() => handleOpenModal('matin')}
                            variant="secondary"
                            className="bg-amber-600/20 text-amber-400 border border-amber-600/30 hover:bg-amber-600/30"
                        >
                            <Zap className="w-4 h-4 mr-2" />
                            Run Matin
                        </Button>
                        <Button
                            onClick={() => handleOpenModal('soir')}
                            variant="primary"
                            className="bg-cyan-600/20 text-cyan-400 border border-cyan-600/30 hover:bg-cyan-600/30 shadow-[0_0_15px_rgba(6,182,212,0.15)]"
                        >
                            <Play className="w-4 h-4 mr-2" />
                            Run Soir
                        </Button>
                    </div>
                </div>
            </header>

            <Modal
                isOpen={isModalOpen}
                onClose={() => setIsModalOpen(false)}
                title={`Confirmer le Cycle ${pendingRunType?.toUpperCase()}`}
                footer={
                    <>
                        <Button variant="secondary" onClick={() => setIsModalOpen(false)}>Annuler</Button>
                        <Button
                            variant="primary"
                            onClick={triggerRun}
                            disabled={isLoading}
                            className="bg-cyan-600 hover:bg-cyan-500 shadow-lg shadow-cyan-900/20"
                        >
                            {isLoading ? (
                                <span className="flex items-center gap-2">
                                    <RotateCcw className="w-4 h-4 animate-spin" />
                                    Lancement...
                                </span>
                            ) : "Lancer la mission"}
                        </Button>
                    </>
                }
            >
                <div className="space-y-4">
                    <div className="flex items-start gap-4 p-4 bg-cyan-950/20 border border-cyan-500/20 rounded-xl">
                        <AlertCircle className="w-6 h-6 text-cyan-400 shrink-0 mt-1" />
                        <div>
                            <p className="text-white font-medium">Vous êtes sur le point de lancer l'essaim iM System.</p>
                            <p className="text-sm text-gray-400 mt-1">L'opération va rechercher des tendances, générer des scripts et préparer les Storyboards en arrière-plan.</p>
                        </div>
                    </div>

                    <div className="p-4 bg-navy-950 rounded-xl border border-gray-800 space-y-3">
                        <h4 className="text-xs font-bold text-gray-500 uppercase">Paramètres du Swarm</h4>
                        <div className="flex justify-between items-center text-sm">
                            <span className="text-gray-400 text-xs">Modèle Principal</span>
                            <Badge variant="cyber">GPT-4o / Gemini 1.5</Badge>
                        </div>
                        <div className="flex justify-between items-center text-sm">
                            <span className="text-gray-400 text-xs">Agents Actifs</span>
                            <span className="text-white">6 Agents Spécialisés</span>
                        </div>
                        <div className="flex justify-between items-center text-sm">
                            <span className="text-gray-400 text-xs">Coût Estimé</span>
                            <span className="text-amber-400">~$0.05 / run</span>
                        </div>
                    </div>
                </div>
            </Modal>

            <Card className="flex-1 overflow-hidden flex flex-col p-0 border border-gray-800">
                <div className="overflow-x-auto border-b border-gray-800">
                    <table className="w-full text-left border-collapse">
                        <thead>
                            <tr className="text-gray-400 text-sm bg-navy-900/80">
                                <th className="py-4 px-6 font-medium">ID Run</th>
                                <th className="py-4 px-6 font-medium">Planification</th>
                                <th className="py-4 px-6 font-medium">Statut</th>
                                <th className="py-4 px-6 font-medium text-right">Métriques</th>
                                <th className="py-4 px-6 font-medium text-center">Action</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-800/60">
                            {runs.map(run => (
                                <React.Fragment key={run.id}>
                                    <tr
                                        className={`hover:bg-cyan-900/10 transition-colors cursor-pointer group ${expandedRun === run.id ? 'bg-navy-900/40' : ''}`}
                                        onClick={() => setExpandedRun(run.id === expandedRun ? null : run.id)}
                                    >
                                        <td className="py-4 px-6">
                                            <div className="flex items-center gap-3">
                                                <ChevronDown className={`w-4 h-4 text-gray-500 transition-transform ${expandedRun === run.id ? 'rotate-180 text-cyan-400' : ''}`} />
                                                <div>
                                                    <div className="font-semibold text-gray-200">{run.name}</div>
                                                    <div className="text-xs text-gray-500 font-mono mt-0.5">{run.id}</div>
                                                </div>
                                            </div>
                                        </td>
                                        <td className="py-4 px-6">
                                            <div className="flex items-center gap-2 text-gray-300">
                                                <Clock className="w-4 h-4 text-gray-500" />
                                                {run.time}
                                            </div>
                                        </td>
                                        <td className="py-4 px-6">
                                            <div className="flex flex-col gap-2">
                                                <Badge variant={run.status === 'completed' ? 'success' : 'cyber'} className="flex inline-flex items-center gap-1.5 px-3 py-1 w-fit">
                                                    {run.status === 'running' && <span className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse"></span>}
                                                    {run.status === 'completed' ? 'TERMINÉ' : run.status === 'running' ? 'EN COURS' : run.status.toUpperCase()}
                                                </Badge>
                                                {run.status === 'running' && (
                                                    <div className="flex flex-col gap-1">
                                                        <div className="w-32 bg-gray-800 rounded-full h-1.5 overflow-hidden border border-gray-700">
                                                            <div
                                                                className="bg-gradient-to-r from-cyan-600 to-cyan-400 h-full transition-all duration-1000"
                                                                style={{ width: `${run.progress_percent || 0}%` }}
                                                            ></div>
                                                        </div>
                                                        <span className="text-[10px] text-cyan-400 font-mono animate-pulse uppercase">
                                                            {run.current_step || 'Initialisation...'}
                                                        </span>
                                                    </div>
                                                )}
                                            </div>
                                        </td>
                                        <td className="py-4 px-6 text-right">
                                            <div className="flex flex-col items-end gap-1 text-sm font-mono">
                                                <div className="text-amber-400 flex items-center gap-1"><DollarSign className="w-3.5 h-3.5" />{run.cost.toFixed(2)}</div>
                                                <div className="text-emerald-400 flex items-center gap-1"><Activity className="w-3.5 h-3.5" />{run.duration}</div>
                                            </div>
                                        </td>
                                        <td className="py-4 px-6 text-center">
                                            {run.status === 'running' ? (
                                                <Button
                                                    variant="danger"
                                                    onClick={(e) => { e.stopPropagation(); handleStopRun(run.id); }}
                                                    disabled={isLoading}
                                                    className="px-3 py-1 text-xs flex items-center gap-2 mx-auto bg-red-600/20 text-red-500 border-red-500/30 hover:bg-red-600/40"
                                                >
                                                    <AlertCircle className="w-3 h-3" /> STOP
                                                </Button>
                                            ) : (
                                                <Button variant="secondary" className="px-3 py-1 text-xs opacity-0 group-hover:opacity-100 flex items-center gap-2 mx-auto">
                                                    <RotateCcw className="w-3 h-3" /> Relancer
                                                </Button>
                                            )}
                                        </td>
                                    </tr>

                                    {expandedRun === run.id && (
                                        <tr className="bg-navy-900/60 border-b-2 border-b-cyan-500/20">
                                            <td colSpan="5" className="p-6">
                                                <div className="flex flex-col lg:flex-row gap-8">

                                                    {/* Timeline */}
                                                    <div className="flex-1">
                                                        <div className="flex justify-between items-center mb-6">
                                                            <h4 className="text-sm font-semibold text-gray-400 uppercase tracking-wider">Pipeline d'Exécution du Swarm</h4>
                                                            {run.status === 'running' && (
                                                                <Badge variant="outline" className="text-cyan-400 border-cyan-500/30 bg-cyan-500/5">
                                                                    ÉTAPE: {run.current_step} ({run.progress_percent}%)
                                                                </Badge>
                                                            )}
                                                        </div>

                                                        <div className="relative border-l-2 border-gray-700 ml-4 space-y-6">
                                                            <TimelineStep title="Analyse des Tendances & Setup" time="00:00" duration="1m 30s" active={run.status === 'running'} status="done" />
                                                            <TimelineStep title="Scoring Viral & Monétisation" time="01:30" duration="2m 10s" active={run.status === 'running'} status="done" />
                                                            <TimelineStep title="Génération & Optimisation des Scripts" time="03:40" duration="3m 45s" active={run.status === 'running'} status={run.status === 'completed' ? 'done' : 'current'} error={false} />
                                                            <TimelineStep title="Appels API Directeurs Vidéo" time="07:25" duration="En attente" active={run.status === 'running'} status={run.status === 'completed' ? 'done' : 'pending'} />
                                                            <TimelineStep title="Revue & Publication" time="--" duration="--" active={run.status === 'running'} status={run.status === 'completed' ? 'done' : 'pending'} />
                                                        </div>
                                                    </div>

                                                    <div className="w-full lg:w-72 space-y-4">
                                                        <div className="glass-panel p-4 rounded-xl border-dashed">
                                                            <h4 className="text-xs uppercase font-semibold text-gray-500 mb-3">Sorties Générées</h4>
                                                            <div className="space-y-2">
                                                                <div className="flex justify-between items-center text-sm p-2 bg-navy-800 rounded">
                                                                    <span className="text-gray-300">Scripts</span>
                                                                    <span className="font-bold text-cyan-400">4</span>
                                                                </div>
                                                                <div className="flex justify-between items-center text-sm p-2 bg-navy-800 rounded">
                                                                    <span className="text-gray-300">Vidéos</span>
                                                                    <span className="font-bold text-emerald-400">{run.status === 'completed' ? '2' : '0'}</span>
                                                                </div>
                                                            </div>
                                                        </div>

                                                        <Button
                                                            variant="primary"
                                                            onClick={() => setPath('/chat')}
                                                            className="w-full flex items-center justify-center gap-2 py-3 shadow-lg shadow-cyan-500/20 active:scale-95 transition-transform"
                                                        >
                                                            <Eye className="w-4 h-4" /> Voir les Logs Complets
                                                        </Button>
                                                    </div>

                                                </div>
                                            </td>
                                        </tr>
                                    )}
                                </React.Fragment>
                            ))}
                        </tbody>
                    </table>
                </div>
            </Card>
        </div>
    );
};

const TimelineStep = ({ title, time, duration, active, status, error }) => {
    return (
        <div className="relative pl-8">
            <div className={`absolute -left-[9px] top-1 w-4 h-4 rounded-full border-2 bg-navy-900 ${status === 'done' ? 'border-emerald-500 bg-emerald-500/20' :
                status === 'current' ? 'border-cyan-400 shadow-[0_0_10px_rgba(6,182,212,0.8)]' :
                    error ? 'border-red-500' : 'border-gray-700'
                }`}>
                {status === 'current' && <div className="absolute inset-0 bg-cyan-400 rounded-full animate-ping opacity-50"></div>}
            </div>

            <div className="flex justify-between items-start">
                <div>
                    <div className={`font-medium ${status === 'done' ? 'text-gray-300' : status === 'current' ? 'text-cyan-400 font-semibold text-glow' : 'text-gray-600'}`}>
                        {title}
                    </div>
                    {error && <p className="text-xs text-red-400 mt-1">Failed to connect to API endpoint.</p>}
                </div>
                <div className="flex flex-col items-end text-xs font-mono">
                    <span className={status === 'current' ? 'text-cyan-400' : 'text-gray-500'}>{duration}</span>
                    <span className="text-gray-600">+{time}</span>
                </div>
            </div>
        </div>
    );
};

export default Runs;
