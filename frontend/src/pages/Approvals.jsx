import { API_URL } from '../api';
import React, { useState, useEffect } from 'react';
import { Card, Badge, Button } from '../components/ui';
import { Check, X, RefreshCw, Eye } from 'lucide-react';

const Approvals = () => {
    const [activeTab, setActiveTab] = useState('all');
    const [approvals, setApprovals] = useState([]);
    const [selectedItem, setSelectedItem] = useState(null);

    const fetchApprovals = async () => {
        try {
            const apiUrl = API_URL;
            const response = await fetch(`${apiUrl}/api/approvals`);
            const data = await response.json();
            setApprovals(data);
        } catch (error) {
            console.error("Failed to fetch approvals:", error);
        }
    };

    useEffect(() => {
        const intervalId = setInterval(async () => {
            try {
                const apiUrl = API_URL;
                const response = await fetch(`${apiUrl}/api/approvals`);
                const data = await response.json();

                setApprovals(prev => {
                    // Update selectedItem if it exists in the new data
                    if (selectedItem) {
                        const updated = data.find(item => item.id === selectedItem.id && item.type === selectedItem.type);
                        if (updated) setSelectedItem(updated);
                    }
                    return data;
                });
            } catch (error) {
                console.error("Failed to fetch approvals:", error);
            }
        }, 3000);

        fetchApprovals();
        return () => clearInterval(intervalId);
    }, [selectedItem]);

    const handleApprove = async (id) => {
        try {
            const apiUrl = API_URL;
            await fetch(`${apiUrl}/api/approvals/${id}/approve`, { method: 'POST' });
            fetchApprovals(); // Refresh list immediately
        } catch (error) {
            console.error("Failed to approve item:", error);
        }
    };

    const handleReject = async (id) => {
        try {
            const apiUrl = API_URL;
            await fetch(`${apiUrl}/api/approvals/${id}/reject`, { method: 'POST' });
            fetchApprovals(); // Refresh list immediately
        } catch (error) {
            console.error("Failed to reject item:", error);
        }
    };

    return (
        <div className="space-y-6">
            <header className="mb-8">
                <h1 className="text-3xl font-bold text-white tracking-tight mb-1">File d'Approbation</h1>
                <p className="text-gray-400">Examinez le contenu généré par l'Essaim avant progression.</p>
            </header>

            <div className="flex gap-4 mb-6 border-b border-gray-800 pb-4 overflow-x-auto custom-scrollbar whitespace-nowrap">
                <button
                    onClick={() => setActiveTab('all')}
                    className={`px-4 py-2 rounded-lg font-medium transition-colors ${activeTab === 'all' ? 'bg-cyan-900/40 text-cyan-400 border border-cyan-500/30' : 'text-gray-400 hover:text-white'}`}
                >
                    Tous en attente
                </button>
                <button
                    onClick={() => setActiveTab('Topic')}
                    className={`px-4 py-2 rounded-lg font-medium transition-colors ${activeTab === 'Topic' ? 'bg-cyan-900/40 text-cyan-400 border border-cyan-500/30' : 'text-gray-400 hover:text-white'}`}
                >
                    Sujets
                </button>
                <button
                    onClick={() => setActiveTab('Script')}
                    className={`px-4 py-2 rounded-lg font-medium transition-colors ${activeTab === 'Script' ? 'bg-cyan-900/40 text-cyan-400 border border-cyan-500/30' : 'text-gray-400 hover:text-white'}`}
                >
                    Scripts
                </button>
                <button
                    onClick={() => setActiveTab('Video')}
                    className={`px-4 py-2 rounded-lg font-medium transition-colors ${activeTab === 'Video' ? 'bg-cyan-900/40 text-cyan-400 border border-cyan-500/30' : 'text-gray-400 hover:text-white'}`}
                >
                    Vidéos
                </button>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
                {approvals.filter(a => activeTab === 'all' || a.type === activeTab).map(item => (
                    <Card key={item.id} className="flex flex-col h-full border-t-4 border-t-cyan-500 relative">
                        <div className="absolute top-4 right-4 text-xs font-mono text-gray-500 bg-gray-900 px-2 py-1 rounded">
                            {item.status === 'review' ? 'en examen' : item.status}
                        </div>

                        <div className="flex items-center gap-2 mb-4">
                            <Badge variant="warning" className="uppercase">
                                {item.type === 'Topic' ? 'SUJET' : item.type === 'Script' ? 'SCRIPT' : 'VIDÉO'}
                            </Badge>
                            <h3 className="font-semibold text-white truncate pr-16">{item.title}</h3>
                        </div>

                        <div className="bg-navy-900/60 rounded-xl p-4 mb-4 border border-gray-800 flex-1">
                            <p className="text-sm text-gray-400 mb-2 line-clamp-2">{item.context}</p>
                            <p className="text-sm font-semibold text-cyan-100 italic">"Q: {item.question}"</p>
                        </div>

                        <div className="grid grid-cols-2 gap-2 mt-auto">
                            <Button variant="danger" onClick={() => handleReject(item.id)} className="flex justify-center items-center gap-1 group whitespace-nowrap">
                                <X className="w-4 h-4 group-hover:scale-110 transition-transform" />
                                <span className="hidden sm:inline text-xs">Rejeter</span>
                            </Button>
                            <Button
                                variant="primary"
                                onClick={() => handleApprove(item.id)}
                                className="flex justify-center items-center gap-1 group border-emerald-500/30 text-emerald-400 hover:bg-emerald-900/20 bg-emerald-900/10 whitespace-nowrap"
                            >
                                <Check className="w-4 h-4 group-hover:scale-110 transition-transform" />
                                <span className="hidden sm:inline text-xs">{item.type === 'Script' ? 'Approuver' : 'Répondre'}</span>
                            </Button>
                        </div>

                        <Button
                            variant="secondary"
                            onClick={() => setSelectedItem(item)}
                            className="w-full mt-2 flex justify-center items-center gap-2 opacity-70 hover:opacity-100"
                        >
                            <Eye className="w-4 h-4" /> Voir tous les détails
                        </Button>
                    </Card>
                ))}
            </div>

            {selectedItem && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4">
                    <div className="bg-navy-900 border border-cyan-900/50 rounded-xl p-6 max-w-2xl w-full shadow-2xl relative max-h-[90vh] flex flex-col">
                        <button
                            onClick={() => setSelectedItem(null)}
                            className="absolute top-4 right-4 text-gray-400 hover:text-white"
                        >
                            ✕
                        </button>
                        <h2 className="text-2xl font-bold text-white mb-4">{selectedItem.title}</h2>
                        <div className="flex-1 overflow-y-auto custom-scrollbar pr-2 mb-4 space-y-4">
                            <div className="bg-navy-800/50 p-4 rounded-lg border border-gray-800">
                                <h3 className="text-sm font-semibold text-cyan-400 mb-1">Contexte</h3>
                                <p className="text-gray-300 text-sm mb-4">{selectedItem.context}</p>

                                <h3 className="text-sm font-semibold text-emerald-400 mb-1">Question / Prompt</h3>
                                <p className="text-white font-medium">{selectedItem.question}</p>
                            </div>

                            {selectedItem.script && (
                                <div>
                                    <h3 className="font-semibold text-cyan-400 mb-2 uppercase text-xs tracking-wider">Script Généré</h3>
                                    <p className="text-gray-300 bg-navy-800/50 p-4 rounded-lg border border-gray-800 whitespace-pre-wrap leading-relaxed font-large">
                                        {selectedItem.script}
                                    </p>
                                </div>
                            )}

                            {selectedItem.keywords && (
                                <div>
                                    <h3 className="font-semibold text-cyan-400 mb-2 uppercase text-xs tracking-wider">Mots-clés</h3>
                                    <div className="flex flex-wrap gap-2">
                                        {selectedItem.keywords.split(',').map((kw, i) => (
                                            <Badge key={i} variant="outline" className="text-gray-300 border-gray-700">{kw.trim()}</Badge>
                                        ))}
                                    </div>
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default Approvals;
