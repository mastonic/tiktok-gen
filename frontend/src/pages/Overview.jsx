import { API_URL } from '../api';
import React, { useState, useEffect } from 'react';
import { Card, Badge, Button } from '../components/ui';
import {
    Bot,
    Video,
    DollarSign,
    TrendingUp,
    AlertTriangle,
    Play
} from 'lucide-react';

const Overview = () => {
    const [isRunning, setIsRunning] = useState(false);
    const [trends, setTrends] = useState([]);
    const [alerts, setAlerts] = useState([]);

    const [overviewData, setOverviewData] = useState({
        activeAgents: '0/10',
        videosToday: '0/2',
        aiCostToday: '$0.00',
        estProfitScore: '0.0',
        budgetRemaining: '$0.00',
        isRunning: false,
        lastRunId: null
    });
    const [config, setConfig] = useState({ commando_mode: false });

    useEffect(() => {
        const fetchData = async () => {
            try {
                const apiUrl = API_URL;
                const [overviewRes, trendsRes, alertsRes, configRes] = await Promise.all([
                    fetch(`${apiUrl}/api/overview`),
                    fetch(`${apiUrl}/api/trends`),
                    fetch(`${apiUrl}/api/alerts`),
                    fetch(`${apiUrl}/api/system/config`)
                ]);
                const overviewData = await overviewRes.json();
                const trendsData = await trendsRes.json();
                const alertsData = await alertsRes.json();
                const configData = await configRes.json();

                setOverviewData(overviewData);
                setTrends(trendsData);
                setAlerts(alertsData);
                setConfig(configData);
            } catch (error) {
                console.error("Error fetching dashboard data:", error);
            }
        };

        fetchData();
        const intervalId = setInterval(fetchData, 3000);
        return () => clearInterval(intervalId);
    }, []);
    const handleRunCycle = async (type) => {
        setIsRunning(true);
        try {
            const apiUrl = API_URL;
            const response = await fetch(`${apiUrl}/api/run`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ type })
            });
            const data = await response.json();
            console.log(data);
        } catch (error) {
            console.error("Error starting run:", error);
            alert(`Failed to start ${type} run.`);
        } finally {
            setIsRunning(false);
        }
    };

    const handleStopScan = async () => {
        if (!overviewData.lastRunId) return;
        setIsRunning(true);
        try {
            await fetch(`${API_URL}/api/run/${overviewData.lastRunId}/stop`, { method: 'POST' });
        } catch (error) {
            console.error("Error stopping run:", error);
        } finally {
            setIsRunning(false);
        }
    };

    return (
        <div className="space-y-6">
            <header className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-8">
                <div>
                    <h1 className="text-3xl font-bold text-white tracking-tight mb-1">Tableau de Bord</h1>
                    <div className="flex items-center gap-2">
                        <p className="text-gray-400 text-sm">État du système et indicateurs clés pour aujourd'hui.</p>
                        {config.commando_mode && (
                            <Badge variant="danger" className="animate-pulse bg-red-500/20 text-red-500 border border-red-500/50 flex items-center gap-1">
                                <TrendingUp className="w-3 h-3" /> COMMANDO 10K ACTIF
                            </Badge>
                        )}
                    </div>
                </div>
                <div className="flex gap-3 w-full sm:w-auto">
                    {overviewData.isRunning ? (
                        <Button
                            variant="danger"
                            className="w-full sm:w-auto flex items-center justify-center gap-2 bg-red-600/20 text-red-500 border border-red-500/50 hover:bg-red-600/40 transition-all font-black animate-pulse px-8"
                            onClick={handleStopScan}
                            disabled={isRunning}
                        >
                            <AlertTriangle className="h-4 w-4" />
                            ARRÊTER LE SCAN
                        </Button>
                    ) : (
                        <>
                            <Button
                                variant="secondary"
                                className="flex-1 sm:flex-none flex items-center justify-center gap-2 bg-[#FF007F]/20 text-[#FF007F] border border-[#FF007F]/50 hover:bg-[#FF007F]/40 transition-all font-bold"
                                onClick={() => handleRunCycle('matin')}
                                disabled={isRunning}
                            >
                                <Play className="h-4 w-4" />
                                {isRunning ? '...' : 'MATIN'}
                            </Button>
                            <Button
                                variant="primary"
                                className="flex-1 sm:flex-none flex items-center justify-center gap-2 bg-[#00E5FF]/20 text-[#00E5FF] border border-[#00E5FF]/50 hover:bg-[#00E5FF]/40 transition-all font-bold"
                                onClick={() => handleRunCycle('soir')}
                                disabled={isRunning}
                            >
                                <Play className="h-4 w-4" />
                                {isRunning ? '...' : 'SOIR'}
                            </Button>
                        </>
                    )}
                </div>
            </header>

            {/* KPI Cards */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4 mb-8">
                <KPI title="Agents Actifs" value={overviewData.activeAgents} icon={Bot} color="text-cyan-400" />
                <KPI title="Vidéos Aujourd'hui" value={overviewData.videosToday} icon={Video} color="text-emerald-400" target="Objectif: 2" />
                <KPI title="Coût IA Aujourd'hui" value={overviewData.aiCostToday} icon={DollarSign} color="text-amber-400" />
                <KPI title="Score Profit Est." value={overviewData.estProfitScore} icon={TrendingUp} color="text-purple-400" />
                <KPI title="Budget Restant" value={overviewData.budgetRemaining} icon={DollarSign} color="text-blue-400" />
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Main Section */}
                <Card className="lg:col-span-2">
                    <h3 className="text-xl font-semibold text-white mb-4 border-b border-gray-700/50 pb-2">Sujets Tendances</h3>
                    <div className="overflow-x-auto custom-scrollbar">
                        <table className="w-full text-left border-collapse min-w-[500px]">
                            <thead>
                                <tr className="text-gray-400 text-sm border-b border-gray-800">
                                    <th className="py-3 px-4 font-medium">Sujet</th>
                                    <th className="py-3 px-4 font-medium text-center">ScoreViral</th>
                                    <th className="py-3 px-4 font-medium text-center">ScoreFinal</th>
                                    <th className="py-3 px-4 font-medium text-right">Statut</th>
                                </tr>
                            </thead>
                            <tbody>
                                {trends.slice(0, 10).map(trend => (
                                    <tr key={trend.id} className="border-b border-gray-800/50 hover:bg-white/5 transition-colors">
                                        <td className="py-3 px-4 font-medium text-gray-200">
                                            {trend.title}
                                            {trend.status === 'posted' && !trend.tiktok_url && (
                                                <div className="text-[9px] text-pink-500 mt-1 flex items-center gap-1">
                                                    <TrendingUp className="w-2 h-2" /> EN ATTENTE DE LIEN
                                                </div>
                                            )}
                                        </td>
                                        <td className="py-3 px-4 text-center text-cyan-400">{trend.viralScore}</td>
                                        <td className="py-3 px-4 text-center font-bold text-white">{trend.finalScore}</td>
                                        <td className="py-3 px-4 text-right">
                                            <div className="flex flex-col items-end gap-1">
                                                <Badge variant={
                                                    trend.status === 'approved' ? 'success' :
                                                        trend.status === 'rejected' ? 'danger' :
                                                            trend.status === 'review' ? 'warning' : 'info'
                                                }>
                                                    {trend.status === 'approved' ? 'approuvé' :
                                                     trend.status === 'rejected' ? 'rejeté' :
                                                     trend.status === 'producing' ? 'en production' :
                                                     trend.status === 'posted' ? 'publié' : trend.status}
                                                </Badge>
                                                {trend.status === 'posted' && !trend.tiktok_url && (
                                                    <button 
                                                        onClick={() => window.location.href='/gallery'} 
                                                        className="text-[9px] font-bold text-pink-500 hover:text-pink-400 border border-pink-500/30 px-2 py-0.5 rounded mt-1 transition-all"
                                                    >
                                                        LIER TIKTOK
                                                    </button>
                                                )}
                                            </div>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </Card>

                {/* Recently Linked Videos Section */}
                <Card className="border border-cyan-900/30">
                    <h3 className="text-xl font-semibold text-white mb-4 border-b border-gray-700/50 pb-2 flex items-center gap-2">
                        <TrendingUp className="text-[#FF007F] h-5 w-5" />
                        Récemment Liés
                    </h3>
                    <div className="space-y-4">
                        {overviewData?.recentLinked?.length > 0 ? overviewData.recentLinked.map(video => (
                            <div key={video.id} className="flex items-center gap-3 p-3 rounded-lg bg-navy-900/50 border border-gray-800 group hover:border-pink-500/30 transition-all">
                                <div className="w-10 h-10 rounded bg-pink-600/20 flex items-center justify-center text-pink-500 font-bold text-xs ring-1 ring-pink-500/20">
                                    TT
                                </div>
                                <div className="flex-1 overflow-hidden">
                                    <div className="text-sm font-medium text-white truncate">{video.title}</div>
                                    <div className="flex items-center gap-2 text-[10px] text-gray-500">
                                        <Eye className="w-3 h-3" /> {video.views} vues • {video.date}
                                    </div>
                                </div>
                                <a href={video.url} target="_blank" rel="noopener noreferrer" className="p-2 rounded-full hover:bg-pink-600/20 text-pink-500 transition-colors">
                                    <Play className="w-4 h-4" />
                                </a>
                            </div>
                        )) : (
                            <div className="text-gray-500 text-sm text-center py-8 italic">
                                Aucune vidéo liée récemment.<br/>Liez-les dans la Galerie pour voir les stats.
                            </div>
                        )}
                    </div>
                </Card>
            </div>
        </div>
    );
};

const KPI = ({ title, value, icon: Icon, color, target }) => (
    <Card className="flex items-center gap-4 relative overflow-hidden group">
        <div className={`p-3 rounded-xl bg-gray-800 border border-gray-700 w-12 h-12 flex justify-center items-center ${color} shadow-lg shadow-black/50 group-hover:scale-110 transition-transform duration-300`}>
            <Icon className="w-6 h-6" />
        </div>
        <div>
            <h4 className="text-gray-400 text-xs uppercase font-semibold tracking-wider">{title}</h4>
            <div className="text-2xl font-bold text-white">{value}</div>
            {target && <div className="text-xs text-gray-500 mt-1">{target}</div>}
        </div>
        <div className="absolute -right-4 -bottom-4 opacity-5 pointer-events-none">
            <Icon className={`w-24 h-24 ${color}`} />
        </div>
    </Card>
);

const AlertItem = ({ type, msg, time }) => {
    const colors = {
        warning: 'border-amber-500/30 text-amber-200 bg-amber-500/10',
        info: 'border-blue-500/30 text-blue-200 bg-blue-500/10',
        danger: 'border-red-500/30 text-red-200 bg-red-500/10 success border-emerald-500/30 text-emerald-200 bg-emerald-500/10'
    };
    const colorClass = colors[type] || 'border-gray-500/30 text-gray-200 bg-gray-500/10';

    return (
        <div className={`p-3 rounded-lg border text-sm flex justify-between items-start gap-3 ${colorClass}`}>
            <span>{msg}</span>
            <span className="text-[10px] opacity-60 mt-0.5">{time}</span>
        </div>
    );
};

export default Overview;
