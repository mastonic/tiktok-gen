import React from 'react';
import { Card, Button, Badge } from '../components/ui';
import { Save, Shield, Bell, Key, Database, Globe } from 'lucide-react';

const Settings = () => {
    return (
        <div className="space-y-6">
            <header className="mb-8 flex justify-between items-end">
                <div>
                    <h1 className="text-3xl font-bold text-white tracking-tight mb-1">System Settings</h1>
                    <p className="text-gray-400">Manage global configuration, security, and integrations.</p>
                </div>
                <Button variant="primary" className="flex items-center gap-2">
                    <Save className="w-4 h-4" /> Save Changes
                </Button>
            </header>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="space-y-2">
                    <SettingNav icon={Globe} title="General" active />
                    <SettingNav icon={Shield} title="Security & Access" />
                    <SettingNav icon={Key} title="API Keys" />
                    <SettingNav icon={Database} title="Data Management" />
                    <SettingNav icon={Bell} title="Notifications" />
                </div>

                <Card className="md:col-span-2 space-y-8">
                    <section className="space-y-4">
                        <h3 className="text-lg font-semibold text-white border-b border-gray-800 pb-2">Instance Profile</h3>

                        <div className="grid grid-cols-2 gap-4">
                            <div className="space-y-1">
                                <label className="text-xs font-semibold text-gray-400 uppercase">System Name</label>
                                <input type="text" defaultValue="Mission Control - Primary" className="w-full bg-navy-900 border border-gray-700 rounded-lg p-2.5 text-sm text-gray-200 focus:outline-none focus:border-cyan-500 transition-colors" />
                            </div>
                            <div className="space-y-1">
                                <label className="text-xs font-semibold text-gray-400 uppercase">Environment</label>
                                <select className="w-full bg-navy-900 border border-gray-700 rounded-lg p-2.5 text-sm text-gray-200 focus:outline-none focus:border-cyan-500 transition-colors">
                                    <option>Production (Live)</option>
                                    <option>Staging</option>
                                    <option>Development</option>
                                </select>
                            </div>
                        </div>
                    </section>

                    <section className="space-y-4">
                        <h3 className="text-lg font-semibold text-white border-b border-gray-800 pb-2">Global Constraints</h3>

                        <div className="space-y-4">
                            <div className="flex justify-between items-center p-3 rounded-xl bg-navy-900/50 border border-gray-800">
                                <div>
                                    <div className="font-medium text-gray-200">Enforce Strict Mode</div>
                                    <div className="text-xs text-gray-500">Require approval for all content before reaching the 'Scheduled' state.</div>
                                </div>
                                <Toggle active={true} />
                            </div>

                            <div className="flex justify-between items-center p-3 rounded-xl bg-navy-900/50 border border-gray-800">
                                <div>
                                    <div className="font-medium text-gray-200">Debug Logging</div>
                                    <div className="text-xs text-gray-500">Export verbose Swarm Chat logs to persistent storage.</div>
                                </div>
                                <Toggle active={false} />
                            </div>
                        </div>
                    </section>

                    <section className="space-y-4">
                        <h3 className="text-lg font-semibold text-white border-b border-gray-800 pb-2">Danger Zone</h3>
                        <div className="p-4 rounded-xl border border-red-900/40 bg-red-900/10 flex justify-between items-center">
                            <div>
                                <div className="font-medium text-red-400">Purge Pipeline</div>
                                <div className="text-xs text-gray-500">Permanently delete all data in the current Kanban pipeline.</div>
                            </div>
                            <Button variant="danger" className="text-xs">Purge Data</Button>
                        </div>
                    </section>

                </Card>
            </div>
        </div>
    );
};

const SettingNav = ({ icon: Icon, title, active }) => (
    <button className={`w-full flex items-center gap-3 p-3 rounded-xl transition-all text-sm font-medium ${active
            ? 'bg-cyan-900/20 text-cyan-400 border border-cyan-500/30 shadow-[0_0_10px_rgba(6,182,212,0.1)]'
            : 'text-gray-400 border border-transparent hover:bg-navy-800 hover:text-gray-200'
        }`}>
        <Icon className="w-4 h-4" /> {title}
    </button>
);

const Toggle = ({ active }) => (
    <div className={`w-10 h-5 rounded-full p-0.5 transition-colors duration-300 cursor-pointer ${active ? 'bg-cyan-500 shadow-[0_0_8px_rgba(6,182,212,0.6)]' : 'bg-gray-700'}`}>
        <div className={`w-4 h-4 rounded-full bg-white transition-transform duration-300 ${active ? 'translate-x-5' : 'translate-x-0'}`}></div>
    </div>
);

export default Settings;
