import React, { useState, useEffect } from 'react';
import { Badge, Card } from '../components/ui';
import { GripVertical, AlertTriangle } from 'lucide-react';

const Pipeline = () => {
    const [contents, setContents] = useState([]);
    const [selectedItem, setSelectedItem] = useState(null);
    const columns = ['Ideas', 'Script', 'Media', 'Review', 'Scheduled', 'Posted'];

    useEffect(() => {
        const fetchContents = async () => {
            try {
                const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
                const response = await fetch(`${apiUrl}/api/contents`);
                const data = await response.json();
                setContents(data);
            } catch (error) {
                console.error("Failed to fetch contents:", error);
            }
        };
        fetchContents();
        const intervalId = setInterval(fetchContents, 3000);
        return () => clearInterval(intervalId);
    }, []);

    return (
        <div className="h-full flex flex-col">
            <header className="mb-8">
                <h1 className="text-3xl font-bold text-white tracking-tight mb-1">Production Pipeline</h1>
                <p className="text-gray-400">Kanban view of all content in the viral factory.</p>
            </header>

            <div className="flex-1 flex gap-4 overflow-x-auto pb-4 custom-scrollbar">
                {columns.map(col => (
                    <div key={col} className="bg-navy-800/60 rounded-xl border border-gray-800 flex flex-col min-w-[320px] max-w-[320px] h-[calc(100vh-12rem)]">
                        <div className="p-4 border-b border-gray-800 flex justify-between items-center bg-navy-900/50 rounded-t-xl shadow-md">
                            <h3 className="font-semibold text-gray-200">{col}</h3>
                            <Badge variant="cyber" className="px-2">{contents.filter(c => c.column === col).length}</Badge>
                        </div>

                        <div className="flex-1 p-3 overflow-y-auto custom-scrollbar space-y-3">
                            {contents.filter(c => c.column === col).map(content => (
                                <div key={content.id} onClick={() => setSelectedItem(content)} className="glass-card p-4 group cursor-pointer hover:bg-navy-800/80 transition-colors border-l-4 border-l-cyan-500">
                                    <div className="flex justify-between items-start mb-2">
                                        <h4 className="font-medium text-white text-sm leading-tight pr-2">{content.title}</h4>
                                        <GripVertical className="w-4 h-4 text-gray-600 opacity-0 group-hover:opacity-100 transition-opacity" />
                                    </div>

                                    <div className="grid grid-cols-3 gap-2 mb-3">
                                        <div className="bg-navy-900/50 rounded p-1.5 text-center flex flex-col items-center border border-gray-700/50">
                                            <span className="text-[10px] text-gray-500 font-semibold mb-0.5">VIRAL</span>
                                            <span className="text-sm font-bold text-cyan-400">{content.viralScore}</span>
                                        </div>
                                        <div className="bg-navy-900/50 rounded p-1.5 text-center flex flex-col items-center border border-gray-700/50">
                                            <span className="text-[10px] text-gray-500 font-semibold mb-0.5">MONEY</span>
                                            <span className="text-sm font-bold text-emerald-400">{content.moneyScore}</span>
                                        </div>
                                        <div className="bg-navy-900/50 rounded p-1.5 text-center flex flex-col items-center border border-cyan-900/30">
                                            <span className="text-[10px] text-gray-500 font-semibold mb-0.5">FINAL</span>
                                            <span className="text-sm font-bold text-white shadow-sm">{content.finalScore}</span>
                                        </div>
                                    </div>

                                    <div className="flex justify-between items-center mt-2 border-t border-gray-700/50 pt-2">
                                        <div className="text-[10px] text-gray-400 bg-gray-800 px-2 py-0.5 rounded flex items-center gap-1">
                                            {content.assignedAgent}
                                        </div>

                                        <div className="flex items-center gap-2">
                                            {content.riskScore > 50 && (
                                                <AlertTriangle className="w-3.5 h-3.5 text-amber-500" />
                                            )}
                                            <span className="text-xs text-gray-500 font-mono">${content.costEstimate.toFixed(2)}</span>
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
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
                            <div>
                                <h3 className="font-semibold text-cyan-400 mb-2 uppercase text-xs tracking-wider">Final Script</h3>
                                <p className="text-gray-300 bg-navy-800/50 p-4 rounded-lg border border-gray-800 whitespace-pre-wrap leading-relaxed font-large">
                                    {selectedItem.script || "No script available. Wait for step to finish or check raw output."}
                                </p>
                            </div>
                            {selectedItem.keywords && (
                                <div>
                                    <h3 className="font-semibold text-cyan-400 mb-2 uppercase text-xs tracking-wider">Keywords</h3>
                                    <div className="flex flex-wrap gap-2">
                                        {selectedItem.keywords.split(',').map((kw, i) => (
                                            <Badge key={i} variant="outline" className="text-gray-300 border-gray-700">{kw.trim()}</Badge>
                                        ))}
                                    </div>
                                </div>
                            )}
                            <div className="grid grid-cols-3 gap-4 pt-4 border-t border-gray-800">
                                <div className="text-center">
                                    <span className="block text-xs text-gray-400">VIRAL SCORE</span>
                                    <span className="font-bold text-cyan-400 text-xl">{selectedItem.viralScore}</span>
                                </div>
                                <div className="text-center">
                                    <span className="block text-xs text-gray-400">MONEY SCORE</span>
                                    <span className="font-bold text-emerald-400 text-xl">{selectedItem.moneyScore}</span>
                                </div>
                                <div className="text-center">
                                    <span className="block text-xs text-gray-400">FINAL SCORE</span>
                                    <span className="font-bold text-white text-xl">{selectedItem.finalScore}</span>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default Pipeline;
