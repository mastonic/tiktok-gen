import React, { useState, useEffect } from 'react';
import { AlertTriangle, Send } from 'lucide-react';
import { Button } from './ui';

const HumanInTheLoop = () => {
    const [pendingQuestion, setPendingQuestion] = useState(null);
    const [answer, setAnswer] = useState('');
    const [isSubmitting, setIsSubmitting] = useState(false);

    useEffect(() => {
        // Poll for pending questions every 3 seconds
        const pollQuestions = async () => {
            try {
                const res = await fetch('http://localhost:8000/api/pending-questions');
                const data = await res.json();
                if (data && data.length > 0) {
                    setPendingQuestion(data[0]); // Handle the first pending question
                } else {
                    setPendingQuestion(null);
                }
            } catch (err) {
                console.error("Failed to poll pending questions:", err);
            }
        };

        const interval = setInterval(pollQuestions, 3000);
        return () => clearInterval(interval);
    }, []);

    const handleSubmit = async () => {
        if (!answer.trim() || !pendingQuestion) return;
        setIsSubmitting(true);
        try {
            await fetch('http://localhost:8000/api/answer-question', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    question_id: pendingQuestion.id,
                    answer: answer
                })
            });
            setPendingQuestion(null);
            setAnswer('');
        } catch (err) {
            console.error("Failed to submit answer:", err);
        } finally {
            setIsSubmitting(false);
        }
    };

    if (!pendingQuestion) return null;

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4">
            <div className="bg-red-950/40 border-2 border-red-500/50 rounded-2xl p-6 max-w-2xl w-full shadow-[0_0_50px_rgba(239,68,68,0.2)] animate-in fade-in zoom-in duration-300">
                <div className="flex items-center gap-3 text-red-400 mb-4">
                    <AlertTriangle className="w-8 h-8 animate-pulse" />
                    <h2 className="text-2xl font-bold uppercase tracking-widest">System Paused</h2>
                </div>

                <div className="mb-6 space-y-4">
                    <div className="bg-black/40 p-4 rounded-lg border border-red-900/50">
                        <div className="text-xs text-red-500/70 uppercase font-mono mb-1">Agent Blocked</div>
                        <div className="font-semibold text-white">{pendingQuestion.agent_name}</div>
                    </div>

                    <div className="bg-black/40 p-4 rounded-lg border border-red-900/50">
                        <div className="text-xs text-red-500/70 uppercase font-mono mb-1">Context</div>
                        <div className="text-sm text-gray-300 italic">"{pendingQuestion.context}"</div>
                    </div>

                    <div className="bg-red-900/20 p-4 rounded-lg border border-red-500/30">
                        <div className="text-xs text-red-400 uppercase font-bold mb-2">Question from AI</div>
                        <div className="text-lg text-white font-medium">{pendingQuestion.question}</div>
                    </div>
                </div>

                <div className="space-y-3">
                    <textarea
                        value={answer}
                        onChange={(e) => setAnswer(e.target.value)}
                        placeholder="Provide your answer or instructions here to resume production..."
                        className="w-full bg-black/60 border border-red-500/30 rounded-xl p-4 text-white placeholder-gray-500 focus:outline-none focus:border-red-400 focus:ring-1 focus:ring-red-400 min-h-[100px] resize-none"
                    />

                    <div className="flex justify-end gap-3">
                        <Button
                            variant="danger"
                            className="bg-red-600 hover:bg-red-500 text-white font-bold py-3 px-6 flex items-center gap-2"
                            onClick={handleSubmit}
                            disabled={isSubmitting || !answer.trim()}
                        >
                            {isSubmitting ? 'Resuming...' : 'Submit & Resume'} <Send className="w-4 h-4 ml-1" />
                        </Button>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default HumanInTheLoop;
