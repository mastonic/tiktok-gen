import React, { useState, useEffect } from 'react';
import { Image, Download, Copy, PlayCircle, Loader2, Film, Wand2, Eye, Clock, Calendar } from 'lucide-react';
import { Player } from '@remotion/player';
import { MyComposition } from '../components/remotion/Composition';
import { Badge } from '../components/ui';

const Studio = () => {
    const [scripts, setScripts] = useState([]);
    const [selectedScript, setSelectedScript] = useState(null);
    const [isGenerating, setIsGenerating] = useState(false);
    const [generatedImages, setGeneratedImages] = useState([]);
    const [showPlayer, setShowPlayer] = useState(false);
    const [playerProps, setPlayerProps] = useState(null);
    const [videoProgress, setVideoProgress] = useState(null);

    useEffect(() => {
        fetchScripts();
    }, []);

    const fetchScripts = async () => {
        try {
            const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
            const response = await fetch(`${apiUrl}/api/contents`);
            const data = await response.json();
            // Filter scripts that actually have image prompts
            const validScripts = data.filter(s => s.imagePrompts && s.imagePrompts.length > 0);

            // Sort by date (newest first)
            validScripts.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));

            setScripts(validScripts);
            if (validScripts.length > 0 && !selectedScript) {
                setSelectedScript(validScripts[0]);
            }
        } catch (error) {
            console.error("Error fetching scripts:", error);
        }
    };

    const handleGenerateImages = async () => {
        if (!selectedScript) return;
        setIsGenerating(true);
        try {
            const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
            const response = await fetch(`${apiUrl}/api/flux/generate`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    prompts: selectedScript.imagePrompts,
                    job_id: selectedScript.id,
                }),
            });
            const data = await response.json();
            if (data.status === 'success') {
                setGeneratedImages(data.images);
            }
        } catch (error) {
            console.error("Error generating images:", error);
        } finally {
            setIsGenerating(false);
        }
    };

    const handleCopyVeoPrompt = () => {
        const veoPrompt = `Animate this futuristic interface with glowing data flows, 4k, cinematic movement`;
        navigator.clipboard.writeText(veoPrompt);
        alert("Veo animation prompt copied to clipboard!");
    };

    const handleDownloadZip = () => {
        // In a real application, you'd use a library like jszip to download multiple files
        // Here we simulate the process
        if (generatedImages.length === 0) return;
        alert("Downloading zip file (simulated)...");
    };

    const handleImageToVideo = async () => {
        if (!selectedScript) return;
        try {
            setVideoProgress({ total: 100, completed: 0, status: 'Démarrage...' });
            const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
            const response = await fetch(`${apiUrl}/api/workflows/image-to-video`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ script_id: selectedScript.id })
            });
            const data = await response.json();

            const interval = setInterval(async () => {
                try {
                    const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
                    const res = await fetch(`${apiUrl}/api/workflows/progress/${selectedScript.id}`);
                    if (!res.ok) return;
                    const progressData = await res.json();

                    if (progressData.status === 'not_found' || progressData.status === 'error') {
                        clearInterval(interval);
                        setVideoProgress(null);
                        return;
                    }

                    setVideoProgress(progressData);

                    if (progressData.status === 'completed') {
                        clearInterval(interval);
                        setTimeout(() => setVideoProgress(null), 4000);
                        // Using a small timeout so the bar stays full before alert
                        setTimeout(() => alert("Génération de clips vidéo terminée !"), 500);
                    }
                } catch (e) { }
            }, 2500);

        } catch (error) {
            console.error("Error triggering image-to-video workflow:", error);
            alert("Erreur lors du lancement du workflow Image-to-Video");
            setVideoProgress(null);
        }
    };

    const handleAssemblageViral = async () => {
        if (!selectedScript) return;
        try {
            const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
            const response = await fetch(`${apiUrl}/api/workflows/assemblage-viral`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ script_id: selectedScript.id })
            });
            const data = await response.json();
            alert(data.message);
            if (data.status === 'success') {
                const videoClips = data.clips && data.clips.length > 0
                    ? data.clips.map(clip => `${apiUrl}${clip}`)
                    : generatedImages.map(img => `${apiUrl}${img}`);

                setPlayerProps({
                    clips: videoClips.length > 0 ? videoClips : [
                        "https://sample-videos.com/video321/mp4/720/big_buck_bunny_720p_5mb.mp4"
                    ],
                    audioUrl: data.audioUrl ? `${apiUrl}${data.audioUrl}` : "",
                    subtitles: data.subtitles || [
                        { text: "VOYEZ", start: 0, end: 15 },
                        { text: "LE", start: 15, end: 30 },
                        { text: "RÉSULTAT !", start: 30, end: 60 },
                    ]
                });
                setShowPlayer(true);
            }
        } catch (error) {
            console.error("Error triggering assemblage-viral workflow:", error);
            alert("Erreur lors du lancement du workflow Assemblage Viral");
        }
    };

    const handlePublish = async () => {
        if (!selectedScript) return;
        try {
            alert("Rendu de la vidéo finale en cours via FFmpeg. Cela peut prendre quelques secondes...");
            const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
            const response = await fetch(`${apiUrl}/api/workflows/publish`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ script_id: selectedScript.id })
            });
            const data = await response.json();
            alert(data.message);
            if (data.status === 'success' && data.videoUrl) {
                window.open(`${apiUrl}${data.videoUrl}`, '_blank');
            }
        } catch (error) {
            console.error("Error publishing:", error);
            alert("Erreur lors de la publication");
        }
    };

    return (
        <div className="space-y-6">
            <div className="flex justify-between items-center mb-6">
                <div>
                    <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
                        <Image className="h-6 w-6 text-pink-500" />
                        Production Studio
                    </h1>
                    <p className="text-gray-400 mt-1">Générer les images FLUX.1 et exporter pour Google Veo</p>
                </div>
                <button
                    onClick={fetchScripts}
                    className="p-2 bg-navy-800 border border-gray-700 rounded-lg text-gray-400 hover:text-white hover:border-gray-500 transition-all"
                    title="Rafraîchir les scripts"
                >
                    <RefreshCw className="h-5 w-5" />
                </button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                {/* Script Selection Sidebar */}
                <div className="md:col-span-1 space-y-4">
                    <h3 className="text-lg font-medium text-white mb-2">Scripts Prêts</h3>
                    <div className="space-y-2 max-h-[70vh] overflow-y-auto custom-scrollbar pr-2">
                        {scripts.map(script => (
                            <div
                                key={script.id}
                                onClick={() => { setSelectedScript(script); setGeneratedImages([]); }}
                                className={`p-4 rounded-xl cursor-pointer transition-all ${selectedScript?.id === script.id ? 'bg-navy-700 border border-pink-500/50 shadow-[0_0_10px_rgba(236,72,153,0.2)]' : 'bg-navy-800 border border-gray-700 hover:border-gray-500'}`}
                            >
                                <div className="flex justify-between items-start mb-2">
                                    <h4 className="font-semibold text-white text-sm truncate pr-2">{script.title}</h4>
                                    <Badge variant="cyber" className="text-[10px] px-1.5 py-0">#{script.id.toString().split('_')[1] || script.id}</Badge>
                                </div>
                                <div className="flex flex-col gap-1.5">
                                    <div className="flex items-center gap-1.5 text-[10px] text-gray-400">
                                        <Calendar className="h-3 w-3 text-pink-400" />
                                        {script.date || (script.created_at ? new Date(script.created_at).toLocaleDateString('fr-FR', { day: '2-digit', month: 'short' }) : 'Date inconnue')}
                                        <Clock className="h-3 w-3 text-cyan-400 ml-1" />
                                        {script.time || (script.created_at ? new Date(script.created_at).toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' }) : '--:--')}
                                    </div>
                                    <p className="text-xs text-gray-500 font-medium">{script.imagePrompts?.length || 0} Storyboard Prompts</p>
                                </div>
                            </div>
                        ))}
                        {scripts.length === 0 && (
                            <div className="text-gray-500 text-sm text-center py-4">Aucun script avec prompts visuels.</div>
                        )}
                    </div>
                </div>

                {/* Main Content */}
                <div className="md:col-span-3 space-y-6">
                    {selectedScript ? (
                        <>
                            <div className="glass-card p-6 flex flex-col md:flex-row justify-between items-start md:items-center gap-4 border border-navy-700">
                                <div>
                                    <h2 className="text-xl font-bold text-white">{selectedScript.title}</h2>
                                    <p className="text-sm text-gray-400 mt-1">7 Prompts structurés par bloc de temps</p>
                                </div>
                                <button
                                    onClick={handleGenerateImages}
                                    disabled={isGenerating}
                                    className="px-6 py-2.5 bg-gradient-to-r from-pink-600 space-x-2 font-medium to-purple-600 text-white rounded-lg shadow-lg hover:shadow-pink-500/25 transition-all w-full md:w-auto flex justify-center items-center disabled:opacity-50"
                                >
                                    {isGenerating ? <Loader2 className="h-5 w-5 animate-spin" /> : <PlayCircle className="h-5 w-5" />}
                                    <span>Générer avec FLUX.1</span>
                                </button>
                            </div>

                            <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
                                {/* Visual Prompts Info */}
                                <div className="glass-card bg-navy-800 p-5 space-y-3">
                                    <h3 className="text-sm uppercase tracking-widest text-gray-400 font-semibold mb-4">Storyboard Prompts</h3>
                                    <div className="space-y-3 max-h-[400px] overflow-y-auto custom-scrollbar pr-2">
                                        {selectedScript.imagePrompts.map((prompt, idx) => (
                                            <div key={idx} className="p-3 bg-navy-900 rounded-lg border border-gray-700">
                                                <div className="text-xs font-bold text-cyan-400 mb-1">Prompt {idx + 1}</div>
                                                <p className="text-sm text-gray-300">{prompt}</p>
                                            </div>
                                        ))}
                                    </div>
                                </div>

                                {/* Generated Images Gallery */}
                                <div className="glass-card bg-navy-800 p-5">
                                    <div className="flex justify-between items-center mb-4">
                                        <h3 className="text-sm uppercase tracking-widest text-gray-400 font-semibold">Galerie de Production</h3>
                                        {generatedImages.length > 0 && (
                                            <button
                                                onClick={handleDownloadZip}
                                                className="flex items-center gap-1.5 text-xs font-semibold bg-gray-700 hover:bg-gray-600 text-white px-3 py-1.5 rounded-md transition-colors"
                                            >
                                                <Download className="h-3.5 w-3.5" /> Zip All
                                            </button>
                                        )}
                                    </div>

                                    {generatedImages.length > 0 ? (
                                        <div className="grid grid-cols-2 gap-3 max-h-[400px] overflow-y-auto custom-scrollbar pr-2">
                                            {generatedImages.map((img, idx) => (
                                                <div key={idx} className="relative aspect-[9/16] bg-navy-900 rounded overflow-hidden border border-gray-700 group flex items-center justify-center">
                                                    <img src={`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}${img}`} alt={`Generated image ${idx + 1}`} className="w-full h-full object-cover" />
                                                </div>
                                            ))}
                                        </div>
                                    ) : (
                                        <div className="h-[400px] flex items-center justify-center border-2 border-dashed border-gray-700 rounded-lg">
                                            <div className="text-center text-gray-500">
                                                <Image className="h-12 w-12 mx-auto mb-3 opacity-20" />
                                                <p>En attente de génération</p>
                                            </div>
                                        </div>
                                    )}
                                </div>
                            </div>

                            {/* Shorts Automation Workflows */}
                            <div className="glass-card p-6 bg-gradient-to-r from-purple-900/40 to-navy-900 border border-purple-500/30">
                                <h3 className="text-md font-bold text-white flex items-center gap-2 mb-4">
                                    <Wand2 className="h-5 w-5 text-purple-400" />
                                    Workflows de Création de Shorts (Auto)
                                </h3>
                                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                                    <button
                                        onClick={handleImageToVideo}
                                        disabled={!!videoProgress}
                                        className="flex flex-col items-center justify-center p-4 bg-navy-900 border border-purple-500/30 hover:border-purple-400 rounded-xl transition-all group disabled:opacity-50"
                                    >
                                        <Film className="h-8 w-8 text-purple-400 mb-2 group-hover:scale-110 transition-transform" />
                                        <span className="font-semibold text-white">1. Image-to-Video Master</span>
                                        <span className="text-xs text-gray-400 mt-1 text-center">Générer via Fal.ai / Kling (5s clips)</span>
                                        {videoProgress && (
                                            <div className="w-full mt-3">
                                                <div className="w-full bg-gray-800 rounded-full h-1.5 overflow-hidden border border-gray-700">
                                                    <div
                                                        className="bg-gradient-to-r from-purple-500 to-pink-500 h-1.5 rounded-full transition-all duration-500"
                                                        style={{ width: `${(videoProgress.completed / Math.max(videoProgress.total, 1)) * 100}%` }}
                                                    ></div>
                                                </div>
                                                <p className="text-[10px] text-purple-300 mt-1 text-center font-mono uppercase tracking-wider">
                                                    {videoProgress.status === 'completed' ? 'Terminé !' : `${videoProgress.completed} / ${videoProgress.total} rendus...`}
                                                </p>
                                            </div>
                                        )}
                                    </button>
                                    <button
                                        onClick={handleAssemblageViral}
                                        className="flex flex-col items-center justify-center p-4 bg-navy-900 border border-pink-500/30 hover:border-pink-400 rounded-xl transition-all group"
                                    >
                                        <PlayCircle className="h-8 w-8 text-pink-400 mb-2 group-hover:scale-110 transition-transform" />
                                        <span className="font-semibold text-white">2. Assemblage Viral</span>
                                        <span className="text-xs text-gray-400 mt-1 text-center">Fusion, TTS & SST (Remotion)</span>
                                    </button>
                                    <button
                                        onClick={handlePublish}
                                        className="flex flex-col items-center justify-center p-4 bg-navy-900 border border-emerald-500/30 hover:border-emerald-400 rounded-xl transition-all group"
                                    >
                                        <Download className="h-8 w-8 text-emerald-400 mb-2 group-hover:scale-110 transition-transform" />
                                        <span className="font-semibold text-white">3. Publier & Exporter (.mp4)</span>
                                        <span className="text-xs text-gray-400 mt-1 text-center">Rendu complet pour TikTok</span>
                                    </button>
                                </div>
                            </div>


                            {/* Remotion Player Preview */}
                            {showPlayer && playerProps && (
                                <div className="glass-card p-6 bg-gradient-to-r from-navy-800 to-navy-900 border border-green-500/30 flex flex-col items-center">
                                    <h3 className="text-md font-bold text-white flex items-center gap-2 mb-4">
                                        <Eye className="h-5 w-5 text-green-400" />
                                        Prévisualisation Remotion (Shorts Viral)
                                    </h3>
                                    <div className="rounded-xl overflow-hidden border border-gray-700 shadow-2xl">
                                        <Player
                                            component={MyComposition}
                                            inputProps={playerProps}
                                            durationInFrames={playerProps.clips.length * 150} // 5s clips at 30 fps
                                            compositionWidth={1080}
                                            compositionHeight={1920}
                                            fps={30}
                                            style={{
                                                width: 300,
                                                height: 533
                                            }}
                                            controls
                                        />
                                    </div>
                                    <p className="text-xs text-gray-400 mt-4 text-center max-w-md">Le rendu final générera automatiquement un véritable .mp4 optimisé pour TikTok avec compression avancée et sous-titres ASS hardcodés.</p>
                                </div>
                            )}

                            {/* Veo Prompt Section */}
                            <div className="glass-card p-6 bg-gradient-to-r from-navy-800 to-navy-900 border border-navy-700">
                                <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 mb-3">
                                    <h3 className="text-md font-bold text-white flex items-center gap-2">
                                        <VideoIcon className="h-5 w-5 text-green-400" />
                                        Prompt d'Animation Universel pour Google Veo
                                    </h3>
                                    <button
                                        onClick={handleCopyVeoPrompt}
                                        className="flex items-center gap-2 text-sm font-semibold bg-gray-800 hover:bg-gray-700 text-gray-200 px-4 py-2 rounded-lg transition-colors border border-gray-700"
                                    >
                                        <Copy className="h-4 w-4" /> Copier le Prompt Veo
                                    </button>
                                </div>
                                <div className="p-4 bg-navy-900 rounded-lg border border-gray-800 text-green-400 font-mono text-sm leading-relaxed">
                                    Animate this futuristic interface with glowing data flows, 4k, cinematic movement
                                </div>
                                <p className="text-xs text-gray-500 mt-3">Collez ce texte avec l'image générée dans l'interface de Google Veo pour animer vos séquences.</p>
                            </div>
                        </>
                    ) : (
                        <div className="glass-card h-[600px] flex items-center justify-center border border-navy-700">
                            <div className="text-center text-gray-500">
                                <p>Sélectionnez un script pour commencer la production visuelle</p>
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

// Lucide icon missing import above
import { VideoIcon } from 'lucide-react';

export default Studio;
