import { API_URL } from '../api';
import React, { useState, useEffect, useRef } from 'react';
import { Card, Badge, Button } from '../components/ui';
import {
    CheckCircle, XCircle, RefreshCw,
    MessageSquare, ChevronRight, Hash, Play, Activity
} from 'lucide-react';

const SwarmChat = () => {
    const [selectedThread, setSelectedThread] = useState('t2');
    const [selectedMessage, setSelectedMessage] = useState(null);
    const [messages, setMessages] = useState([]);
    const [liveStreamTexts, setLiveStreamTexts] = useState([]);
    const [searchQuery, setSearchQuery] = useState('');
    const [filterType, setFilterType] = useState('all');
    const messagesEndRef = useRef(null);

    const [threads, setThreads] = useState([]);

    useEffect(() => {
        const fetchThreads = async () => {
            try {
                const apiUrl = API_URL;
                const res = await fetch(`${apiUrl}/api/contents`);
                const data = await res.json();

                const mappedThreads = data.map(item => ({
                    id: item.id,
                    title: item.title,
                    status: item.column === 'Review' ? 'Script' : item.column,
                    time: item.created_at,
                    date: item.date
                }));

                setThreads(mappedThreads);
                if (mappedThreads.length > 0 && selectedThread === 't2') {
                    setSelectedThread(mappedThreads[0].id);
                }
            } catch (err) {
                console.error("Failed to fetch threads:", err);
            }
        };
        fetchThreads();
    }, []);

    useEffect(() => {
        const fetchMessages = async () => {
            try {
                const apiUrl = API_URL;
                const res = await fetch(`${apiUrl}/api/messages?content_id=${selectedThread}`);
                const data = await res.json();
                setMessages(data);
                if (data.length > 0) setSelectedMessage(data[0]);
            } catch (err) {
                console.error("Failed to fetch messages:", err);
            }
        };
        fetchMessages();
    }, [selectedThread]);

    useEffect(() => {
        const fetchHistory = async () => {
            try {
                const apiUrl = API_URL;
                const res = await fetch(`${apiUrl}/api/logs/history`);
                const data = await res.json();
                if (data.logs) {
                    setLiveStreamTexts(data.logs);
                }
            } catch (err) {
                console.error("Failed to fetch log history:", err);
            }
        };
        fetchHistory();

        const apiUrl = API_URL;
        const eventSource = new EventSource(`${apiUrl}/api/stream`);

        eventSource.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                if (data.log) {
                    setLiveStreamTexts(prev => [...prev, data.log]);
                }
            } catch (e) {
                console.error("Could not parse stream data", e);
            }
        };

        return () => {
            eventSource.close();
        };
    }, []);

    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [liveStreamTexts, messages]);

    const filteredMessages = messages.filter(m => {
        const matchesType = filterType === 'all' || m.type === filterType;
        const matchesSearch = m.summary.toLowerCase().includes(searchQuery.toLowerCase()) ||
            m.from_agent.toLowerCase().includes(searchQuery.toLowerCase());
        return matchesType && matchesSearch;
    });

    return (
        <div className="flex flex-col lg:flex-row bg-navy-800/50 rounded-2xl border border-gray-800 h-[calc(100vh-8rem)] overflow-hidden">

            {/* Left Panel: Threads */}
            <div className="w-full lg:w-72 border-b lg:border-b-0 lg:border-r border-gray-800 flex flex-col bg-navy-900/40">
                <div className="p-4 border-b border-gray-800 flex justify-between items-center">
                    <h2 className="font-semibold text-white flex items-center gap-2">
                        <Hash className="w-4 h-4 text-cyan-400" />
                        Active Threads
                    </h2>
                </div>
                <div className="flex-1 overflow-y-auto custom-scrollbar p-2 space-y-2 max-h-48 lg:max-h-full">
                    {threads.map(thread => (
                        <button
                            key={thread.id}
                            onClick={() => setSelectedThread(thread.id)}
                            className={`w-full text-left p-3 rounded-xl border transition-all ${selectedThread === thread.id
                                ? 'bg-cyan-900/20 border-cyan-500/30'
                                : 'border-transparent hover:bg-gray-800/80 hover:border-gray-700'
                                }`}
                        >
                            <div className="text-sm font-medium text-gray-200 truncate">{thread.title}</div>
                            <div className="flex justify-between items-center mt-2">
                                <span className="text-[10px] text-gray-500 flex items-center gap-1">
                                    <Activity className="w-3 h-3" /> {thread.date}
                                </span>
                                <Badge variant={thread.status === 'Posted' ? 'success' : 'info'} className="text-[10px] px-1.5 py-0">
                                    {thread.status}
                                </Badge>
                            </div>
                        </button>
                    ))}
                </div>
            </div>

            {/* Center Panel: Conversation */}
            <div className="flex-1 flex flex-col relative bg-[url('https://www.transparenttextures.com/patterns/cubes.png')] bg-opacity-5">
                <div className="absolute inset-0 bg-navy-900/80 pointer-events-none z-0"></div>

                {/* Header with Filters */}
                <div className="p-4 border-b border-gray-800 bg-navy-900/90 z-20 flex flex-col sm:flex-row justify-between items-center gap-4 shadow-md backdrop-blur-md">
                    <div className="flex items-center gap-2">
                        <MessageSquare className="w-4 h-4 text-emerald-400" />
                        <h2 className="font-semibold text-white">Agent Swarm Stream</h2>
                    </div>

                    <div className="flex items-center gap-3 w-full sm:w-auto">
                        <select
                            value={filterType}
                            onChange={(e) => setFilterType(e.target.value)}
                            className="bg-navy-800 border border-gray-700 text-gray-300 text-xs rounded-lg px-2 py-1.5 outline-none focus:border-cyan-500 transition-colors"
                        >
                            <option value="all">All Types</option>
                            <option value="info">Info</option>
                            <option value="alert">Alerts</option>
                            <option value="vote">Votes</option>
                        </select>

                        <div className="relative flex-1 sm:w-64">
                            <input
                                type="text"
                                placeholder="Search agents or logs..."
                                value={searchQuery}
                                onChange={(e) => setSearchQuery(e.target.value)}
                                className="w-full bg-navy-800 border border-gray-700 text-gray-300 text-xs rounded-lg pl-3 pr-8 py-1.5 outline-none focus:border-cyan-500 transition-colors"
                            />
                            {searchQuery && (
                                <button
                                    onClick={() => setSearchQuery('')}
                                    className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-500 hover:text-white"
                                >
                                    ✕
                                </button>
                            )}
                        </div>
                    </div>
                </div>

                <div className="flex-1 overflow-y-auto custom-scrollbar p-6 space-y-6 z-10">
                    {/* Live Stream Panel overlay */}
                    {liveStreamTexts.length > 0 && !searchQuery && filterType === 'all' && (
                        <div className="mb-4 bg-black/60 border border-cyan-900/50 p-4 rounded-xl font-mono text-xs text-cyan-400 overflow-x-auto shadow-[0_0_15px_rgba(6,182,212,0.1)]">
                            <div className="flex items-center gap-2 mb-2 text-white font-sans text-sm">
                                <Activity className="w-4 h-4 text-cyan-400 animate-pulse" /> Live Terminal Log
                            </div>
                            {liveStreamTexts.slice(-10).map((text, i) => (
                                <div key={i} className="opacity-80 leading-relaxed whitespace-pre-wrap">{text}</div>
                            ))}
                        </div>
                    )}

                    {filteredMessages.length > 0 ? filteredMessages.map(msg => (
                        <div
                            key={msg.id}
                            onClick={() => setSelectedMessage(msg === selectedMessage ? null : msg)}
                            className={`flex flex-col gap-1 max-w-3xl transition-all ${selectedMessage?.id === msg.id ? 'opacity-100 scale-[1.01]' : 'opacity-85 hover:opacity-100'} ${msg.from_agent === 'RiskGuard' ? 'ml-auto items-end' : ''}`}
                        >
                            <div className={`flex items-center gap-2 text-xs font-medium ${msg.from_agent === 'RiskGuard' ? 'text-red-400 flex-row-reverse' : 'text-cyan-400'}`}>
                                <span>{msg.from_agent}</span>
                                <ChevronRight className="w-3 h-3 text-gray-600 mx-1" />
                                <span className="text-gray-400">{msg.to_agent}</span>
                                <span className="text-gray-600 ml-2 font-mono">{msg.timestamp}</span>
                            </div>

                            <div className={`p-4 rounded-2xl shadow-lg border cursor-pointer transition-colors ${selectedMessage?.id === msg.id ? 'border-cyan-500/50 ring-1 ring-cyan-500/20' : 'border-gray-600/30'} ${msg.type === 'alert' ? 'bg-red-900/20 border-red-500/30 text-rose-100 rounded-tr-sm' :
                                msg.type === 'vote' ? 'bg-emerald-900/20 border-emerald-500/30 text-emerald-100 rounded-tl-sm' :
                                    'bg-navy-700/80 text-gray-200 rounded-tl-sm backdrop-blur-sm'
                                }`}>
                                <div className="flex items-start justify-between gap-4 mb-2">
                                    <Badge variant={msg.type === 'alert' ? 'danger' : msg.type === 'vote' ? 'success' : 'info'} className="uppercase text-[9px] px-1.5 italic">
                                        {msg.type}
                                    </Badge>
                                    {msg.status === 'pending' && <span className="animate-pulse flex h-2 w-2 rounded-full bg-amber-400"></span>}
                                </div>
                                <p className="text-sm font-medium leading-relaxed">{msg.summary}</p>

                                {/* Inspector Details integrated if selected */}
                                {selectedMessage?.id === msg.id && (
                                    <div className="mt-4 pt-4 border-t border-white/10 space-y-3 animate-in fade-in slide-in-from-top-2">
                                        {Object.keys(msg.payload).length > 0 && (
                                            <div className="bg-black/40 rounded border border-gray-700/50 p-3 overflow-x-auto text-[11px] font-mono text-gray-400">
                                                <div className="text-[9px] uppercase font-bold text-gray-500 mb-2">Payload Data</div>
                                                <pre>{JSON.stringify(msg.payload, null, 2)}</pre>
                                            </div>
                                        )}

                                        <div className="flex justify-between items-center bg-navy-900/50 p-2 rounded-lg border border-gray-700">
                                            <div className="text-[10px] text-gray-500 font-mono">ID: {msg.id}</div>
                                            <div className="flex gap-2">
                                                <Button variant="primary" className="!px-2 !py-1 text-[10px] h-7 flex items-center gap-1">
                                                    <CheckCircle className="w-3 h-3" /> Approve
                                                </Button>
                                                <Button variant="danger" className="!px-2 !py-1 text-[10px] h-7 flex items-center gap-1">
                                                    <XCircle className="w-3 h-3" /> Reject
                                                </Button>
                                            </div>
                                        </div>
                                    </div>
                                )}
                            </div>
                        </div>
                    )) : (
                        <div className="text-gray-500 text-center mt-10">No messages matching your filters.</div>
                    )}
                    <div ref={messagesEndRef} />
                </div>
            </div>
        </div>
    );
};

export default SwarmChat;
