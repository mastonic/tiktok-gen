import { API_URL } from '../api';
import React, { useState, useEffect } from 'react';
import { Card, Button } from '../components/ui';
import {
    LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer
} from 'recharts';
import { TrendingUp, Users, Clock, Eye, MessageCircle, AlertCircle, Sparkles } from 'lucide-react';

const Analytics = () => {
    const [runMetrics, setRunMetrics] = useState([]);

    useEffect(() => {
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
        fetchMetrics();
    }, []);
    return (
        <div className="space-y-6">
            <header className="mb-8">
                <h1 className="text-3xl font-bold text-white tracking-tight mb-1">Performance Intelligence</h1>
                <p className="text-gray-400">TikTok metrics, growth analysis, and AI-driven recommendations.</p>
            </header>

            {/* Top row of metrics */}
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
                <MetricCard title="Total Views (Week)" value={runMetrics?.kpis?.totalViews || "0"} trend="-" icon={Eye} color="text-cyan-400" />
                <MetricCard title="Avg Retention %" value={runMetrics?.kpis?.avgRetention || "0%"} trend="-" icon={Clock} color="text-emerald-400" />
                <MetricCard title="Engagement Rate" value={runMetrics?.kpis?.engagement || "0%"} trend="-" icon={MessageCircle} color="text-amber-400" />
                <MetricCard title="Follower Growth" value={runMetrics?.kpis?.followers || "0"} trend="-" icon={Users} color="text-purple-400" />
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Chart Section */}
                <Card className="lg:col-span-2 relative">
                    <h3 className="text-xl font-semibold text-white mb-6 flex items-center gap-2">
                        <TrendingUp className="w-5 h-5 text-cyan-400" />
                        Performance per Time Slot
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
                                    <Line type="monotone" dataKey="morning" name="Morning Run" stroke="#0ea5e9" strokeWidth={3} dot={{ r: 4, strokeWidth: 2 }} activeDot={{ r: 6 }} />
                                    <Line type="monotone" dataKey="evening" name="Evening Run" stroke="#8b5cf6" strokeWidth={3} dot={{ r: 4, strokeWidth: 2 }} activeDot={{ r: 6 }} />
                                </LineChart>
                            ) : (
                                <div className="h-full flex items-center justify-center text-gray-500 italic">No execution data available yet.</div>
                            )}
                        </ResponsiveContainer>
                    </div>
                </Card>

                {/* Recommendations Box */}
                <Card className="flex flex-col border border-emerald-500/30 shadow-[0_0_30px_rgba(16,185,129,0.05)] h-full relative overflow-hidden">
                    <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-emerald-400 to-cyan-400"></div>

                    <h3 className="text-xl font-semibold text-white mb-6 flex items-center gap-2">
                        <Sparkles className="w-5 h-5 text-emerald-400" />
                        GrowthAnalyst Recommendations
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
                                <p className="text-gray-500 text-sm italic">Waiting for agents to generate strategic growth insights...</p>
                            </div>
                        )}
                    </div>
                </Card>
            </div>
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
            {trend} vs last week
        </div>
    </Card>
);

export default Analytics;
