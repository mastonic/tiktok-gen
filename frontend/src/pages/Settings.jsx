import React, { useState, useEffect } from 'react';
import { Card, Button, Badge } from '../components/ui';
import { Save, Shield, Bell, Key, Database, Globe, Loader2, AlertTriangle } from 'lucide-react';

const Settings = () => {
    const [config, setConfig] = useState({
        system_name: "",
        environment: "Production (Live)",
        strict_mode: true,
        debug_logging: false
    });
    const [isSaving, setIsSaving] = useState(false);
    const [activeTab, setActiveTab] = useState("General");

    const fetchConfig = async () => {
        try {
            const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:5656';
            const response = await fetch(`${apiUrl}/api/system/config`);
            const data = await response.json();
            setConfig(data);
        } catch (error) {
            console.error("Failed to fetch settings:", error);
        }
    };

    useEffect(() => {
        fetchConfig();
    }, []);

    const handleSave = async () => {
        setIsSaving(true);
        try {
            const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:5656';
            await fetch(`${apiUrl}/api/system/config`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(config)
            });
            // Show success notification or feedback
        } catch (error) {
            console.error("Failed to save settings:", error);
        } finally {
            setIsSaving(false);
        }
    };

    const handlePurge = async () => {
        if (!confirm("⚠️ DANGER : Est-tu sûr de vouloir purger TOUT le pipeline (Scripts + Historique) ? Cette action est irréversible.")) return;

        try {
            const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:5656';
            const response = await fetch(`${apiUrl}/api/system/purge-pipeline`, { method: 'POST' });
            if (response.ok) {
                alert("Pipeline purgé avec succès.");
            }
        } catch (error) {
            console.error("Purge failed:", error);
        }
    };

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
                <div className="md:col-span-1 space-y-2">
                    <SettingNav icon={Globe} title="General" active={activeTab === "General"} onClick={() => setActiveTab("General")} />
                    <SettingNav icon={Shield} title="Security & Access" active={activeTab === "Security"} onClick={() => setActiveTab("Security")} />
                    <SettingNav icon={Key} title="API Keys" active={activeTab === "API Keys"} onClick={() => setActiveTab("API Keys")} />
                    <SettingNav icon={Database} title="Data Management" active={activeTab === "Data"} onClick={() => setActiveTab("Data")} />
                    <SettingNav icon={Bell} title="Notifications" active={activeTab === "Notifications"} onClick={() => setActiveTab("Notifications")} />
                </div>

                <Card className="md:col-span-3 space-y-8 bg-navy-900/40 backdrop-blur-sm border-gray-800">
                    {activeTab === "General" ? (
                        <>
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
                                            value={config.system_name}
                                            onChange={(e) => setConfig({ ...config, system_name: e.target.value })}
                                            className="w-full bg-navy-900 border border-gray-700/50 rounded-xl p-3 text-sm text-gray-200 focus:outline-none focus:ring-2 focus:ring-cyan-500/30 transition-all"
                                            placeholder="Ex: iM-System-01"
                                        />
                                    </div>
                                    <div className="space-y-2">
                                        <label className="text-xs font-mono text-gray-500 uppercase tracking-widest">Environment</label>
                                        <select
                                            value={config.environment}
                                            onChange={(e) => setConfig({ ...config, environment: e.target.value })}
                                            className="w-full bg-navy-900 border border-gray-700/50 rounded-xl p-3 text-sm text-gray-200 focus:outline-none focus:ring-2 focus:ring-cyan-500/30 transition-all appearance-none cursor-pointer"
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
                                    <div className="flex justify-between items-center p-4 rounded-xl bg-navy-900/60 border border-gray-800 transition-colors hover:border-gray-700">
                                        <div className="pr-8">
                                            <div className="font-semibold text-gray-200 mb-1">Enforce Strict Mode</div>
                                            <div className="text-xs text-gray-500 leading-relaxed">Require human approval for all content segments before they reach the final assembly stage.</div>
                                        </div>
                                        <Toggle active={config.strict_mode} onClick={() => setConfig({ ...config, strict_mode: !config.strict_mode })} />
                                    </div>

                                    <div className="flex justify-between items-center p-4 rounded-xl bg-navy-900/60 border border-gray-800 transition-colors hover:border-gray-700">
                                        <div className="pr-8">
                                            <div className="font-semibold text-gray-200 mb-1">Debug Logging</div>
                                            <div className="text-xs text-gray-500 leading-relaxed">Persist verbose Swarm Chat logs and internal agent traces. Recommended for troubleshooting only.</div>
                                        </div>
                                        <Toggle active={config.debug_logging} onClick={() => setConfig({ ...config, debug_logging: !config.debug_logging })} />
                                    </div>
                                </div>
                            </section>

                            <section className="space-y-6">
                                <h3 className="text-lg font-semibold text-red-400 border-b border-gray-800 pb-4 flex items-center gap-2">
                                    <AlertTriangle className="w-5 h-5 text-red-500" />
                                    Danger Zone
                                </h3>
                                <div className="p-6 rounded-xl border border-red-900/40 bg-red-950/20 flex flex-col md:flex-row justify-between items-center gap-4">
                                    <div>
                                        <div className="font-bold text-red-400 mb-1">Purge Pipeline Infrastructure</div>
                                        <div className="text-xs text-gray-500 leading-relaxed">This will delete all current Inbox scripts and run history. Agent configurations and models will be preserved.</div>
                                    </div>
                                    <Button variant="danger" className="text-sm font-bold px-6 py-2.5 shadow-2xl shadow-red-950/40" onClick={handlePurge}>
                                        Purge All Data
                                    </Button>
                                </div>
                            </section>
                        </>
                    ) : activeTab === "Security" ? (
                        <section className="space-y-6 animate-in fade-in slide-in-from-bottom-2 duration-300">
                            <h3 className="text-lg font-semibold text-white border-b border-gray-800 pb-4 flex items-center gap-2">
                                <Shield className="w-5 h-5 text-cyan-400" />
                                Security & Access Control
                            </h3>
                            <div className="space-y-6">
                                <div className="space-y-2">
                                    <label className="text-xs font-mono text-gray-500 uppercase tracking-widest">Master Access Token</label>
                                    <input
                                        type="password"
                                        value={config.access_token}
                                        onChange={(e) => setConfig({ ...config, access_token: e.target.value })}
                                        className="w-full bg-navy-900 border border-gray-700/50 rounded-xl p-3 text-sm text-gray-200 focus:outline-none focus:ring-2 focus:ring-cyan-500/30 transition-all font-mono"
                                    />
                                    <p className="text-[10px] text-gray-500 italic">Used for external API calls and remote agent synchronization.</p>
                                </div>
                                <div className="space-y-2">
                                    <label className="text-xs font-mono text-gray-500 uppercase tracking-widest">Allowed IP Patterns</label>
                                    <input
                                        type="text"
                                        value={config.allowed_ips}
                                        onChange={(e) => setConfig({ ...config, allowed_ips: e.target.value })}
                                        className="w-full bg-navy-900 border border-gray-700/50 rounded-xl p-3 text-sm text-gray-200 focus:outline-none focus:ring-2 focus:ring-cyan-500/30 transition-all"
                                        placeholder="Comma separated IPs or * for any"
                                    />
                                </div>
                            </div>
                        </section>
                    ) : activeTab === "API Keys" ? (
                        <section className="space-y-6 animate-in fade-in slide-in-from-bottom-2 duration-300">
                            <h3 className="text-lg font-semibold text-white border-b border-gray-800 pb-4 flex items-center gap-2">
                                <Key className="w-5 h-5 text-amber-400" />
                                Integrated LLM & Media Services
                            </h3>
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                <div className="space-y-2">
                                    <label className="text-xs font-mono text-gray-500 uppercase tracking-widest">OpenAI API Key</label>
                                    <input
                                        type="password"
                                        value={config.openai_key}
                                        onChange={(e) => setConfig({ ...config, openai_key: e.target.value })}
                                        className="w-full bg-navy-900 border border-gray-700/50 rounded-xl p-3 text-sm text-gray-200 focus:outline-none focus:ring-2 focus:ring-cyan-500/30 transition-all font-mono"
                                        placeholder="sk-..."
                                    />
                                </div>
                                <div className="space-y-2">
                                    <label className="text-xs font-mono text-gray-500 uppercase tracking-widest">Gemini API Key</label>
                                    <input
                                        type="password"
                                        value={config.gemini_key}
                                        onChange={(e) => setConfig({ ...config, gemini_key: e.target.value })}
                                        className="w-full bg-navy-900 border border-gray-700/50 rounded-xl p-3 text-sm text-gray-200 focus:outline-none focus:ring-2 focus:ring-cyan-500/30 transition-all font-mono"
                                    />
                                </div>
                                <div className="space-y-2">
                                    <label className="text-xs font-mono text-gray-500 uppercase tracking-widest">Fal.ai Key</label>
                                    <input
                                        type="password"
                                        value={config.fal_key}
                                        onChange={(e) => setConfig({ ...config, fal_key: e.target.value })}
                                        className="w-full bg-navy-900 border border-gray-700/50 rounded-xl p-3 text-sm text-gray-200 focus:outline-none focus:ring-2 focus:ring-cyan-500/30 transition-all font-mono"
                                    />
                                </div>
                                <div className="space-y-2">
                                    <label className="text-xs font-mono text-gray-500 uppercase tracking-widest">ElevenLabs Key</label>
                                    <input
                                        type="password"
                                        value={config.elevenlabs_key}
                                        onChange={(e) => setConfig({ ...config, elevenlabs_key: e.target.value })}
                                        className="w-full bg-navy-900 border border-gray-700/50 rounded-xl p-3 text-sm text-gray-200 focus:outline-none focus:ring-2 focus:ring-cyan-500/30 transition-all font-mono"
                                    />
                                </div>
                            </div>
                        </section>
                    ) : activeTab === "Data" ? (
                        <div className="space-y-8 animate-in fade-in slide-in-from-bottom-2 duration-300">
                            <section className="space-y-6">
                                <h3 className="text-lg font-semibold text-white border-b border-gray-800 pb-4 flex items-center gap-2">
                                    <Database className="w-5 h-5 text-indigo-400" />
                                    Data Lifecycles
                                </h3>
                                <div className="space-y-2">
                                    <label className="text-xs font-mono text-gray-500 uppercase tracking-widest">Auto-Cleanup Threshold (Days)</label>
                                    <input
                                        type="number"
                                        value={config.auto_cleanup_days}
                                        onChange={(e) => setConfig({ ...config, auto_cleanup_days: parseInt(e.target.value) })}
                                        className="w-full bg-navy-900 border border-gray-700/50 rounded-xl p-3 text-sm text-gray-200 focus:outline-none focus:ring-2 focus:ring-cyan-500/30 transition-all"
                                    />
                                    <p className="text-[10px] text-gray-500 italic">Automatically delete logs and media older than this period to save disk space.</p>
                                </div>
                            </section>

                            <section className="space-y-6">
                                <h3 className="text-lg font-semibold text-red-400 border-b border-gray-800 pb-4 flex items-center gap-2">
                                    <AlertTriangle className="w-5 h-5 text-red-500" />
                                    Danger Zone
                                </h3>
                                <div className="p-6 rounded-xl border border-red-900/40 bg-red-950/20 flex flex-col md:flex-row justify-between items-center gap-4">
                                    <div>
                                        <div className="font-bold text-red-400 mb-1">Purge Pipeline Infrastructure</div>
                                        <div className="text-xs text-gray-500 leading-relaxed">This will delete all current Inbox scripts and run history. Agent configurations and models will be preserved.</div>
                                    </div>
                                    <Button variant="danger" className="text-sm font-bold px-6 py-2.5 shadow-2xl shadow-red-950/40" onClick={handlePurge}>
                                        Purge All Data
                                    </Button>
                                </div>
                            </section>
                        </div>
                    ) : activeTab === "Notifications" ? (
                        <section className="space-y-6 animate-in fade-in slide-in-from-bottom-2 duration-300">
                            <h3 className="text-lg font-semibold text-white border-b border-gray-800 pb-4 flex items-center gap-2">
                                <Bell className="w-5 h-5 text-fuchsia-400" />
                                Alert Channels
                            </h3>
                            <div className="space-y-6">
                                <div className="flex justify-between items-center p-4 rounded-xl bg-navy-900/60 border border-gray-800">
                                    <div className="pr-8">
                                        <div className="font-semibold text-gray-200 mb-1">System Alerts</div>
                                        <div className="text-xs text-gray-500 leading-relaxed">Enable push notifications for critical errors and quota limits.</div>
                                    </div>
                                    <Toggle active={config.enable_alerts} onClick={() => setConfig({ ...config, enable_alerts: !config.enable_alerts })} />
                                </div>
                                <div className="space-y-2">
                                    <label className="text-xs font-mono text-gray-500 uppercase tracking-widest">Discord Webhook URL</label>
                                    <input
                                        type="text"
                                        value={config.discord_webhook}
                                        onChange={(e) => setConfig({ ...config, discord_webhook: e.target.value })}
                                        className="w-full bg-navy-900 border border-gray-700/50 rounded-xl p-3 text-sm text-gray-200 focus:outline-none focus:ring-2 focus:ring-cyan-500/30 transition-all font-mono"
                                        placeholder="https://discord.com/api/webhooks/..."
                                    />
                                </div>
                                <div className="space-y-2">
                                    <label className="text-xs font-mono text-gray-500 uppercase tracking-widest">Telegram Bot Token</label>
                                    <input
                                        type="password"
                                        value={config.telegram_token}
                                        onChange={(e) => setConfig({ ...config, telegram_token: e.target.value })}
                                        className="w-full bg-navy-900 border border-gray-700/50 rounded-xl p-3 text-sm text-gray-200 focus:outline-none focus:ring-2 focus:ring-cyan-500/30 transition-all font-mono"
                                    />
                                </div>
                            </div>
                        </section>
                    ) : null}
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

const Toggle = ({ active, onClick }) => (
    <div
        onClick={onClick}
        className={`w-12 h-6 rounded-full p-1 transition-all duration-300 cursor-pointer ${active ? 'bg-cyan-500 shadow-[0_0_12px_rgba(6,182,212,0.4)]' : 'bg-gray-700'}`}
    >
        <div className={`w-4 h-4 rounded-full bg-white transition-all duration-300 ${active ? 'translate-x-6' : 'translate-x-0'}`}></div>
    </div>
);

export default Settings;
