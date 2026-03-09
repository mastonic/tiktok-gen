import React, { useState, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import {
    ArrowLeft, Loader2, AlertCircle, Calendar, Tag,
    Clock, Share2, ExternalLink, BookOpen, Video
} from 'lucide-react';
import AffiliateBento from '../components/AffiliateBento';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:5656';

/**
 * Parse un fichier Markdown avec frontmatter YAML et données Bento JSON.
 */
function parseMarkdownFile(rawContent) {
    const frontmatter = {};
    let body = rawContent.trim();
    let bentoData = null;

    // --- PHASE 1: Extraction du premier Frontmatter ---
    const fmMatch = body.match(/^---\r?\n([\s\S]*?)\r?\n---\r?\n?([\s\S]*)$/);
    if (fmMatch) {
        const yamlStr = fmMatch[1];
        body = fmMatch[2].trim();
        yamlStr.split(/\r?\n/).forEach(line => {
            const kv = line.match(/^([\w-]+):\s*"?([\s\S]*?)"?\s*$/);
            if (kv) frontmatter[kv[1]] = kv[2].replace(/^"(.*)"$/, '$1').trim();
        });
    }

    // --- PHASE 2: Nettoyage recursif (IA artifacts / Double FM) ---
    // On boucle pour enlever les couches successives de ```markdown ou de frontmatter en trop
    let cleaned = true;
    while (cleaned) {
        cleaned = false;

        // Supprime les blocs ```markdown ... ```
        const codeMatch = body.match(/^```(?:markdown)?\r?\n([\s\S]*?)\r?\n```$/i);
        if (codeMatch) {
            body = codeMatch[1].trim();
            cleaned = true;
        }

        // Supprime un second frontmatter si l'IA en a regénéré un (fréquent)
        if (body.startsWith('---')) {
            const secondFmMatch = body.match(/^---\r?\n([\s\S]*?)\r?\n---\r?\n?([\s\S]*)$/);
            if (secondFmMatch) {
                body = secondFmMatch[2].trim();
                cleaned = true;
            }
        }
    }

    // --- PHASE 3: Extraction des données Bento ---
    const bentoMatch = body.match(/<!--\s*AFFILIATE_BENTO_DATA\s*```json\s*([\s\S]*?)\s*```\s*-->/);
    if (bentoMatch) {
        try {
            bentoData = JSON.parse(bentoMatch[1]);
            body = body.replace(bentoMatch[0], '').trim();
        } catch (e) {
            console.warn('Could not parse bento data:', e);
        }
    }

    return { frontmatter, body, bentoData };
}

/**
 * Remplace les balises <AffiliateBento id="..." /> dans le Markdown
 * en les splitant en sections rendues séparément.
 */
function splitBodyByBento(body) {
    const parts = [];
    // Catch [INSERT_VIDEO_PLAYER], [INSERT_BENTO_BOX_1] and old <AffiliateBento />
    const tagRegex = /\[INSERT_VIDEO_PLAYER\]|\[INSERT_BENTO_BOX_1\]|<AffiliateBento\s+id="([^"]+)"\s*\/>/g;
    let lastIndex = 0;
    let match;

    while ((match = tagRegex.exec(body)) !== null) {
        if (match.index > lastIndex) {
            parts.push({ type: 'markdown', content: body.slice(lastIndex, match.index) });
        }

        const fullTag = match[0];
        if (fullTag === '[INSERT_VIDEO_PLAYER]') {
            parts.push({ type: 'video_player' });
        } else if (fullTag === '[INSERT_BENTO_BOX_1]') {
            parts.push({ type: 'bento_multi' });
        } else {
            parts.push({ type: 'bento', toolId: match[1] });
        }

        lastIndex = match.index + fullTag.length;
    }

    if (lastIndex < body.length) {
        parts.push({ type: 'markdown', content: body.slice(lastIndex) });
    }

    return parts;
}

// Mapping pour résoudre les `affiliate_link_placeholder` → vrais liens DB
function resolveToolLink(tool, dbAffiliates) {
    if (!dbAffiliates || !tool.affiliate_link_placeholder) return tool;
    const matched = dbAffiliates.find(a =>
        a.name.toLowerCase() === tool.name?.toLowerCase() ||
        a.reconciliation_keywords?.includes(tool.affiliate_link_placeholder?.replace('_affiliate', ''))
    );
    return matched ? { ...tool, link: matched.link } : tool;
}

// ─────────────────────────────────────────────────────────────────────────────
// COMPOSANT PRINCIPAL BlogPost
// ─────────────────────────────────────────────────────────────────────────────

const BlogPost = ({ slug, onBack }) => {
    // Force scroll to top when opening an article
    useEffect(() => {
        window.scrollTo(0, 0);
    }, [slug]);
    const [state, setState] = useState({ loading: true, error: null, frontmatter: {}, body: '', bentoData: null });
    const [dbAffiliates, setDbAffiliates] = useState([]);
    const [readTime, setReadTime] = useState(0);

    useEffect(() => {
        const load = async () => {
            try {
                // Fetch Markdown file from backend
                const res = await fetch(`${API_URL}/api/blog-squad/post/${slug}`);
                if (!res.ok) throw new Error(`HTTP ${res.status}`);
                const rawContent = await res.text();

                const { frontmatter, body, bentoData } = parseMarkdownFile(rawContent);
                const words = body.split(/\s+/).length;
                setReadTime(Math.ceil(words / 200)); // 200 wpm

                setState({ loading: false, error: null, frontmatter, body, bentoData });
            } catch (e) {
                setState({ loading: false, error: e.message, frontmatter: {}, body: '', bentoData: null });
            }
        };

        // Fetch DB affiliates for link resolution
        fetch(`${API_URL}/api/affiliates`)
            .then(r => r.ok ? r.json() : [])
            .then(setDbAffiliates)
            .catch(() => { });

        load();
    }, [slug]);

    if (state.loading) return (
        <div className="min-h-screen bg-[#050505] flex items-center justify-center">
            <Loader2 className="w-10 h-10 text-cyan-400 animate-spin" />
        </div>
    );

    if (state.error) return (
        <div className="min-h-screen bg-[#050505] flex items-center justify-center">
            <div className="text-center p-8 bg-[#0f0f0f] rounded-3xl border border-white/5 max-w-md">
                <AlertCircle className="w-10 h-10 text-amber-400 mx-auto mb-4" />
                <p className="text-gray-400">{state.error}</p>
                <button onClick={onBack} className="mt-4 text-cyan-400 text-sm hover:underline">← Retour</button>
            </div>
        </div>
    );

    const { frontmatter, body, bentoData } = state;
    const parts = splitBodyByBento(body);
    const tools = bentoData?.tools || [];

    return (
        <div className="min-h-screen bg-[#050505] text-white overflow-y-auto" style={{ fontFamily: "'Inter', sans-serif" }}>

            {/* HEADER */}
            <header className="border-b border-white/5 bg-black/50 backdrop-blur-xl sticky top-0 z-50">
                <div className="max-w-4xl mx-auto px-6 py-4 flex items-center gap-4">
                    <button
                        onClick={onBack}
                        className="flex items-center gap-2 text-gray-400 hover:text-white transition text-sm font-medium"
                    >
                        <ArrowLeft className="w-4 h-4" />
                        <span className="hidden sm:inline">Retour au Blog</span>
                    </button>
                    <div className="flex-1 text-center text-xl font-black tracking-tighter italic">
                        iM-<span className="text-cyan-400">System</span>
                    </div>
                    <button className="flex items-center gap-1.5 bg-white/5 border border-white/10 px-4 py-2 rounded-full text-xs font-semibold hover:bg-white/10 transition">
                        <Share2 className="w-3.5 h-3.5" /> Partager
                    </button>
                </div>
            </header>

            {/* HERO COVER */}
            {frontmatter.cover_image && (
                <div className="w-full h-64 md:h-80 overflow-hidden relative">
                    <img
                        src={frontmatter.cover_image}
                        alt={frontmatter.title}
                        className="w-full h-full object-cover opacity-50"
                    />
                    <div className="absolute inset-0 bg-gradient-to-b from-transparent to-[#050505]" />
                </div>
            )}

            {/* ARTICLE CONTENT */}
            <article className="max-w-3xl mx-auto px-6 py-10">

                {/* Méta */}
                <div className="flex flex-wrap items-center gap-4 mb-6 text-sm text-gray-500">
                    {frontmatter.category && (
                        <span className="flex items-center gap-1.5 bg-cyan-400/10 border border-cyan-400/20 text-cyan-400 px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider">
                            <BookOpen className="w-3 h-3" /> {frontmatter.category}
                        </span>
                    )}
                    {frontmatter.date && (
                        <span className="flex items-center gap-1.5">
                            <Calendar className="w-3.5 h-3.5" /> {frontmatter.date}
                        </span>
                    )}
                    <span className="flex items-center gap-1.5">
                        <Clock className="w-3.5 h-3.5" /> {readTime} min de lecture
                    </span>
                </div>

                {/* Corps de l'article avec Bento inlines */}
                <div className="prose prose-invert prose-lg max-w-none
                    prose-h1:font-black prose-h1:tracking-tight prose-h1:text-4xl prose-h1:md:text-5xl
                    prose-h2:font-bold prose-h2:text-2xl prose-h2:text-white prose-h2:border-b prose-h2:border-white/5 prose-h2:pb-2 prose-h2:mt-12
                    prose-p:text-gray-400 prose-p:leading-relaxed prose-p:text-base
                    prose-blockquote:border-l-cyan-400 prose-blockquote:bg-cyan-400/5 prose-blockquote:rounded-r-xl prose-blockquote:py-1
                    prose-code:text-cyan-300 prose-code:bg-white/5 prose-code:rounded prose-code:px-1
                    prose-pre:bg-[#0f0f0f] prose-pre:border prose-pre:border-white/10 prose-pre:rounded-2xl
                    prose-a:text-cyan-400 prose-a:no-underline hover:prose-a:underline
                    prose-strong:text-white">

                    {parts.map((part, i) => {
                        if (part.type === 'markdown') {
                            return (
                                <ReactMarkdown key={i} remarkPlugins={[remarkGfm]}>
                                    {part.content}
                                </ReactMarkdown>
                            );
                        }

                        if (part.type === 'video_player') {
                            const videoUrl = frontmatter.video_url;
                            return (
                                <div key={i} className="my-10 aspect-video rounded-[2.5rem] bg-neutral-900 overflow-hidden border border-white/10 shadow-2xl">
                                    {videoUrl ? (
                                        <video src={videoUrl} controls autoPlay loop muted playsInline className="w-full h-full object-cover" />
                                    ) : (
                                        <div className="w-full h-full flex flex-col items-center justify-center text-gray-500 gap-3">
                                            <Video className="w-12 h-12 text-cyan-400" />
                                            <p className="text-sm font-bold uppercase tracking-widest italic">Chargement de la vidéo virale...</p>
                                        </div>
                                    )}
                                </div>
                            );
                        }

                        if (part.type === 'bento_multi') {
                            return (
                                <div key={i} className="my-10 grid grid-cols-1 sm:grid-cols-2 gap-4">
                                    {tools.slice(0, 2).map((tool, idx) => {
                                        const resolved = resolveToolLink(tool, dbAffiliates);
                                        return <AffiliateBento key={idx} tool={resolved} compact={true} />;
                                    })}
                                </div>
                            );
                        }

                        if (part.type === 'bento') {
                            const tool = tools.find(t => t.id === part.toolId);
                            if (!tool) return null;
                            const resolvedTool = resolveToolLink(tool, dbAffiliates);
                            return <AffiliateBento key={i} tool={resolvedTool} compact={true} />;
                        }

                        return null;
                    })}
                </div>

                {/* SEO Tags */}
                {bentoData?.seo_tags?.length > 0 && (
                    <div className="mt-12 pt-6 border-t border-white/5 flex flex-wrap gap-2">
                        {bentoData.seo_tags.map((tag, i) => (
                            <span key={i} className="flex items-center gap-1 text-xs text-gray-500 bg-white/5 border border-white/8 px-3 py-1.5 rounded-full">
                                <Tag className="w-3 h-3" /> {tag}
                            </span>
                        ))}
                    </div>
                )}
            </article>

            {/* FOOTER */}
            <footer className="mt-16 py-10 border-t border-white/5 text-center">
                <p className="max-w-2xl mx-auto text-[10px] text-gray-500 mb-6 leading-relaxed normal-case px-4">
                    Certains liens sur ce site sont des liens d'affiliation. Si vous passez par eux, le Dev Masto reçoit une petite commission qui sert exclusivement à financer les serveurs (et le café pour les nuits blanches). Ça ne vous coûte pas plus cher, et ça soutient l'indépendance du projet.
                </p>
                <div className="text-gray-600 text-xs tracking-widest uppercase">
                    iM-System © 2026 • Martinique
                </div>
            </footer>
        </div>
    );
};

export default BlogPost;
