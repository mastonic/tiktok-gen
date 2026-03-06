import React from 'react';
import Sidebar from './Sidebar';

const Layout = ({ currentPath, setPath, children }) => {
    const [isSidebarOpen, setIsSidebarOpen] = React.useState(false);

    return (
        <div className="flex h-screen bg-navy-900 text-gray-200 overflow-hidden relative">
            <div className="absolute inset-0 z-0 bg-[url('https://www.transparenttextures.com/patterns/stardust.png')] opacity-[0.03] pointer-events-none"></div>

            {/* Mobile Header */}
            <div className="lg:hidden absolute top-0 left-0 right-0 h-16 flex items-center justify-between px-6 bg-navy-800/80 backdrop-blur-md border-b border-gray-800 z-40">
                <h1 className="text-lg font-bold tracking-tight text-white flex items-center gap-2">
                    <span className="text-cyan-400">Mission</span> Control
                </h1>
                <button
                    onClick={() => setIsSidebarOpen(!isSidebarOpen)}
                    className="p-2 text-gray-400 hover:text-white transition-colors"
                >
                    <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d={isSidebarOpen ? "M6 18L18 6M6 6l12 12" : "M4 6h16M4 12h16M4 18h16"} />
                    </svg>
                </button>
            </div>

            {/* Sidebar with mobile overlay handling */}
            <div className={`${isSidebarOpen ? 'translate-x-0' : '-translate-x-full'} lg:translate-x-0 transition-transform duration-300 fixed lg:relative z-50 h-full`}>
                <Sidebar
                    currentPath={currentPath}
                    setPath={(path) => {
                        setPath(path);
                        setIsSidebarOpen(false);
                    }}
                />
            </div>

            {/* Overlay for mobile sidebar */}
            {isSidebarOpen && (
                <div
                    className="fixed inset-0 bg-black/60 backdrop-blur-sm z-40 lg:hidden"
                    onClick={() => setIsSidebarOpen(false)}
                ></div>
            )}

            {/* Main Content Area */}
            <main className="flex-1 overflow-y-auto custom-scrollbar relative z-10 pt-16 lg:pt-0">
                <div className="h-full p-4 md:p-8 max-w-7xl mx-auto">
                    {children}
                </div>
            </main>
        </div>
    );
};

export default Layout;
