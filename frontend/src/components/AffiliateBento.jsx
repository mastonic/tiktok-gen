import { API_URL } from '../api';
import React from 'react';
import { ExternalLink, Zap, Mic, Video, Server, BookOpen, Cpu, Cloud } from 'lucide-react';

const categoryIcons = {
    'Voice IA': Mic,
    'Video Gen': Video,
    'Cloud Hosting': Server,
    'Prompt Engineering': BookOpen,
    'GPU Cloud': Cpu,
    'Cloud VPS': Cloud,
};

/**
 * AffiliateBento
 * Carte affilié premium pour affichage inline dans les articles de blog.
 * Props:
 *   - tool: { id, name, category, description, cta, link, gradient, relevance_score }
 *   - compact: boolean (mode inline dans l'article vs pleine largeur)
 */
const AffiliateBento = ({ tool, compact = false }) => {
    if (!tool) return null;
    const Icon = categoryIcons[tool.category] || Zap;
    const gradient = tool.gradient || 'from-cyan-400 to-emerald-400';

    if (compact) {
        // Mode inline — version "bande" horizontale dans le flux de l'article
        return (
            <div className="my-8 p-5 rounded-2xl bg-[#0f0f0f] border border-white/8 flex items-center gap-5 hover:border-white/15 transition-all duration-300 group">
                {/* Icon */}
                <div className={`flex-shrink-0 p-3 rounded-xl bg-gradient-to-br ${gradient} opacity-90`}>
                    <Icon className="w-6 h-6 text-black" />
                </div>

                {/* Info */}
                <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-0.5">
                        <span className="font-bold text-white text-base">{tool.name}</span>
                        <span className="text-[10px] font-bold uppercase tracking-widest text-amber-400 bg-amber-400/10 border border-amber-400/20 px-2 py-0.5 rounded-full">
                            ⚡ IA Recommandée
                        </span>
                    </div>
                    <p className="text-gray-500 text-sm truncate">{tool.description}</p>
                </div>

                {/* CTA */}
                <a
                    href={tool.link || '#'}
                    target="_blank"
                    rel="noopener noreferrer"
                    className={`flex-shrink-0 flex items-center gap-2 px-5 py-2.5 rounded-xl bg-gradient-to-r ${gradient} text-black font-bold text-sm hover:brightness-110 hover:scale-105 transition-all active:scale-95 whitespace-nowrap`}
                >
                    {tool.cta || 'Tester'}
                    <ExternalLink className="w-3.5 h-3.5" />
                </a>
            </div>
        );
    }

    // Mode full card (grille)
    return (
        <div className="bg-[#0f0f0f] border border-white/5 p-6 rounded-[2rem] flex flex-col justify-between hover:border-white/20 transition-all duration-300">
            <div className="flex justify-between items-start mb-6">
                <div className={`p-4 rounded-2xl bg-gradient-to-br ${gradient} border border-white/10`}
                    style={{ background: `linear-gradient(135deg, rgba(8,145,178,0.15), rgba(5,150,105,0.15))` }}>
                    <Icon className="w-6 h-6 text-white" />
                </div>
                <div className="flex items-center gap-1 bg-white/5 px-3 py-1 rounded-full border border-white/10">
                    <Zap className="w-3 h-3 text-amber-400 fill-amber-400" />
                    <span className="text-[10px] font-bold uppercase tracking-widest text-amber-400">IA Recommandée</span>
                </div>
            </div>

            <div className="mb-6">
                <h3 className="text-xl font-bold mb-1 text-white">{tool.name}</h3>
                <p className="text-gray-500 text-sm">{tool.category}</p>
                {tool.description && (
                    <p className="text-gray-600 text-xs mt-2 leading-relaxed">{tool.description}</p>
                )}
            </div>

            <a
                href={tool.link || '#'}
                target="_blank"
                rel="noopener noreferrer"
                className={`w-full py-4 rounded-2xl bg-gradient-to-r ${gradient} text-black font-bold flex items-center justify-center gap-2 hover:brightness-110 transition-all active:scale-95`}
            >
                {tool.cta || 'Essayer'} <ExternalLink className="w-4 h-4" />
            </a>
        </div>
    );
};

export default AffiliateBento;
