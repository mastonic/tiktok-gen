import { API_URL } from '../api';
import React, { useState, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import {
    ArrowLeft, Loader2, AlertCircle, Calendar, Tag,
    Clock, Share2, ExternalLink, BookOpen, Video, Zap
} from 'lucide-react';
import AffiliateBento from '../components/AffiliateBento';
import { LogoFull } from '../components/ui/Logos';

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

    // --- PHASE 2: Nettoyage recursif ---
    let cleaned = true;
    while (cleaned) {
        cleaned = false;
        const codeMatch = body.match(/^```(?:markdown)?\r?\n([\s\S]*?)\r?\n```$/i);
        if (codeMatch) {
            body = codeMatch[1].trim();
            cleaned = true;
        }
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

function splitBodyByBento(body) {
    const parts = [];
    const tagRegex = /\[INSERT_VIDEO_PLAYER\]|\[INSERT_BENTO_BOX_1\]|\[BENTO_TOOLS\]|<AffiliateBento\s+id="([^"]+)"\s*\/>/g;
    let lastIndex = 0;
    let match;

    while ((match = tagRegex.exec(body)) !== null) {
        if (match.index > lastIndex) {
            parts.push({ type: 'markdown', content: body.slice(lastIndex, match.index) });
        }
        const fullTag = match[0];
        if (fullTag === '[INSERT_VIDEO_PLAYER]') {
            parts.push({ type: 'video_player' });
        } else if (fullTag === '[INSERT_BENTO_BOX_1]' || fullTag === '[BENTO_TOOLS]') {
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

function resolveToolLink(tool, dbAffiliates) {
    if (!dbAffiliates || !tool.affiliate_link_placeholder) return tool;
    const matched = dbAffiliates.find(a =>
        a.name.toLowerCase() === tool.name?.toLowerCase() ||
        a.reconciliation_keywords?.includes(tool.affiliate_link_placeholder?.replace('_affiliate', ''))
    );
    return matched ? { ...tool, link: matched.link } : tool;
}

const BlogPost = ({ slug, onBack }) => {
    const [state, setState] = useState({ loading: true, error: null, frontmatter: {}, body: '', bentoData: null });
    const [dbAffiliates, setDbAffiliates] = useState([]);
    const [readTime, setReadTime] = useState(0);
    const [scrollProgress, setScrollProgress] = useState(0);
    const [showBackToTop, setShowBackToTop] = useState(false);
    const [headings, setHeadings] = useState([]);

    useEffect(() => {
        window.scrollTo(0, 0);
    }, [slug]);

    useEffect(() => {
        const handleScroll = () => {
            const totalHeight = document.documentElement.scrollHeight - window.innerHeight;
            const progress = totalHeight > 0 ? (window.scrollY / totalHeight) * 100 : 0;
            setScrollProgress(progress);
            setShowBackToTop(window.scrollY > 400);
        };
        window.addEventListener('scroll', handleScroll);
        return () => window.removeEventListener('scroll', handleScroll);
    }, []);

    useEffect(() => {
        const load = async () => {
            try {
                const res = await fetch(`${API_URL}/api/blog-squad/post/${slug}`);
                if (!res.ok) throw new Error(`HTTP ${res.status}`);
                const rawContent = await res.text();
                const { frontmatter, body, bentoData } = parseMarkdownFile(rawContent);
                const words = body.split(/\s+/).length;
                setReadTime(Math.ceil(words / 200));
                
                // Extract TOC
                const matches = body.match(/^#{2,3}\s+(.+)$/gm);
                if (matches) {
                    const h = matches.map(m => {
                        const level = m.startsWith('###') ? 3 : 2;
                        const text = m.replace(/^#{2,3}\s+/, '');
                        const id = text.toLowerCase().replace(/[^\w\s-]/g, '').replace(/\s+/g, '-');
                        return { level, text, id };
                    });
                    setHeadings(h);
                }

                setState({ loading: false, error: null, frontmatter, body, bentoData });
            } catch (e) {
                setState({ loading: false, error: e.message, frontmatter: {}, body: '', bentoData: null });
            }
        };
        fetch(`${API_URL}/api/affiliates`).then(r => r.ok ? r.json() : []).then(setDbAffiliates).catch(() => { });
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

    const components = {
        h2: ({ children }) => {
            const text = React.Children.toArray(children).join('');
            const id = text.toLowerCase().replace(/[^\w\s-]/g, '').replace(/\s+/g, '-');
            return <h2 id={id} className="text-2xl font-bold text-white border-b border-white/5 pb-2 mt-12 mb-6 group flex items-center gap-2">
                <span className="text-cyan-500 opacity-0 group-hover:opacity-100 transition-opacity">#</span>
                {children}
            </h2>;
        },
        h3: ({ children }) => {
            const text = React.Children.toArray(children).join('');
            const id = text.toLowerCase().replace(/[^\w\s-]/g, '').replace(/\s+/g, '-');
            return <h3 id={id} className="text-xl font-semibold text-gray-200 mt-8 mb-4 flex items-center gap-2">
                <span className="w-1.5 h-1.5 rounded-full bg-cyan-500" />
                {children}
            </h3>;
        }
    };

    return (
        <div className="min-h-screen bg-[#050505] text-white overflow-y-auto pb-24" style={{ fontFamily: "'Inter', sans-serif" }}>
            <div className="fixed top-0 left-0 h-1 bg-gradient-to-r from-cyan-600 to-blue-500 z-[60] transition-all duration-100 shadow-[0_0_10px_rgba(6,182,212,0.5)]" style={{ width: `${scrollProgress}%` }} />
            
            <button
                onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}
                className={`fixed bottom-8 right-8 z-[60] bg-cyan-500 text-black p-4 rounded-2xl shadow-2xl transition-all duration-500 hover:scale-110 active:scale-95 ${showBackToTop ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-10 pointer-events-none'}`}
            >
                <ArrowLeft className="w-6 h-6 rotate-90" />
            </button>

            <header className="border-b border-white/5 bg-black/50 backdrop-blur-xl sticky top-0 z-50">
                <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
                    <button onClick={onBack} className="flex items-center gap-2 text-gray-400 hover:text-white transition text-sm font-medium">
                        <ArrowLeft className="w-4 h-4" />
                        <span className="hidden sm:inline">Blog</span>
                    </button>
                    <div className="flex-1 flex justify-center transform hover:scale-105 transition-transform"><LogoFull className="h-10 md:h-14 w-auto" /></div>
                    <button className="flex items-center gap-1.5 bg-white/5 border border-white/10 px-4 py-2 rounded-full text-xs font-semibold hover:bg-white/10 transition">
                        <Share2 className="w-3.5 h-3.5" /> <span className="hidden md:inline">Partager</span>
                    </button>
                </div>
            </header>

            <div className="max-w-7xl mx-auto px-6 grid grid-cols-1 lg:grid-cols-12 gap-12 mt-12">
                <aside className="hidden lg:block lg:col-span-3">
                    <div className="sticky top-32 space-y-8">
                        <div>
                            <h4 className="text-[10px] font-black uppercase tracking-widest text-cyan-400/60 mb-6">Sommaire</h4>
                            <nav className="space-y-4">
                                {headings.map((h, i) => (
                                    <a key={i} href={`#${h.id}`} className={`block text-sm transition-all hover:text-cyan-400 ${h.level === 3 ? 'pl-4 text-gray-500' : 'text-gray-400 font-medium'}`}>
                                        {h.text}
                                    </a>
                                ))}
                            </nav>
                        </div>
                        <div className="p-6 rounded-3xl bg-white/5 border border-white/10 space-y-4">
                            <div className="w-10 h-10 rounded-2xl bg-cyan-500/10 flex items-center justify-center"><Zap className="w-5 h-5 text-cyan-400" /></div>
                            <h5 className="font-bold text-sm">Prêt à automatiser ?</h5>
                            <p className="text-xs text-gray-500 leading-relaxed">Boostez votre productivité avec nos outils IA sélectionnés par des pros.</p>
                        </div>
                    </div>
                </aside>

                <div className="lg:col-span-9 max-w-3xl">
                    <article>
                        <div className="space-y-6 mb-12">
                            <div className="flex items-center gap-3">
                                <span className="bg-cyan-500/10 text-cyan-400 text-[10px] font-black uppercase tracking-widest px-3 py-1 rounded-full border border-cyan-500/20">{frontmatter.category || "IA Générative"}</span>
                                <div className="h-px w-8 bg-white/10" />
                                <span className="text-[10px] text-gray-500 font-bold uppercase tracking-widest flex items-center gap-1.5"><Clock className="w-3 h-3" /> {readTime} min de lecture</span>
                            </div>
                            <h1 className="text-4xl md:text-6xl font-black tracking-tight leading-[1.1] text-white">{frontmatter.title}</h1>
                            <p className="text-xl text-gray-400 leading-relaxed italic border-l-4 border-cyan-500 pl-6 py-2">{frontmatter.excerpt}</p>
                            <div className="flex items-center gap-3 py-4 border-y border-white/5">
                                <img src="https://api.dicebear.com/7.x/avataaars/svg?seed=Masto" className="w-10 h-10 rounded-full bg-white/10" alt="Author" />
                                <div>
                                    <p className="text-sm font-bold">Masto Dev</p>
                                    <p className="text-[10px] text-gray-500 uppercase font-black tracking-widest">{frontmatter.date || "Mars 2026"}</p>
                                </div>
                            </div>
                        </div>

                        {headings.length > 0 && (
                            <div className="lg:hidden p-6 rounded-[2rem] bg-white/5 border border-white/10 mb-12">
                                <details className="group">
                                    <summary className="list-none flex items-center justify-between cursor-pointer">
                                        <h4 className="text-sm font-black uppercase tracking-widest text-cyan-400">Sommaire de l'article</h4>
                                        <div className="w-8 h-8 rounded-full bg-white/5 flex items-center justify-center transition-transform group-open:rotate-180"><ArrowLeft className="w-4 h-4 rotate-270" /></div>
                                    </summary>
                                    <nav className="mt-6 space-y-4 border-t border-white/5 pt-6">
                                        {headings.map((h, i) => (
                                            <a key={i} href={`#${h.id}`} className={`block text-sm text-gray-400 hover:text-cyan-400 ${h.level === 3 ? 'pl-4' : 'font-medium'}`}>{h.text}</a>
                                        ))}
                                    </nav>
                                </details>
                            </div>
                        )}

                        <div className="prose prose-invert prose-lg max-w-none prose-p:text-gray-400 prose-p:leading-relaxed prose-p:text-base prose-blockquote:border-l-cyan-400 prose-blockquote:bg-cyan-400/5 prose-blockquote:rounded-r-xl prose-blockquote:py-1 prose-code:text-cyan-300 prose-code:bg-white/5 prose-code:rounded prose-code:px-1 prose-pre:bg-[#0f0f0f] prose-pre:border prose-pre:border-white/10 prose-pre:rounded-2xl prose-a:text-cyan-400 prose-a:no-underline hover:prose-a:underline prose-strong:text-white">
                            {parts.map((part, i) => {
                                if (part.type === 'markdown') return <ReactMarkdown key={i} remarkPlugins={[remarkGfm]} components={components}>{part.content}</ReactMarkdown>;
                                if (part.type === 'video_player') {
                                    const vUrl = frontmatter.video_url;
                                    const cImg = frontmatter.cover_image || "https://images.unsplash.com/photo-1677442136019-21780ecad995?auto=format&fit=crop&q=80&w=1200";
                                    return (
                                        <div key={i} className="my-12 relative aspect-video rounded-[2.5rem] bg-neutral-900 overflow-hidden border border-white/10 shadow-2xl group">
                                            {vUrl ? <video src={vUrl.startsWith('http') ? vUrl : `${API_URL}${vUrl}`} poster={cImg} controls autoPlay loop muted playsInline className="w-full h-full object-cover" /> :
                                                <div className="relative w-full h-full">
                                                    <img src={cImg} className="w-full h-full object-cover opacity-40 blur-sm" alt="Fallback" />
                                                    <div className="absolute inset-0 flex flex-col items-center justify-center text-gray-500 gap-4">
                                                        <div className="w-16 h-16 rounded-full bg-cyan-500/20 flex items-center justify-center border border-cyan-500/30"><Video className="w-8 h-8 text-cyan-400 animate-pulse" /></div>
                                                        <p className="text-xs font-black uppercase tracking-[0.2em] text-cyan-400/80">Rendu Vidéo en cours...</p>
                                                    </div>
                                                </div>
                                            }
                                        </div>
                                    );
                                }
                                if (part.type === 'bento_multi') return <div key={i} className="my-10 grid grid-cols-1 sm:grid-cols-2 gap-4">{tools.slice(0, 2).map((t, idx) => <AffiliateBento key={idx} tool={resolveToolLink(t, dbAffiliates)} compact={true} />)}</div>;
                                if (part.type === 'bento') {
                                    const t = tools.find(x => x.id === part.toolId);
                                    return t ? <AffiliateBento key={i} tool={resolveToolLink(t, dbAffiliates)} compact={true} /> : null;
                                }
                                return null;
                            })}
                        </div>

                        {bentoData?.seo_tags?.length > 0 && (
                            <div className="mt-12 pt-6 border-t border-white/5 flex flex-wrap gap-2">
                                {bentoData.seo_tags.map((tag, i) => <span key={i} className="flex items-center gap-1 text-xs text-gray-500 bg-white/5 border border-white/8 px-3 py-1.5 rounded-full"><Tag className="w-3 h-3" /> {tag}</span>)}
                            </div>
                        )}
                    </article>
                </div>
            </div>

            <footer className="mt-16 py-10 border-t border-white/5 text-center">
                <p className="max-w-2xl mx-auto text-[10px] text-gray-500 mb-6 px-4">Certains liens sur ce site sont des liens d'affiliation. Le Dev Masto reçoit une commission pour financer les serveurs.</p>
                <div className="text-gray-600 text-xs tracking-widest uppercase">CrewAI972 © 2026 • Martinique</div>
            </footer>
        </div>
    );
};

export default BlogPost;
