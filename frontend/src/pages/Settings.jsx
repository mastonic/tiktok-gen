import React, { useState, useEffect } from 'react';
import { Card, Button, Badge } from '../components/ui';
import { Save, Shield, Bell, Key, Database, Globe, Loader2, AlertCircle, TriangleAlert, DollarSign, Plus, Trash2, ExternalLink } from 'lucide-react';

const Settings = () => {
    const [config, setConfig] = useState({
        system_name: "Mission Control",
        environment: "Production (Live)",
        strict_mode: true,
        debug_logging: false,
        access_token: "",
        allowed_ips: "*",
        openai_key: "",
        gemini_key: "",
        fal_key: "",
        stability_key: "",
        elevenlabs_key: "",
        auto_cleanup_days: 30,
        discord_webhook: "",
        telegram_token: "",
        telegram_chat_id: "",
        enable_alerts: true
    });
    const [isSaving, setIsSaving] = useState(false);
    const [activeTab, setActiveTab] = useState("General");
    const [isLoading, setIsLoading] = useState(true);
    const [affiliates, setAffiliates] = useState([]);
    const [newAffiliate, setNewAffiliate] = useState({ name: '', category: '', description: '', cta: 'Tester Gratuitement', link: '', gradient: 'from-cyan-400 to-emerald-400', reconciliation_keywords: '' });
    const [addingAffiliate, setAddingAffiliate] = useState(false);
    const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:5656';

    const fetchConfig = async () => {
        try {
            const response = await fetch(`${apiUrl}/api/system/config`);
            if (response.ok) {
                const data = await response.json();
                setConfig(prev => ({ ...prev, ...data }));
            }
        } catch (error) {
            console.error("Failed to fetch settings:", error);
        } finally {
            setIsLoading(false);
        }
    };

    const fetchAffiliates = async () => {
        try {
            const res = await fetch(`${apiUrl}/api/affiliates`);
            if (res.ok) setAffiliates(await res.json());
        } catch (e) { console.error(e); }
    };

    useEffect(() => {
        fetchConfig();
        fetchAffiliates();
    }, []);

    const handleSave = async () => {
        setIsSaving(true);
        try {
            await fetch(`${apiUrl}/api/system/config`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(config)
            });
        } catch (error) {
            console.error("Failed to save settings:", error);
            alert("Erreur lors de la sauvegarde.");
        } finally {
            setIsSaving(false);
        }
    };

    const handleAddAffiliate = async () => {
        if (!newAffiliate.name || !newAffiliate.link) return alert("Nom et URL requis.");
        setAddingAffiliate(true);
        try {
            await fetch(`${apiUrl}/api/affiliates`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(newAffiliate)
            });
            setNewAffiliate({ name: '', category: '', description: '', cta: 'Tester Gratuitement', link: '', gradient: 'from-cyan-400 to-emerald-400', reconciliation_keywords: '' });
            fetchAffiliates();
        } catch (e) { console.error(e); }
        finally { setAddingAffiliate(false); }
    };

    const handleDeleteAffiliate = async (id) => {
        if (!confirm('Supprimer ce lien affilié ?')) return;
        await fetch(`${apiUrl}/api/affiliates/${id}`, { method: 'DELETE' });
        fetchAffiliates();
    };

    const handlePurge = async () => {
        if (!confirm("⚠️ DANGER : Est-tu sûr de vouloir purger TOUT le pipeline (Scripts + Historique) ? Cette action est irréversible.")) return;

        try {
            const response = await fetch(`${apiUrl}/api/system/purge-pipeline`, { method: 'POST' });
            if (response.ok) {
                alert("Pipeline purgé avec succès.");
            }
        } catch (error) {
            console.error("Purge failed:", error);
        }
    };

    if (isLoading) {
        return (
            <div className="flex items-center justify-center min-h-[400px]">
                <Loader2 className="w-8 h-8 text-cyan-500 animate-spin" />
            </div>
        );
    }

    return (
        <div className="space-y-6">
            <header className="mb-8 flex justify-between items-end">
                <div>
                    <h1 className="text-3xl font-bold text-white tracking-tight mb-1">System Settings</h1>
                    <p className="text-gray-400">Manage global configuration, security, and integrations.</p>
                </div>
                <Button
                    variant="primary"
                    className="flex items-center gap-2 shadow-lg shadow-cyan-900/20 px-6"
                    onClick={handleSave}
                    disabled={isSaving}
                >
                    {isSaving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
                    {isSaving ? "Saving..." : "Save Changes"}
                </Button>
            </header>

            <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                <nav className="md:col-span-1 space-y-2">
                    <SettingNav icon={Globe} title="General" active={activeTab === "General"} onClick={() => setActiveTab("General")} />
                    <SettingNav icon={Shield} title="Security & Access" active={activeTab === "Security"} onClick={() => setActiveTab("Security")} />
                    <SettingNav icon={Key} title="API Keys" active={activeTab === "API Keys"} onClick={() => setActiveTab("API Keys")} />
                    <SettingNav icon={Database} title="Data Management" active={activeTab === "Data"} onClick={() => setActiveTab("Data")} />
                    <SettingNav icon={Bell} title="Notifications" active={activeTab === "Notifications"} onClick={() => setActiveTab("Notifications")} />
                    <SettingNav icon={DollarSign} title="Monétisation" active={activeTab === "Monetisation"} onClick={() => setActiveTab("Monetisation")} />
                </nav>

                <Card className="md:col-span-3 space-y-8 bg-navy-900/40 backdrop-blur-sm border-gray-800">
                    {activeTab === "General" && (
                        <div className="space-y-8 animate-in fade-in duration-300">
                            <section className="space-y-6">
                                <h3 className="text-lg font-semibold text-white border-b border-gray-800 pb-4 flex items-center gap-2">
                                    <Globe className="w-5 h-5 text-cyan-400" />
                                    Instance Profile
                                </h3>
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                    <div className="space-y-2">
                                        <label className="text-xs font-mono text-gray-500 uppercase tracking-widest">System Name</label>
                                        <input
                                            type="text"
                                            value={config.system_name || ''}
                                            onChange={(e) => setConfig({ ...config, system_name: e.target.value })}
                                            className="w-full bg-navy-900 border border-gray-700/50 rounded-xl p-3 text-sm text-gray-200 focus:outline-none focus:ring-2 focus:ring-cyan-500/30 transition-all font-medium"
                                        />
                                    </div>
                                    <div className="space-y-2">
                                        <label className="text-xs font-mono text-gray-500 uppercase tracking-widest">Environment</label>
                                        <select
                                            value={config.environment || 'Production (Live)'}
                                            onChange={(e) => setConfig({ ...config, environment: e.target.value })}
                                            className="w-full bg-navy-900 border border-gray-700/50 rounded-xl p-3 text-sm text-gray-200 focus:outline-none focus:ring-2 focus:ring-cyan-500/30 transition-all cursor-pointer"
                                        >
                                            <option>Production (Live)</option>
                                            <option>Staging</option>
                                            <option>Development</option>
                                        </select>
                                    </div>
                                </div>
                            </section>

                            <section className="space-y-6">
                                <h3 className="text-lg font-semibold text-white border-b border-gray-800 pb-4 flex items-center gap-2">
                                    <Shield className="w-5 h-5 text-emerald-400" />
                                    Global Constraints
                                </h3>
                                <div className="space-y-4">
                                    <ToggleSetting
                                        title="Enforce Strict Mode"
                                        description="Require human approval for all content segments before final assembly."
                                        active={config.strict_mode}
                                        onClick={() => setConfig({ ...config, strict_mode: !config.strict_mode })}
                                    />
                                    <ToggleSetting
                                        title="Debug Logging"
                                        description="Persist verbose Swarm Chat logs and internal agent traces."
                                        active={config.debug_logging}
                                        onClick={() => setConfig({ ...config, debug_logging: !config.debug_logging })}
                                    />
                                </div>
                            </section>
                        </div>
                    )}

                    {activeTab === "Security" && (
                        <section className="space-y-6 animate-in fade-in duration-300">
                            <h3 className="text-lg font-semibold text-white border-b border-gray-800 pb-4 flex items-center gap-2">
                                <Shield className="w-5 h-5 text-cyan-400" />
                                Security & Access Control
                            </h3>
                            <div className="space-y-6">
                                <div className="space-y-2">
                                    <label className="text-xs font-mono text-gray-500 uppercase tracking-widest">Master Access Token</label>
                                    <input
                                        type="password"
                                        value={config.access_token || ''}
                                        onChange={(e) => setConfig({ ...config, access_token: e.target.value })}
                                        className="w-full bg-navy-900 border border-gray-700/50 rounded-xl p-3 text-sm text-gray-200 focus:outline-none focus:ring-2 focus:ring-cyan-500/30 transition-all font-mono"
                                    />
                                </div>
                                <div className="space-y-2">
                                    <label className="text-xs font-mono text-gray-500 uppercase tracking-widest">Allowed IP Patterns</label>
                                    <input
                                        type="text"
                                        value={config.allowed_ips || ''}
                                        onChange={(e) => setConfig({ ...config, allowed_ips: e.target.value })}
                                        className="w-full bg-navy-900 border border-gray-700/50 rounded-xl p-3 text-sm text-gray-200 focus:outline-none focus:ring-2 focus:ring-cyan-500/30 transition-all font-medium"
                                        placeholder="Comma separated IPs or * for any"
                                    />
                                </div>
                            </div>
                        </section>
                    )}

                    {activeTab === "API Keys" && (
                        <section className="space-y-6 animate-in fade-in duration-300">
                            <h3 className="text-lg font-semibold text-white border-b border-gray-800 pb-4 flex items-center gap-2">
                                <Key className="w-5 h-5 text-amber-400" />
                                Integrated LLM & Media Services
                            </h3>
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                <ApiKeyInput label="OpenAI API Key" value={config.openai_key} onChange={(val) => setConfig({ ...config, openai_key: val })} />
                                <ApiKeyInput label="Gemini API Key" value={config.gemini_key} onChange={(val) => setConfig({ ...config, gemini_key: val })} />
                                <ApiKeyInput label="Fal.ai Key" value={config.fal_key} onChange={(val) => setConfig({ ...config, fal_key: val })} />
                                <ApiKeyInput label="ElevenLabs Key" value={config.elevenlabs_key} onChange={(val) => setConfig({ ...config, elevenlabs_key: val })} />
                            </div>
                        </section>
                    )}

                    {activeTab === "Data" && (
                        <div className="space-y-8 animate-in fade-in duration-300">
                            <section className="space-y-6">
                                <h3 className="text-lg font-semibold text-white border-b border-gray-800 pb-4 flex items-center gap-2">
                                    <Database className="w-5 h-5 text-indigo-400" />
                                    Data Lifecycles
                                </h3>
                                <div className="space-y-2">
                                    <label className="text-xs font-mono text-gray-500 uppercase tracking-widest">Auto-Cleanup Threshold (Days)</label>
                                    <input
                                        type="number"
                                        value={config.auto_cleanup_days || 30}
                                        onChange={(e) => setConfig({ ...config, auto_cleanup_days: parseInt(e.target.value) || 0 })}
                                        className="w-full bg-navy-900 border border-gray-700/50 rounded-xl p-3 text-sm text-gray-200 focus:outline-none focus:ring-2 focus:ring-cyan-500/30 transition-all font-medium"
                                    />
                                </div>
                            </section>

                            <section className="space-y-6">
                                <h3 className="text-lg font-semibold text-red-500 border-b border-gray-800 pb-4 flex items-center gap-2">
                                    <TriangleAlert className="w-5 h-5" />
                                    Danger Zone
                                </h3>
                                <div className="p-6 rounded-xl border border-red-900/40 bg-red-950/20 flex flex-col md:flex-row justify-between items-center gap-6">
                                    <div>
                                        <div className="font-bold text-red-400 mb-1">Purge Pipeline Infrastructure</div>
                                        <div className="text-xs text-gray-500 leading-relaxed">This will delete all current Inbox scripts and run history. Agent configurations and models will be preserved.</div>
                                    </div>
                                    <Button variant="danger" className="text-sm font-bold min-w-[160px] h-11 shadow-xl shadow-red-950/40" onClick={handlePurge}>
                                        Purge All Data
                                    </Button>
                                </div>
                            </section>
                        </div>
                    )}

                    {activeTab === "Notifications" && (
                        <section className="space-y-6 animate-in fade-in duration-300">
                            <h3 className="text-lg font-semibold text-white border-b border-gray-800 pb-4 flex items-center gap-2">
                                <Bell className="w-5 h-5 text-fuchsia-400" />
                                Alert Channels
                            </h3>
                            <div className="space-y-6">
                                <ToggleSetting
                                    title="System Alerts"
                                    description="Enable push notifications for critical errors and quota limits."
                                    active={config.enable_alerts}
                                    onClick={() => setConfig({ ...config, enable_alerts: !config.enable_alerts })}
                                />
                                <div className="space-y-2">
                                    <label className="text-xs font-mono text-gray-500 uppercase tracking-widest">Discord Webhook URL</label>
                                    <input
                                        type="text"
                                        value={config.discord_webhook || ''}
                                        onChange={(e) => setConfig({ ...config, discord_webhook: e.target.value })}
                                        className="w-full bg-navy-900 border border-gray-700/50 rounded-xl p-3 text-sm text-gray-200 focus:outline-none focus:ring-2 focus:ring-cyan-500/30 transition-all font-mono"
                                        placeholder="https://discord.com/api/webhooks/..."
                                    />
                                </div>
                                <div className="space-y-2">
                                    <label className="text-xs font-mono text-gray-500 uppercase tracking-widest">Telegram Bot Token</label>
                                    <input
                                        type="password"
                                        value={config.telegram_token || ''}
                                        onChange={(e) => setConfig({ ...config, telegram_token: e.target.value })}
                                        className="w-full bg-navy-900 border border-gray-700/50 rounded-xl p-3 text-sm text-gray-200 focus:outline-none focus:ring-2 focus:ring-cyan-500/30 transition-all font-mono"
                                        placeholder="bot123456:ABC-DEF..."
                                    />
                                </div>
                                <div className="space-y-2">
                                    <label className="text-xs font-mono text-gray-500 uppercase tracking-widest">Telegram Chat ID</label>
                                    <input
                                        type="text"
                                        value={config.telegram_chat_id || ''}
                                        onChange={(e) => setConfig({ ...config, telegram_chat_id: e.target.value })}
                                        className="w-full bg-navy-900 border border-gray-700/50 rounded-xl p-3 text-sm text-gray-200 focus:outline-none focus:ring-2 focus:ring-cyan-500/30 transition-all font-mono"
                                        placeholder="123456789"
                                    />
                                </div>
                            </div>
                        </section>
                    )}

                    {activeTab === "Monetisation" && (
                        <section className="space-y-6 animate-in fade-in duration-300">
                            <h3 className="text-lg font-semibold text-white border-b border-gray-800 pb-4 flex items-center gap-2">
                                <DollarSign className="w-5 h-5 text-emerald-400" />
                                Liens d'Affiliation
                            </h3>

                            {/* Formulaire Ajout */}
                            <div className="p-5 bg-navy-900/60 border border-emerald-900/40 rounded-2xl space-y-4">
                                <p className="text-sm font-semibold text-emerald-400">➕ Ajouter un Lien Affilié</p>
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                                    <input placeholder="Nom (ex: ElevenLabs)" value={newAffiliate.name} onChange={e => setNewAffiliate({ ...newAffiliate, name: e.target.value })} className="bg-navy-900 border border-gray-700/50 rounded-xl p-3 text-sm text-gray-200 focus:outline-none focus:ring-2 focus:ring-emerald-500/30 transition-all" />
                                    <input placeholder="Catégorie (ex: Voice IA, Cloud Hosting)" value={newAffiliate.category} onChange={e => setNewAffiliate({ ...newAffiliate, category: e.target.value })} className="bg-navy-900 border border-gray-700/50 rounded-xl p-3 text-sm text-gray-200 focus:outline-none focus:ring-2 focus:ring-emerald-500/30 transition-all" />
                                    <input placeholder="URL Affilié" value={newAffiliate.link} onChange={e => setNewAffiliate({ ...newAffiliate, link: e.target.value })} className="bg-navy-900 border border-gray-700/50 rounded-xl p-3 text-sm text-gray-200 font-mono focus:outline-none focus:ring-2 focus:ring-emerald-500/30 transition-all" />
                                    <input placeholder="Mots-clés (ex: voice, tts, audio)" value={newAffiliate.reconciliation_keywords} onChange={e => setNewAffiliate({ ...newAffiliate, reconciliation_keywords: e.target.value })} className="bg-navy-900 border border-gray-700/50 rounded-xl p-3 text-sm text-gray-200 focus:outline-none focus:ring-2 focus:ring-emerald-500/30 transition-all" />
                                    <input placeholder="Description courte" value={newAffiliate.description} onChange={e => setNewAffiliate({ ...newAffiliate, description: e.target.value })} className="bg-navy-900 border border-gray-700/50 rounded-xl p-3 text-sm text-gray-200 focus:outline-none focus:ring-2 focus:ring-emerald-500/30 transition-all md:col-span-2" />
                                </div>
                                <button onClick={handleAddAffiliate} disabled={addingAffiliate} className="flex items-center gap-2 bg-emerald-600 hover:bg-emerald-500 text-white font-bold py-2.5 px-5 rounded-xl transition-all text-sm disabled:opacity-50">
                                    {addingAffiliate ? <Loader2 className="w-4 h-4 animate-spin" /> : <Plus className="w-4 h-4" />}
                                    Ajouter
                                </button>
                            </div>

                            {/* Liste des affiliés */}
                            <div className="space-y-3">
                                {affiliates.length === 0 && <p className="text-gray-500 text-sm text-center py-4">Aucun lien affilié configuré.</p>}
                                {affiliates.map(a => (
                                    <div key={a.id} className="flex items-center justify-between p-4 bg-navy-900/60 border border-gray-800 rounded-xl hover:border-gray-700 transition-colors">
                                        <div className="flex-1 min-w-0">
                                            <div className="font-semibold text-gray-200 flex items-center gap-2">
                                                {a.name}
                                                <span className="text-xs text-gray-500 bg-gray-800 px-2 py-0.5 rounded-full">{a.category}</span>
                                            </div>
                                            <div className="text-xs text-gray-500 mt-1 font-mono truncate">{a.link}</div>
                                            {a.reconciliation_keywords && <div className="text-xs text-emerald-600 mt-1">🔑 {a.reconciliation_keywords}</div>}
                                        </div>
                                        <div className="flex items-center gap-2 ml-4 shrink-0">
                                            <a href={a.link} target="_blank" rel="noreferrer" className="p-2 text-gray-500 hover:text-cyan-400 transition-colors">
                                                <ExternalLink className="w-4 h-4" />
                                            </a>
                                            <button onClick={() => handleDeleteAffiliate(a.id)} className="p-2 text-gray-500 hover:text-red-400 transition-colors">
                                                <Trash2 className="w-4 h-4" />
                                            </button>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </section>
                    )}
                </Card>
            </div>
        </div>
    );
};

const SettingNav = ({ icon: Icon, title, active, onClick }) => (
    <button
        onClick={onClick}
        className={`w-full flex items-center gap-3 p-4 rounded-xl transition-all text-sm font-semibold border ${active
            ? 'bg-cyan-950/30 text-cyan-400 border-cyan-500/40 shadow-xl shadow-cyan-950/20 active:scale-95'
            : 'text-gray-400 border-transparent hover:bg-navy-800 hover:text-gray-200'
            }`}>
        <Icon className="w-5 h-5" /> {title}
    </button>
);

const ToggleSetting = ({ title, description, active, onClick }) => (
    <div className="flex justify-between items-center p-4 rounded-xl bg-navy-900/60 border border-gray-800 transition-colors hover:border-gray-700">
        <div className="pr-8">
            <div className="font-semibold text-gray-200 mb-1">{title}</div>
            <div className="text-xs text-gray-500 leading-relaxed">{description}</div>
        </div>
        <div
            onClick={onClick}
            className={`w-12 h-6 rounded-full p-1 transition-all duration-300 cursor-pointer shrink-0 ${active ? 'bg-cyan-500 shadow-[0_0_12px_rgba(6,182,212,0.4)]' : 'bg-gray-700'}`}
        >
            <div className={`w-4 h-4 rounded-full bg-white transition-all duration-300 ${active ? 'translate-x-6' : 'translate-x-0'}`}></div>
        </div>
    </div>
);

const ApiKeyInput = ({ label, value, onChange }) => (
    <div className="space-y-2">
        <label className="text-xs font-mono text-gray-500 uppercase tracking-widest">{label}</label>
        <input
            type="password"
            value={value || ''}
            onChange={(e) => onChange(e.target.value)}
            className="w-full bg-navy-900 border border-gray-700/50 rounded-xl p-3 text-sm text-gray-200 focus:outline-none focus:ring-2 focus:ring-cyan-500/30 transition-all font-mono"
            placeholder="••••••••••••••••"
        />
    </div>
);

export default Settings;
