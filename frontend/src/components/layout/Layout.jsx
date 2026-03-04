import React from 'react';
import Sidebar from './Sidebar';

const Layout = ({ currentPath, setPath, children }) => {
    return (
        <div className="flex h-screen bg-navy-900 text-gray-200 overflow-hidden relative">
            <div className="absolute inset-0 z-0 bg-[url('https://www.transparenttextures.com/patterns/stardust.png')] opacity-[0.03] pointer-events-none"></div>

            {/* Sidebar */}
            <Sidebar currentPath={currentPath} setPath={setPath} />

            {/* Main Content Area */}
            <main className="flex-1 overflow-y-auto custom-scrollbar relative z-10">
                <div className="h-full p-8 max-w-7xl mx-auto">
                    {children}
                </div>
            </main>
        </div>
    );
};

export default Layout;
