import { API_URL } from '../api';
import React, { useState, useEffect } from 'react';
import { Card, Button, Badge } from '../components/ui';
import {
    LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer
} from 'recharts';
import { TrendingUp, Users, Clock, Eye, MessageCircle, AlertCircle, Sparkles, Video } from 'lucide-react';

const Analytics = () => {
    const [runMetrics, setRunMetrics] = useState([]);

    const handleApplyRecommendation = async (recId) => {
        try {
            const apiUrl = API_URL;
            const response = await fetch(`${apiUrl}/api/recs/${recId}/apply`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });
            const data = await response.json();
            if (data.status === 'success') {
                alert(`✅ Succès : ${data.message}`);
                // Refresh metrics to reflect potential changes (like budget)
                fetchMetrics();
            } else {
                alert(`❌ Erreur : ${data.message}`);
            }
        } catch (error) {
            console.error("Failed to apply recommendation:", error);
            alert("Erreur de connexion au serveur.");
        }
    };

    const fetchMetrics = async () => {
        try {
            const apiUrl = API_URL;
            const response = await fetch(`${apiUrl}/api/metrics`);
            const data = await response.json();
            setRunMetrics(data);
        } catch (error) {
            console.error("Failed to fetch metrics:", error);
        }
    };

    useEffect(() => {
        fetchMetrics();
    }, []);
    return (
        <div className="space-y-6">
            <header className="mb-8">
                <h1 className="text-3xl font-bold text-white tracking-tight mb-1">Intelligence de Performance</h1>
                <p className="text-gray-400">Métriques TikTok, analyse de croissance et recommandations de l'IA.</p>
            </header>

            {/* Top row of metrics */}
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
                <MetricCard title="Vues Totales (Semaine)" value={runMetrics?.kpis?.totalViews || "0"} trend="-" icon={Eye} color="text-cyan-400" />
                <MetricCard title="Rétention Moyenne %" value={runMetrics?.kpis?.avgRetention || "0%"} trend="-" icon={Clock} color="text-emerald-400" />
                <MetricCard title="Taux d'Engagement" value={runMetrics?.kpis?.engagement || "0%"} trend="-" icon={MessageCircle} color="text-amber-400" />
                <MetricCard title="Croissance Abonnés" value={runMetrics?.kpis?.followers || "0"} trend="-" icon={Users} color="text-purple-400" />
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Chart Section */}
                <Card className="lg:col-span-2 relative">
                    <h3 className="text-xl font-semibold text-white mb-6 flex items-center gap-2">
                        <TrendingUp className="w-5 h-5 text-cyan-400" />
                        Performance par Créneau Horaire
                    </h3>

                    <div className="h-80 w-full rounded-xl overflow-hidden pt-4 pb-2 bg-navy-900/40">
                        <ResponsiveContainer width="100%" height="100%">
                            {runMetrics?.chartData?.length > 0 ? (
                                <LineChart data={runMetrics?.chartData} margin={{ top: 5, right: 30, left: -20, bottom: 5 }}>
                                    <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" vertical={false} />
                                    <XAxis dataKey="name" stroke="#6b7280" tick={{ fill: '#9ca3af', fontSize: 12 }} axisLine={false} tickLine={false} />
                                    <YAxis stroke="#6b7280" tick={{ fill: '#9ca3af', fontSize: 12 }} axisLine={false} tickLine={false} />
                                    <Tooltip
                                        contentStyle={{ backgroundColor: '#111827', borderColor: '#374151', borderRadius: '8px', color: '#f3f4f6' }}
                                        itemStyle={{ color: '#f3f4f6' }}
                                    />
                                    <Legend iconType="circle" wrapperStyle={{ paddingTop: '20px' }} />
                                    <Line type="monotone" dataKey="morning" name="Run Matin" stroke="#0ea5e9" strokeWidth={3} dot={{ r: 4, strokeWidth: 2 }} activeDot={{ r: 6 }} />
                                    <Line type="monotone" dataKey="evening" name="Run Soir" stroke="#8b5cf6" strokeWidth={3} dot={{ r: 4, strokeWidth: 2 }} activeDot={{ r: 6 }} />
                                </LineChart>
                            ) : (
                                <div className="h-full flex items-center justify-center text-gray-500 italic">Aucune donnée d'exécution disponible pour le moment.</div>
                            )}
                        </ResponsiveContainer>
                    </div>
                </Card>

                {/* Recommendations Box */}
                <Card className="flex flex-col border border-emerald-500/30 shadow-[0_0_30px_rgba(16,185,129,0.05)] h-full relative overflow-hidden">
                    <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-emerald-400 to-cyan-400"></div>

                    <h3 className="text-xl font-semibold text-white mb-6 flex items-center gap-2">
                        <Sparkles className="w-5 h-5 text-emerald-400" />
                        Conseils GrowthAnalyst
                    </h3>

                    <div className="space-y-4 flex-1">
                        {runMetrics?.recommendations?.length > 0 ? (
                            runMetrics.recommendations.map(rec => (
                                <div
                                    key={rec.id}
                                    className={`p-4 rounded-xl border relative transition-all hover:scale-[1.02] ${rec.type === 'scale'
                                            ? 'bg-emerald-900/10 border-emerald-500/20'
                                            : 'bg-navy-800 border-gray-700'
                                        }`}
                                >
                                    {rec.type === 'scale' && <div className="absolute top-0 left-0 w-full h-1 bg-emerald-500/50 rounded-t-xl"></div>}

                                    <div className={`text-sm font-semibold mb-1 flex items-center gap-2 ${rec.type === 'scale' ? 'text-emerald-400' : 'text-gray-200'
                                        }`}>
                                        {rec.type !== 'scale' && <AlertCircle className="w-4 h-4 text-amber-500" />}
                                        {rec.title}
                                    </div>
                                    <p className={`text-sm ${rec.type === 'scale' ? 'text-gray-300' : 'text-gray-400'}`}>
                                        {rec.description}
                                    </p>
                                    <Button
                                        variant={rec.type === 'scale' ? 'primary' : 'outline'}
                                        onClick={() => handleApplyRecommendation(rec.id)}
                                        className={`mt-3 text-[10px] uppercase tracking-wider font-bold !py-2 w-full ${rec.type === 'scale'
                                                ? 'bg-emerald-600 hover:bg-emerald-500 border-emerald-500 shadow-lg shadow-emerald-900/20'
                                                : 'border-gray-700 text-gray-400 hover:text-white'
                                            }`}
                                    >
                                        {rec.action_label}
                                    </Button>
                                </div>
                            ))
                        ) : (
                            <div className="h-40 flex flex-col items-center justify-center text-center px-4">
                                <Sparkles className="w-8 h-8 text-gray-700 mb-2 opacity-20" />
                                <p className="text-gray-500 text-sm italic">En attente des conseils stratégiques des agents...</p>
                            </div>
                        )}
                    </div>
                </Card>
            </div>

            {/* Live Video Performance Table */}
            <Card className="mt-8 overflow-hidden">
                <div className="p-6 border-b border-gray-800 flex justify-between items-center">
                    <h3 className="text-xl font-semibold text-white flex items-center gap-2">
                        <Video className="w-5 h-5 text-pink-500" />
                        Analyses des Vidéos en Direct
                    </h3>
                    <Badge variant="cyber" className="text-gray-400 border-gray-700">Suivi Temps Réel</Badge>
                </div>
                <div className="overflow-x-auto">
                    <table className="w-full text-left border-collapse">
                        <thead>
                            <tr className="text-gray-500 text-[10px] uppercase tracking-widest border-b border-gray-800">
                                <th className="py-4 px-6 font-bold">Titre de la Vidéo</th>
                                <th className="py-4 px-6 font-bold text-center">Vues</th>
                                <th className="py-4 px-6 font-bold text-center">J'aime</th>
                                <th className="py-4 px-6 font-bold text-center">Rétention</th>
                                <th className="py-4 px-6 font-bold text-right">Lien TikTok</th>
                            </tr>
                        </thead>
                        <tbody>
                            {runMetrics?.recentVideos?.length > 0 ? (
                                runMetrics.recentVideos.map((video) => (
                                    <tr key={video.id} className="border-b border-gray-800/50 hover:bg-white/5 transition-colors group">
                                        <td className="py-4 px-6">
                                            <div className="font-medium text-gray-200 group-hover:text-cyan-400 transition-colors">{video.title}</div>
                                            <div className="text-[10px] text-gray-500 font-mono mt-1">ID: {video.id}</div>
                                        </td>
                                        <td className="py-4 px-6 text-center font-bold text-white text-lg">{video.views}</td>
                                        <td className="py-4 px-6 text-center text-emerald-400 font-semibold">{video.likes}</td>
                                        <td className="py-4 px-6 text-center">
                                            <div className="inline-flex items-center gap-2">
                                                <div className="w-16 h-1.5 bg-gray-800 rounded-full overflow-hidden">
                                                    <div
                                                        className="h-full bg-cyan-500 rounded-full"
                                                        style={{ width: `${video.retention}%` }}
                                                    ></div>
                                                </div>
                                                <span className="text-xs font-mono text-gray-400">{video.retention}%</span>
                                            </div>
                                        </td>
                                        <td className="py-4 px-6 text-right">
                                            <a
                                                href={video.url}
                                                target="_blank"
                                                rel="noopener noreferrer"
                                                className="inline-flex items-center gap-1 text-pink-500 hover:text-pink-400 text-xs font-bold transition-colors"
                                            >
                                                OUVRIR <TrendingUp className="w-3 h-3" />
                                            </a>
                                        </td>
                                    </tr>
                                ))
                            ) : (
                                <tr>
                                    <td colSpan="5" className="py-12 text-center text-gray-500 italic bg-navy-900/20">
                                        Aucune vidéo liée pour le moment. Liez-les dans la Galerie.
                                    </td>
                                </tr>
                            )}
                        </tbody>
                    </table>
                </div>
            </Card>
        </div>
    );
};

const MetricCard = ({ title, value, trend, icon: Icon, color }) => (
    <Card className="hover:border-gray-600 transition-colors">
        <div className="flex justify-between items-start mb-2">
            <h4 className="text-xs font-semibold text-gray-400 uppercase tracking-wider">{title}</h4>
            <div className={`p-2 rounded-lg bg-navy-900/80 ${color} shadow-inner`}>
                <Icon className="w-4 h-4" />
            </div>
        </div>
        <div className="text-3xl font-bold text-white mb-2">{value}</div>
        <div className={`text-xs font-medium flex items-center gap-1 ${trend.startsWith('+') ? 'text-emerald-400' : trend.startsWith('-') ? 'text-red-400' : 'text-gray-500'}`}>
            {trend} vs semaine dernière
        </div>
    </Card>
);

export default Analytics;
