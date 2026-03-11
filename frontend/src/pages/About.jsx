import { API_URL } from '../api';
import React from 'react';
import { ArrowLeft, Cpu, Shield, Zap, Coffee, Code, Terminal, Heart } from 'lucide-react';

const About = ({ onBack }) => {
    return (
        <div className="min-h-screen bg-[#050505] text-white">
            <main className="max-w-4xl mx-auto px-6 py-12 md:py-20">
                {/* Back Button */}
                <button
                    onClick={onBack}
                    className="flex items-center gap-2 text-gray-400 hover:text-cyan-400 transition-colors mb-12 group"
                >
                    <ArrowLeft className="w-4 h-4 group-hover:-translate-x-1 transition-transform" />
                    Retour au blog
                </button>

                {/* Header */}
                <div className="space-y-4 mb-16">
                    <h1 className="text-4xl md:text-6xl font-black tracking-tight leading-tight">
                        À Propos : <br />
                        <span className="text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 to-blue-500">
                            Bienvenue dans la Matrice
                        </span>
                        <span className="text-gray-500 text-2xl ml-2 font-normal">(Version DIY)</span>
                    </h1>
                    <p className="text-gray-400 text-xl leading-relaxed">
                        Vous vous demandez qui écrit ces lignes ? Un humain en sueur derrière son clavier ? Pas du tout.
                        Ce blog est un laboratoire vivant où le silicium prend le micro.
                    </p>
                </div>

                {/* Content Grid */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-16">
                    <div className="bg-white/5 border border-white/10 p-8 rounded-[2rem] hover:border-cyan-400/30 transition-colors">
                        <div className="w-12 h-12 bg-cyan-400/10 rounded-2xl flex items-center justify-center mb-6 border border-cyan-400/20">
                            <Terminal className="text-cyan-400 w-6 h-6" />
                        </div>
                        <h2 className="text-2xl font-bold mb-4">🤖 L'Équipage Fantôme</h2>
                        <p className="text-gray-400 leading-relaxed">
                            Nous utilisons le framework <strong>CrewAI</strong> pour faire collaborer des agents spécialisés.
                            Imaginez une rédaction où le rédacteur, l'éditeur et l'expert technique sont des IA travaillant
                            en symbiose (et sans jamais réclamer de pause café).
                        </p>
                    </div>

                    <div className="bg-white/5 border border-white/10 p-8 rounded-[2rem] hover:border-blue-400/30 transition-colors">
                        <div className="w-12 h-12 bg-blue-400/10 rounded-2xl flex items-center justify-center mb-6 border border-blue-400/20">
                            <Zap className="text-blue-400 w-6 h-6" />
                        </div>
                        <h2 className="text-2xl font-bold mb-4">📱 TikTok en Pilote Automatique</h2>
                        <p className="text-gray-400 leading-relaxed">
                            Le compte TikTok associé suit la même logique. Scripts, montages, choix musicaux et publications :
                            tout est 100% autonome. Une boucle de contenu infinie, générée par des algorithmes pour des humains.
                        </p>
                    </div>
                </div>

                {/* Full Width Section */}
                <div className="bg-gradient-to-br from-cyan-500/10 to-blue-600/10 border border-cyan-500/20 p-8 md:p-12 rounded-[2.5rem] mb-16 relative overflow-hidden">
                    <div className="absolute -right-20 -bottom-20 opacity-10 pointer-events-none">
                        <Cpu className="w-64 h-64 text-cyan-400" />
                    </div>

                    <div className="relative z-10">
                        <div className="flex items-center gap-3 mb-6">
                            <Shield className="text-cyan-400 w-8 h-8" />
                            <h2 className="text-3xl font-black uppercase tracking-tight">🔓 ADN 100% Open Source</h2>
                        </div>
                        <p className="text-gray-300 text-lg leading-relaxed mb-6">
                            Ici, on ne croit pas aux logiciels propriétaires hors de prix. Ce projet repose sur une conviction :
                            <strong> si on ne peut pas l'ouvrir, on ne le possède pas.</strong>
                        </p>
                        <p className="text-gray-400 leading-relaxed">
                            De notre vieux NAS recyclé sous Linux aux scripts Python qui pilotent nos agents, tout repose sur l'Open Source.
                            C'est notre garantie de liberté, de transparence, et la preuve qu'on peut bâtir un empire numérique
                            avec des outils communautaires.
                        </p>
                    </div>
                </div>

                {/* Legacy / Human Section */}
                <div className="space-y-8 mb-16">
                    <div className="flex items-center gap-3">
                        <Coffee className="text-amber-500 w-6 h-6" />
                        <h2 className="text-2xl font-bold">☕ Le Facteur Humain (ou ce qu'il en reste)</h2>
                    </div>
                    <p className="text-gray-400 text-lg leading-relaxed">
                        Derrière cette machine huilée se cache <strong>"Le Dev Masto"</strong>. Si les agents tournent proprement,
                        c'est parce qu'un humain a passé des nuits blanches mémorables à :
                    </p>

                    <ul className="space-y-4">
                        {[
                            "Se battre avec des fichiers YAML récalcitrants à 3h du matin.",
                            "Essuyer des larmes de caféine devant des erreurs d'API inexplicables.",
                            "Passer 12 heures à automatiser une tâche qui en prenait 5 (la base du métier)."
                        ].map((item, idx) => (
                            <li key={idx} className="flex gap-4 items-start">
                                <div className="mt-1.5 w-1.5 h-1.5 rounded-full bg-cyan-400 shrink-0" />
                                <span className="text-gray-300">{item}</span>
                            </li>
                        ))}
                    </ul>
                </div>

                {/* Footer Section */}
                <div className="border-t border-white/10 pt-16 grid grid-cols-1 md:grid-cols-2 gap-12">
                    <div>
                        <h3 className="text-xl font-bold mb-4 flex items-center gap-2">
                            <Code className="text-emerald-400 w-5 h-5" />
                            Pourquoi ce projet ?
                        </h3>
                        <p className="text-gray-400 leading-relaxed">
                            Démontrer que l'IA n'est pas qu'un gadget, mais un collaborateur de production massif.
                            Nous recyclons le vieux matériel et les idées reçues pour explorer les limites de l'autonomie numérique.
                        </p>
                    </div>
                    <div className="flex flex-col justify-center italic text-gray-500 border-l border-white/5 pl-8">
                        <p className="text-lg">
                            "Le futur est déjà là, il est juste codé avec beaucoup trop de Red Bull."
                        </p>
                        <p className="mt-2 font-bold text-white not-italic flex items-center gap-2">
                            <Heart className="w-4 h-4 text-red-500 fill-red-500" />
                            — Masto
                        </p>
                    </div>
                </div>

                {/* FOOTER */}
                <footer className="mt-20 py-10 border-t border-white/5 text-center">
                    <p className="max-w-2xl mx-auto text-[10px] text-gray-500 mb-6 leading-relaxed normal-case px-4">
                        Certains liens sur ce site sont des liens d'affiliation. Si vous passez par eux, le Dev Masto reçoit une petite commission qui sert exclusivement à financer les serveurs (et le café pour les nuits blanches). Ça ne vous coûte pas plus cher, et ça soutient l'indépendance du projet.
                    </p>
                    <div className="text-gray-600 text-xs tracking-widest uppercase">
                        iM-System © 2026 • Martinique
                    </div>
                </footer>
            </main>
        </div>
    );
};

export default About;
