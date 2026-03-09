import React, { useState, useEffect } from 'react';
import { ExternalLink, Zap, Mic, Video, Server, Loader2, AlertCircle, Mail, ArrowRight, Calendar, BookOpen, Cpu, Search } from 'lucide-react';
import AffiliateBento from '../components/AffiliateBento';
import BlogPost from './BlogPost';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:5656';

const categoryIcons = {
    'Voice IA': Mic,
    'Video Gen': Video,
    'Cloud Hosting': Server,
    'GPU Cloud': Cpu,
};

// ─────────────────────────────────────────
// Carte de résumé d'un article (liste)
// ─────────────────────────────────────────
const PostCard = ({ post, onClick }) => (
    <button
        onClick={onClick}
        className="relative text-left w-full h-80 rounded-[2.5rem] border border-white/5 overflow-hidden group transition-all duration-500 hover:border-cyan-400/30 hover:shadow-[0_0_30px_rgba(34,211,238,0.1)]"
    >
        {/* Background Image with Overlay */}
        <div className="absolute inset-0 z-0">
            <img
                src={post.cover_image || "https://images.unsplash.com/photo-1677442136019-21780ecad995?auto=format&fit=crop&q=80&w=1200"}
                className="w-full h-full object-cover transform group-hover:scale-110 transition-transform duration-700 opacity-40 group-hover:opacity-60"
                alt={post.title}
            />
            <div className="absolute inset-0 bg-gradient-to-t from-[#050505] via-[#050505]/80 to-transparent" />
        </div>

        {/* Content */}
        <div className="absolute inset-0 z-10 p-8 flex flex-col justify-end gap-4">
            <div className="flex items-center gap-2">
                <span className="text-[10px] font-bold uppercase tracking-widest text-cyan-400 bg-cyan-400/10 border border-cyan-400/20 px-2 py-0.5 rounded-full">
                    ✍️ iM-Tech Academy
                </span>
                {post.date && (
                    <span className="text-[10px] text-gray-400 flex items-center gap-1 font-medium">
                        <Calendar className="w-3 h-3 text-cyan-400" /> {post.date}
                    </span>
                )}
            </div>

            <h3 className="text-xl font-black text-white leading-tight group-hover:text-cyan-400 transition-colors">
                {post.title}
            </h3>

            {/* Button Large with Gradient */}
            <div className="mt-2 inline-flex items-center justify-center gap-2 bg-gradient-to-r from-cyan-500 to-blue-600 text-white text-xs font-black uppercase tracking-wider py-4 px-6 rounded-2xl group-hover:shadow-[0_0_20px_rgba(6,182,212,0.4)] transform group-hover:-translate-y-1 transition-all duration-300">
                Explorer l'article
                <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
            </div>
        </div>
    </button>
);

// ─────────────────────────────────────────
// Section Héro Vidéo
// ─────────────────────────────────────────
const HeroSection = ({ data }) => {
    const tools = data?.tools || [];

    return (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 items-start mb-24">

            {/* Colonne Gauche: Vidéo + Texte */}
            <div className="lg:col-span-8 space-y-8">
                <div className="relative aspect-video w-full bg-neutral-900 rounded-[2rem] border border-white/10 overflow-hidden shadow-2xl shadow-cyan-950/10">
                    {data?.videoUrl ? (
                        <video src={data.videoUrl} autoPlay loop muted playsInline controls className="w-full h-full object-cover" />
                    ) : (
                        <>
                            <img
                                src="https://images.unsplash.com/photo-1677442136019-21780ecad995?auto=format&fit=crop&q=80&w=1600"
                                className="w-full h-full object-cover"
                                alt="AI Visual"
                            />
                            <div className="absolute inset-0 flex items-center justify-center bg-black/30">
                                <div className="w-20 h-20 bg-white/10 backdrop-blur-md rounded-full flex items-center justify-center border border-white/20 hover:scale-110 transition-transform cursor-pointer">
                                    <div className="w-0 h-0 border-y-[12px] border-y-transparent border-l-[20px] border-l-white ml-1" />
                                </div>
                            </div>
                        </>
                    )}
                    <div className="absolute top-4 left-4 bg-black/60 backdrop-blur-sm px-3 py-1.5 rounded-full border border-white/10 text-xs font-semibold text-gray-300">
                        🎬 Viral Video [Autoplay Loop]
                    </div>
                </div>

                <div className="space-y-4">
                    <h1 className="text-4xl md:text-6xl font-black tracking-tight leading-[1.1]">
                        {data?.videoTitle || 'Le Secret de l\'IA Révélé'}
                        <br className="hidden md:block" />
                        <span className="text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 to-blue-500">
                            {' '}(1M de Vues !)
                        </span>
                    </h1>
                    <p className="text-gray-400 text-lg md:text-xl max-w-2xl leading-relaxed">
                        {data?.summary || 'Voici les outils exacts utilisés pour créer cette vidéo. Testez-les gratuitement.'}
                    </p>
                    <ul className="hidden md:block space-y-3 text-gray-500 border-l-2 border-white/5 pl-6 text-sm">
                        <li>• Automatisation complète via CrewAI</li>
                        <li>• Rendu cinématique via Luma Dream Machine</li>
                        <li>• Voix off émotionnelle via ElevenLabs</li>
                    </ul>
                </div>

                {/* Mobile: cartes 2 cols */}
                {tools.length > 0 && (
                    <div className="grid grid-cols-2 gap-4 lg:hidden">
                        {tools.map((tool, i) => (
                            <AffiliateBento key={i} tool={tool} />
                        ))}
                    </div>
                )}
            </div>

            {/* Colonne Droite: Bento Cards (desktop) */}
            {tools.length > 0 && (
                <div className="hidden lg:flex lg:col-span-4 flex-col gap-4">
                    {tools.map((tool, i) => (
                        <AffiliateBento key={i} tool={tool} />
                    ))}
                </div>
            )}
        </div>
    );
};

// ─────────────────────────────────────────
// PAGE PRINCIPALE
// ─────────────────────────────────────────
const Blog = () => {
    useEffect(() => {
        window.scrollTo(0, 0);
    }, []);

    const [heroData, setHeroData] = useState(null);
    const [posts, setPosts] = useState([]);
    const [loadingHero, setLoadingHero] = useState(true);
    const [loadingPosts, setLoadingPosts] = useState(true);
    const [activePost, setActivePost] = useState(null);

    // Filter states
    const [searchTerm, setSearchTerm] = useState('');
    const [selectedCategory, setSelectedCategory] = useState('All');
    const [selectedTag, setSelectedTag] = useState('All');

    useEffect(() => {
        // Fetch dernière vidéo pour le Héro
        fetch(`${API_URL}/api/blog/latest`, { redirect: 'follow' })
            .then(r => r.ok ? r.json() : null)
            .then(d => { setHeroData(d); setLoadingHero(false); })
            .catch(() => setLoadingHero(false));

        // Fetch liste des articles générés par BlogSquad
        fetch(`${API_URL}/api/blog-squad/posts`)
            .then(r => r.ok ? r.json() : [])
            .then(d => { setPosts(d); setLoadingPosts(false); })
            .catch(() => setLoadingPosts(false));
    }, []);

    // Derived data for filters
    const categories = ['All', ...new Set(posts.map(p => p.category).filter(Boolean))];
    const tags = ['All', ...new Set(posts.flatMap(p => p.tags || []).filter(Boolean))];

    const filteredPosts = posts.filter(post => {
        const matchesSearch = post.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
            post.excerpt.toLowerCase().includes(searchTerm.toLowerCase());
        const matchesCategory = selectedCategory === 'All' || post.category === selectedCategory;
        const matchesTag = selectedTag === 'All' || (post.tags && post.tags.includes(selectedTag));
        return matchesSearch && matchesCategory && matchesTag;
    });

    // Navigation vers un article
    if (activePost) {
        return <BlogPost slug={activePost} onBack={() => setActivePost(null)} />;
    }

    return (
        <div className="min-h-screen bg-[#050505] text-white overflow-y-auto" style={{ fontFamily: "'Inter', sans-serif" }}>

            {/* HEADER */}
            <header className="border-b border-white/5 bg-black/50 backdrop-blur-xl sticky top-0 z-50">
                <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
                    <div className="text-2xl font-black tracking-tighter italic">
                        iM-<span className="text-cyan-400">System</span>
                        <span className="ml-2 text-xs font-semibold text-gray-600 bg-white/5 px-2 py-0.5 rounded-full border border-white/8 align-middle normal-case not-italic">BLOG</span>
                    </div>
                    <div className="hidden md:flex flex-1 justify-center max-w-md mx-8 px-4">
                        <div className="relative w-full">
                            <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500">
                                <Search className="w-4 h-4" />
                            </span>
                            <input
                                type="text"
                                placeholder="Rechercher un article..."
                                className="w-full bg-white/5 border border-white/10 rounded-full py-2 pl-10 pr-4 text-sm focus:outline-none focus:border-cyan-400 transition-colors"
                                value={searchTerm}
                                onChange={(e) => setSearchTerm(e.target.value)}
                            />
                        </div>
                    </div>
                    <div className="hidden md:flex gap-8 text-sm font-medium text-gray-400">
                        <a href="#" className="hover:text-white transition">Home</a>
                        <a href="#" className="hover:text-white transition">About</a>
                    </div>
                    <div className="flex items-center gap-2">
                        <div className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                        <span className="text-xs text-gray-500">Live</span>
                    </div>
                </div>
            </header>

            <main className="max-w-7xl mx-auto px-6 py-8 md:py-16">

                {/* SECTION HÉRO — Dernière Vidéo + Affiliés */}
                {loadingHero ? (
                    <div className="flex items-center justify-center py-24">
                        <Loader2 className="w-8 h-8 text-cyan-400 animate-spin" />
                    </div>
                ) : heroData ? (
                    <HeroSection data={heroData} />
                ) : (
                    <div className="text-center py-20 text-gray-600">
                        <AlertCircle className="w-10 h-10 mx-auto mb-3 text-gray-700" />
                        Lance un Run pour voir ta première vidéo ici.
                    </div>
                )}

                {/* SECTION ARTICLES — Générés par BlogSquad */}
                {(posts.length > 0 || loadingPosts) && (
                    <section>
                        <div className="flex flex-col md:flex-row md:items-end justify-between mb-8 gap-4">
                            <div>
                                <h2 className="text-3xl font-black tracking-tight">
                                    Articles du Blog
                                </h2>
                                <p className="text-gray-500 text-sm mt-1">Générés automatiquement par la BlogSquad · Optimisés SEO</p>
                            </div>

                            <div className="flex flex-wrap gap-2">
                                {/* Category Select */}
                                <select
                                    className="bg-white/5 border border-white/10 rounded-xl px-3 py-1.5 text-xs text-gray-300 focus:outline-none focus:border-cyan-400"
                                    value={selectedCategory}
                                    onChange={(e) => setSelectedCategory(e.target.value)}
                                >
                                    {categories.map(cat => <option key={cat} value={cat}>{cat === 'All' ? 'Toutes les catégories' : cat}</option>)}
                                </select>

                                {/* Tag Select */}
                                <select
                                    className="bg-white/5 border border-white/10 rounded-xl px-3 py-1.5 text-xs text-gray-300 focus:outline-none focus:border-cyan-400"
                                    value={selectedTag}
                                    onChange={(e) => setSelectedTag(e.target.value)}
                                >
                                    {tags.map(tag => <option key={tag} value={tag}>{tag === 'All' ? 'Tous les tags' : `#${tag}`}</option>)}
                                </select>
                            </div>
                        </div>

                        {loadingPosts ? (
                            <div className="flex items-center gap-2 text-gray-600 text-sm">
                                <Loader2 className="w-4 h-4 animate-spin" /> Chargement des articles...
                            </div>
                        ) : filteredPosts.length === 0 ? (
                            <div className="py-20 text-center text-gray-500 italic">
                                Aucun article ne correspond à votre recherche.
                            </div>
                        ) : (
                            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                                {filteredPosts.map((post) => (
                                    <PostCard
                                        key={post.slug}
                                        post={post}
                                        onClick={() => setActivePost(post.slug)}
                                    />
                                ))}
                            </div>
                        )}
                    </section>
                )}
            </main>

            {/* FOOTER */}
            <footer className="mt-20 py-12 border-t border-white/5 text-center text-gray-600 text-xs tracking-widest uppercase">
                iM-System © 2026 • Martinique • <a href="#" className="hover:text-gray-400 transition">Mentions Légales</a> | <a href="#" className="hover:text-gray-400 transition">Contact</a>
            </footer>
        </div>
    );
};

export default Blog;
