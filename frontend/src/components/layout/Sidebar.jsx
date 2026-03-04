import React from 'react';
import {
    LayoutDashboard,
    MessageSquare,
    ListTodo,
    CheckSquare,
    Play,
    LineChart,
    Bot,
    Wallet,
    Settings,
    Image as ImageIcon,
    Clock,
    Library
} from 'lucide-react';

const Sidebar = ({ currentPath, setPath }) => {
    const [time, setTime] = React.useState(new Date());

    React.useEffect(() => {
        const timer = setInterval(() => setTime(new Date()), 1000);
        return () => clearInterval(timer);
    }, []);

    const navItems = [
        { name: 'Overview', icon: LayoutDashboard, path: '/overview' },
        { name: 'Swarm Chat', icon: MessageSquare, path: '/chat' },
        { name: 'Pipeline', icon: ListTodo, path: '/pipeline' },
        { name: 'Approvals', icon: CheckSquare, path: '/approvals' },
        { name: 'Runs', icon: Play, path: '/runs' },
        { name: 'Studio', icon: ImageIcon, path: '/studio' },
        { name: 'Gallery', icon: Library, path: '/gallery' },
        { name: 'Analytics', icon: LineChart, path: '/analytics' },
        { name: 'Agents', icon: Bot, path: '/agents' },
        { name: 'Budget & Models', icon: Wallet, path: '/budget' },
        { name: 'Settings', icon: Settings, path: '/settings' },
    ];

    return (
        <aside className="w-64 h-screen bg-navy-800 border-r border-gray-800 flex flex-col shadow-2xl z-20">
            <div className="p-6">
                <h1 className="text-xl font-bold tracking-tight text-white flex items-center gap-2">
                    <span className="text-cyan-400">Mission</span> Control
                </h1>
                <p className="text-xs text-gray-500 mt-1 uppercase tracking-widest font-semibold flex items-center">
                    <span className="w-2 h-2 rounded-full bg-cyan-500 mr-2 animate-pulse"></span>
                    Hybrid Engine
                </p>
            </div>

            <nav className="flex-1 px-4 py-4 space-y-1 overflow-y-auto custom-scrollbar">
                {navItems.map((item) => {
                    const isActive = currentPath === item.path;
                    return (
                        <button
                            key={item.name}
                            onClick={() => setPath(item.path)}
                            className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-300 ${isActive
                                ? 'bg-gradient-to-r from-cyan-500/10 to-blue-500/10 text-cyan-400 border border-cyan-500/20 shadow-[0_0_15px_rgba(6,182,212,0.1)]'
                                : 'text-gray-400 hover:text-gray-200 hover:bg-gray-800/50'
                                }`}
                        >
                            <item.icon className={`h-5 w-5 ${isActive ? 'text-cyan-400 drop-shadow-[0_0_8px_rgba(6,182,212,0.8)]' : 'text-gray-500'}`} />
                            <span className="font-medium">{item.name}</span>
                        </button>
                    );
                })}
            </nav>

            <div className="p-4 border-t border-gray-800 space-y-3">
                <div className="glass-card p-3 flex items-center justify-between bg-navy-900/50 border border-gray-800/50">
                    <div className="flex items-center gap-2">
                        <Clock className="h-4 w-4 text-cyan-400 animate-pulse" />
                        <span className="text-xs font-bold text-gray-200 uppercase tracking-widest">Local Time</span>
                    </div>
                    <span className="text-sm font-mono text-cyan-400 font-bold">
                        {time.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
                    </span>
                </div>

                <div className="glass-card p-4 flex flex-col gap-2">
                    <div className="text-xs text-gray-400 uppercase tracking-widest font-semibold">System Status</div>
                    <div className="flex justify-between items-center text-sm">
                        <span className="text-gray-300">Agents Online</span>
                        <span className="text-cyan-400 font-bold">10/10</span>
                    </div>
                    <div className="w-full bg-gray-700/50 rounded-full h-1.5 mt-1">
                        <div className="bg-cyan-400 h-1.5 rounded-full w-full shadow-[0_0_10px_rgba(6,182,212,0.5)]"></div>
                    </div>
                </div>
            </div>
        </aside>
    );
};

export default Sidebar;
