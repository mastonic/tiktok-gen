import React, { useState, useEffect } from 'react';
import { Image, Download, Copy, PlayCircle, Loader2, Film, Wand2, Eye, Clock, Calendar, RefreshCw, Video as VideoIcon } from 'lucide-react';
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
    const [isAvailable, setIsAvailable] = useState(false);
    const [finalVideoUrl, setFinalVideoUrl] = useState('');

    useEffect(() => {
        fetchScripts();
    }, []);

    const fetchScripts = async () => {
        try {
            const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:5656';
            const response = await fetch(`${apiUrl}/api/contents`);
            const data = await response.json();

            // Keep scripts with images or video potential
            const validScripts = data; // Already filtered by status column in backend API

            // Strictly sort by ID (newest first) as requested
            validScripts.sort((a, b) => {
                const idA = parseInt(a.id.split('_')[1]) || 0;
                const idB = parseInt(b.id.split('_')[1]) || 0;
                return idB - idA;
            });

            setScripts(validScripts);

            const savedId = localStorage.getItem('lastSelectedScriptId');
            const restored = validScripts.find(s => s.id === savedId);

            if (restored) {
                setSelectedScript(restored);
                loadScriptAssets(restored);
            } else if (validScripts.length > 0) {
                const first = validScripts[0];
                setSelectedScript(first);
                loadScriptAssets(first);
            }
        } catch (error) {
            console.error("Error fetching scripts:", error);
        }
    };

    const loadScriptAssets = (script) => {
        const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:5656';
        const timestamp = Date.now();
        if (script.hasImages) {
            const imgs = (script.imagePrompts || []).map((_, i) =>
                `${apiUrl}/media/production/${script.id}/img_${(i + 1).toString().padStart(2, '0')}.jpg?t=${timestamp}`
            );
            setGeneratedImages(imgs);
        } else {
            setGeneratedImages([]);
        }

        // Also load player props if it has audio
        if (script.hasAudio) {
            setPlayerProps({
                clips: script.existingClips && script.existingClips.length > 0
                    ? script.existingClips.map(c => `${apiUrl}${c}?t=${timestamp}`)
                    : (script.imagePrompts || []).map((_, i) => `${apiUrl}/media/production/${script.id}/img_${(i + 1).toString().padStart(2, '0')}.jpg?t=${timestamp}`),
                audioUrl: `${apiUrl}/media/production/${script.id}/voiceover.wav?t=${timestamp}`,
                subtitles: []
            });
            setShowPlayer(true);
        } else {
            setShowPlayer(false);
        }
    };

    const handleGenerateImages = async () => {
        if (!selectedScript) return;
        setIsGenerating(true);
        try {
            const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:5656';
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
                const timestamp = Date.now();
                setGeneratedImages(data.images.map(img => `${apiUrl}${img}?t=${timestamp}`));
                fetchScripts(); // Refresh to get hasImages:true
            }
        } catch (error) {
            console.error("Error generating images:", error);
        } finally {
            setIsGenerating(false);
        }
    };

    const handleImageToVideo = async () => {
        if (!selectedScript) return;
        try {
            setVideoProgress({ total: 100, completed: 0, status: 'Démarrage...' });
            const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:5656';
            const response = await fetch(`${apiUrl}/api/workflows/image-to-video`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ script_id: selectedScript.id })
            });

            const interval = setInterval(async () => {
                try {
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
                        setTimeout(() => alert("Génération de clips vidéo terminée !"), 500);
                        fetchScripts();
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
            const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:5656';
            const response = await fetch(`${apiUrl}/api/workflows/assemblage-viral`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ script_id: selectedScript.id })
            });
            const data = await response.json();
            if (data.status === 'success') {
                const videoClips = data.clips && data.clips.length > 0
                    ? data.clips.map(clip => `${apiUrl}${clip}`)
                    : generatedImages;

                setPlayerProps({
                    clips: videoClips.length > 0 ? videoClips : ["https://sample-videos.com/video321/mp4/720/big_buck_bunny_720p_5mb.mp4"],
                    audioUrl: data.audioUrl ? `${apiUrl}${data.audioUrl}` : "",
                    subtitles: data.subtitles || []
                });
                setShowPlayer(true);
            }
        } catch (error) {
            console.error("Error triggering assemblage-viral workflow:", error);
        }
    };

    const handlePublish = async () => {
        if (!selectedScript) return;
        try {
            setIsGenerating(true); // Re-use loading state for rendering
            setIsAvailable(false);
            setFinalVideoUrl('');

            const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:5656';
            const response = await fetch(`${apiUrl}/api/workflows/publish`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ script_id: selectedScript.id })
            });
            const data = await response.json();

            if (data.status === 'success' && data.videoUrl) {
                // Refresh script list to get newest hasFinalVideo status
                await fetchScripts();
                // Find updated script to get correct finalVideoUrl
                const updated = scripts.find(s => s.id === selectedScript.id);
                const downloadUrl = updated?.finalVideoUrl ? `${apiUrl}${updated.finalVideoUrl}` : `${apiUrl}${data.videoUrl}`;

                setFinalVideoUrl(downloadUrl);
                setIsAvailable(true);
            } else {
                alert(`Erreur de rendu: ${data.message || "Fichier non généré"}`);
            }
        } catch (error) {
            console.error("Error publishing:", error);
            alert("Erreur de connexion lors du rendu final.");
        } finally {
            setIsGenerating(false);
        }
    };

    return (
        <div className="space-y-6">
            <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-6">
                <div>
                    <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
                        <Image className="h-6 w-6 text-pink-500" />
                        Production Studio
                    </h1>
                    <p className="text-gray-400 mt-1 text-sm">Générer les images FLUX.1 et vidéo viral</p>
                </div>
                <button
                    onClick={fetchScripts}
                    className="p-2 bg-navy-800 border border-gray-700 rounded-lg text-gray-400 hover:text-white hover:border-gray-500 transition-all self-end sm:self-auto"
                >
                    <RefreshCw className="h-5 w-5" />
                </button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                {/* Sidebar */}
                <div className="md:col-span-1 space-y-4">
                    <h3 className="text-lg font-medium text-white mb-2">Scripts Prêts</h3>
                    <div className="space-y-2 max-h-[70vh] overflow-y-auto custom-scrollbar pr-2">
                        {scripts.map(script => (
                            <button
                                key={script.id}
                                onClick={() => {
                                    setSelectedScript(script);
                                    localStorage.setItem('lastSelectedScriptId', script.id);
                                    loadScriptAssets(script);
                                }}
                                className={`w-full text-left p-4 rounded-xl border transition-all ${selectedScript?.id === script.id
                                    ? 'bg-pink-900/20 border-pink-500/50'
                                    : 'border-gray-800 hover:bg-gray-800/50 hover:border-gray-700'
                                    }`}
                            >
                                <div className="flex justify-between items-start mb-2">
                                    <h4 className="font-semibold text-white text-sm truncate pr-2">{script.title}</h4>
                                    <Badge variant="cyber" className="text-[10px] px-1.5 py-0">#{script.id.toString().split('_')[1] || script.id}</Badge>
                                </div>
                                <div className="flex flex-col gap-1.5">
                                    <div className="flex items-center gap-1.5 text-[10px] text-gray-400">
                                        <Calendar className="h-3 w-3 text-pink-400" />
                                        {script.date || (script.created_at ? new Date(script.created_at).toLocaleDateString('fr-FR', { day: '2-digit', month: 'short' }) : 'Date inconnue')}
                                    </div>
                                    <div className="flex items-center gap-2">
                                        {script.hasImages && <Badge variant="success" className="text-[8px] h-3">Images OK</Badge>}
                                        {script.hasVideos && <Badge variant="info" className="text-[8px] h-3">Video OK</Badge>}
                                    </div>
                                </div>
                            </button>
                        ))}
                    </div>
                </div>

                {/* Main View */}
                <div className="md:col-span-3 space-y-6">
                    {selectedScript ? (
                        <div className="bg-navy-800/50 rounded-2xl border border-gray-700 p-4 md:p-6">
                            <div className="flex flex-col xl:flex-row justify-between items-start gap-6 mb-6">
                                <div className="w-full">
                                    <h2 className="text-xl font-bold text-white mb-2">{selectedScript.title}</h2>
                                    <div className="flex flex-wrap gap-2">
                                        {selectedScript.keywords?.split(',').map((kw, i) => (
                                            <span key={i} className="text-[10px] bg-navy-900 text-gray-400 px-2 py-1 rounded border border-gray-800 truncate max-w-[120px]">
                                                {kw.trim()}
                                            </span>
                                        ))}
                                    </div>
                                </div>
                                <div className="flex flex-wrap sm:flex-nowrap gap-2 w-full xl:w-auto">
                                    <button
                                        onClick={handleGenerateImages}
                                        disabled={isGenerating}
                                        className="flex-1 sm:flex-none flex items-center justify-center gap-2 px-4 py-2 bg-pink-600 hover:bg-pink-500 disabled:bg-gray-700 text-white rounded-lg text-xs font-semibold transition-all shadow-lg"
                                    >
                                        {isGenerating ? <Loader2 className="h-4 w-4 animate-spin" /> : <Wand2 className="h-4 w-4" />}
                                        <span className="whitespace-nowrap">{selectedScript.hasImages ? "Régénérer" : "Images"}</span>
                                    </button>
                                    <button
                                        onClick={handleImageToVideo}
                                        disabled={!selectedScript.hasImages || videoProgress}
                                        className="flex-1 sm:flex-none flex items-center justify-center gap-2 px-4 py-2 bg-cyan-600 hover:bg-cyan-500 disabled:bg-gray-700 text-white rounded-lg text-xs font-semibold transition-all shadow-lg"
                                    >
                                        <Film className="h-4 w-4" />
                                        <span className="whitespace-nowrap">Clips</span>
                                    </button>
                                    <button
                                        onClick={handleAssemblageViral}
                                        disabled={!selectedScript.hasImages}
                                        className="flex-1 sm:flex-none flex items-center justify-center gap-2 px-4 py-2 bg-emerald-600 hover:bg-emerald-500 disabled:bg-gray-700 text-white rounded-lg text-xs font-semibold transition-all shadow-lg"
                                    >
                                        <PlayCircle className="h-4 w-4" />
                                        <span className="whitespace-nowrap">Preview</span>
                                    </button>
                                </div>
                            </div>

                            {/* Video Generation Progress Bar */}
                            {videoProgress && (
                                <div className="mb-6 bg-navy-900/80 p-4 rounded-xl border border-cyan-500/30">
                                    <div className="flex justify-between text-xs text-white mb-2">
                                        <span className="flex items-center gap-2">
                                            <Loader2 className="h-3 w-3 animate-spin text-cyan-400" />
                                            {videoProgress.status || "Génération..."}
                                        </span>
                                        <span>{videoProgress.completed} / {videoProgress.total} clips</span>
                                    </div>
                                    <div className="w-full bg-gray-800 h-2 rounded-full overflow-hidden">
                                        <div
                                            className="bg-cyan-500 h-full transition-all duration-500 shadow-[0_0_10px_rgba(6,182,212,0.5)]"
                                            style={{ width: `${(videoProgress.completed / videoProgress.total) * 100}%` }}
                                        ></div>
                                    </div>
                                </div>
                            )}

                            {/* Remotion Player Section */}
                            {showPlayer && playerProps && (
                                <div className="mb-8 overflow-hidden rounded-xl border border-gray-700 bg-black aspect-[9/16] max-w-[320px] mx-auto shadow-2xl relative group">
                                    <Player
                                        component={MyComposition}
                                        inputProps={playerProps}
                                        durationInFrames={playerProps.clips.length * 90}
                                        fps={30}
                                        compositionWidth={1080}
                                        compositionHeight={1920}
                                        style={{ width: '100%', height: '100%' }}
                                        controls
                                        autoPlay
                                        loop
                                    />
                                    <div className="absolute top-4 right-4 flex flex-col gap-2 z-20">
                                        {isAvailable && finalVideoUrl ? (
                                            <a
                                                href={finalVideoUrl}
                                                target="_blank"
                                                rel="noopener noreferrer"
                                                className="p-3 bg-green-500 rounded-full text-white shadow-xl hover:scale-110 transition-transform flex items-center justify-center"
                                                title="Télécharger la Vidéo Finale"
                                            >
                                                <Download className="h-5 w-5" />
                                            </a>
                                        ) : (
                                            <button
                                                onClick={handlePublish}
                                                disabled={isGenerating}
                                                className={`p-3 rounded-full text-white shadow-xl flex items-center justify-center transition-transform ${isGenerating ? 'bg-gray-500 cursor-not-allowed' : 'bg-pink-600 hover:scale-110'}`}
                                                title={isGenerating ? "Rendu en cours..." : "Exporter & Publier"}
                                            >
                                                {isGenerating ? <Loader2 className="h-5 w-5 animate-spin" /> : <Film className="h-5 w-5" />}
                                            </button>
                                        )}
                                    </div>
                                </div>
                            )}

                            {/* Storyboard Grid */}
                            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                                {(selectedScript.imagePrompts || []).map((prompt, i) => (
                                    <div key={i} className="group relative bg-navy-900 rounded-xl overflow-hidden border border-gray-800 transition-all hover:border-pink-500/50">
                                        <div className="aspect-[9/16] bg-gray-800">
                                            {generatedImages[i] ? (
                                                <img src={generatedImages[i]} alt={`Scene ${i + 1}`} className="w-full h-full object-cover" />
                                            ) : (
                                                <div className="w-full h-full flex flex-col items-center justify-center text-gray-600 gap-2 p-4 text-center">
                                                    <Image className="h-8 w-8 opacity-20" />
                                                    <span className="text-[10px]">Scene {i + 1} en attente</span>
                                                </div>
                                            )}
                                        </div>
                                        <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity p-4 flex flex-col justify-end">
                                            <p className="text-[10px] text-gray-200 line-clamp-3">{prompt}</p>
                                        </div>
                                        <div className="absolute top-2 left-2 px-2 py-0.5 bg-black/60 backdrop-blur-md rounded text-[10px] text-white border border-white/10">
                                            Scene {i + 1}
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    ) : (
                        <div className="h-[60vh] flex flex-col items-center justify-center text-gray-500 bg-navy-800/30 rounded-2xl border border-dashed border-gray-700">
                            <Film className="h-12 w-12 mb-4 opacity-20" />
                            <p>Sélectionnez un script pour commencer la production</p>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

export default Studio;
