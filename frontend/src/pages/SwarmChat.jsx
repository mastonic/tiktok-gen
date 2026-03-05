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
    const messagesEndRef = useRef(null);

    const [threads, setThreads] = useState([]);

    useEffect(() => {
        const fetchThreads = async () => {
            try {
                const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:5656';
                const res = await fetch(`${apiUrl}/api/contents`);
                const data = await res.json();

                // Map the pipeline contents to thread format
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
                const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:5656';
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
                const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:5656';
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

        const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:5656';
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
    const threadMessages = messages.filter(m => m.content_id === selectedThread);

    return (
        <div className="flex bg-navy-800/50 rounded-2xl border border-gray-800 h-[calc(100vh-8rem)] overflow-hidden">

            {/* Left Panel: Threads */}
            <div className="w-72 border-r border-gray-800 flex flex-col bg-navy-900/40">
                <div className="p-4 border-b border-gray-800">
                    <h2 className="font-semibold text-white flex items-center gap-2">
                        <Hash className="w-4 h-4 text-cyan-400" />
                        Active Threads
                    </h2>
                </div>
                <div className="flex-1 overflow-y-auto custom-scrollbar p-2 space-y-2">
                    {threads.map(thread => (
                        <button
                            key={thread.id}
                            onClick={() => {
                                setSelectedThread(thread.id);
                            }}
                            className={`w-full text-left p-3 rounded-xl border transition-all ${selectedThread === thread.id
                                ? 'bg-cyan-900/20 border-cyan-500/30'
                                : 'border-transparent hover:bg-gray-800/80 hover:border-gray-700'
                                }`}
                        >
                            <div className="text-sm font-medium text-gray-200 truncate">{thread.title}</div>
                            <div className="flex justify-between items-center mt-2">
                                <span className="text-[10px] text-gray-500 flex items-center gap-1">
                                    <Activity className="w-3 h-3" /> {thread.date} {thread.time}
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
                <div className="p-4 border-b border-gray-800 bg-navy-900/90 z-10 flex justify-between items-center shadow-md">
                    <h2 className="font-semibold text-white flex items-center gap-2">
                        <MessageSquare className="w-4 h-4 text-emerald-400" />
                        Agent Swarm Stream
                    </h2>
                    <Badge variant="cyber">Live Tracking</Badge>
                </div>

                <div className="flex-1 overflow-y-auto custom-scrollbar p-6 space-y-6 z-10">
                    {/* Live Stream Panel overlay */}
                    {liveStreamTexts.length > 0 && (
                        <div className="mb-4 bg-black/60 border border-cyan-900/50 p-4 rounded-xl font-mono text-xs text-cyan-400 overflow-x-auto shadow-[0_0_15px_rgba(6,182,212,0.1)]">
                            <div className="flex items-center gap-2 mb-2 text-white font-sans text-sm">
                                <Activity className="w-4 h-4 text-cyan-400 animate-pulse" /> Live Terminal Log
                            </div>
                            {liveStreamTexts.map((text, i) => (
                                <div key={i} className="opacity-80 leading-relaxed whitespace-pre-wrap">{text}</div>
                            ))}
                        </div>
                    )}

                    {threadMessages.length > 0 ? threadMessages.map(msg => (
                        <div
                            key={msg.id}
                            onClick={() => setSelectedMessage(msg)}
                            className={`flex flex-col gap-1 max-w-2xl cursor-pointer transition-all ${selectedMessage?.id === msg.id ? 'opacity-100 scale-[1.01]' : 'opacity-70 hover:opacity-100'} ${msg.from_agent === 'RiskGuard' ? 'ml-auto items-end' : ''}`}
                        >
                            <div className={`flex items-center gap-2 text-xs font-medium ${msg.from_agent === 'RiskGuard' ? 'text-red-400 flex-row-reverse' : 'text-cyan-400'}`}>
                                <span>{msg.from_agent}</span>
                                <ChevronRight className="w-3 h-3 text-gray-600 mx-1" />
                                <span className="text-gray-400">{msg.to_agent}</span>
                                <span className="text-gray-600 ml-2 font-mono">{msg.timestamp}</span>
                            </div>

                            <div className={`p-4 rounded-2xl shadow-lg border ${msg.type === 'alert' ? 'bg-red-900/20 border-red-500/30 text-rose-100 rounded-tr-sm' :
                                msg.type === 'vote' ? 'bg-emerald-900/20 border-emerald-500/30 text-emerald-100 rounded-tl-sm' :
                                    'bg-navy-700/80 border-gray-600/50 text-gray-200 rounded-tl-sm backdrop-blur-sm'
                                }`}>
                                <div className="flex items-start justify-between gap-4 mb-2">
                                    <Badge variant={msg.type === 'alert' ? 'danger' : msg.type === 'vote' ? 'success' : 'info'} className="uppercase">
                                        {msg.type}
                                    </Badge>
                                    {msg.status === 'pending' && <span className="animate-pulse flex h-2 w-2 rounded-full bg-amber-400"></span>}
                                </div>
                                <p className="text-sm font-medium leading-relaxed">{msg.summary}</p>

                                {/* Expandable JSON Payload */}
                                {Object.keys(msg.payload).length > 0 && (
                                    <div className="mt-3 bg-black/40 rounded border border-gray-700/50 p-2 overflow-x-auto text-xs font-mono text-gray-400">
                                        <pre>{JSON.stringify(msg.payload, null, 2)}</pre>
                                    </div>
                                )}
                            </div>
                        </div>
                    )) : (
                        <div className="text-gray-500 text-center mt-10">No messages found for this thread.</div>
                    )}
                    <div ref={messagesEndRef} />
                </div>
            </div>

            {/* Right Panel: Inspector */}
            <div className="w-80 border-l border-gray-800 bg-navy-900/60 p-6 flex flex-col gap-6">
                <h2 className="font-semibold text-white border-b border-gray-800 pb-2">Inspector</h2>

                {selectedMessage ? (
                    <>
                        <div className="space-y-4">
                            <div>
                                <div className="text-xs text-gray-500 mb-1 uppercase tracking-wider font-semibold">Message ID</div>
                                <div className="font-mono text-sm text-cyan-400">{selectedMessage.id}</div>
                            </div>
                            <div>
                                <div className="text-xs text-gray-500 mb-1 uppercase tracking-wider font-semibold">Cost Estimate</div>
                                <div className="text-lg font-bold text-emerald-400">$0.04 <span className="text-xs font-normal text-gray-500">API tokens</span></div>
                            </div>

                            <div className="pt-4 border-t border-gray-800">
                                <div className="text-xs text-gray-500 mb-3 uppercase tracking-wider font-semibold">Agent Actions</div>
                                <div className="grid grid-cols-2 gap-2">
                                    <Button variant="primary" className="flex items-center justify-center gap-1 !p-2 text-xs">
                                        <CheckCircle className="w-3 h-3" /> Approve
                                    </Button>
                                    <Button variant="danger" className="flex items-center justify-center gap-1 !p-2 text-xs">
                                        <XCircle className="w-3 h-3" /> Reject
                                    </Button>
                                    <Button variant="secondary" className="flex items-center justify-center gap-1 !p-2 text-xs col-span-2">
                                        <RefreshCw className="w-3 h-3" /> Regenerate
                                    </Button>
                                    <Button variant="secondary" className="flex items-center justify-center gap-1 !p-2 text-xs col-span-2 border-cyan-500/30 text-cyan-400 hover:bg-cyan-900/20">
                                        <Play className="w-3 h-3" /> Rerun Step
                                    </Button>
                                </div>
                            </div>
                        </div>
                    </>
                ) : (
                    <div className="text-gray-500 text-sm italic">Select a message to inspect details.</div>
                )}
            </div>

        </div>
    );
};

export default SwarmChat;
