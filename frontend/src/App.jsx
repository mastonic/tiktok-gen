import React, { useState } from 'react';
import Layout from './components/layout/Layout';
import HumanInTheLoop from './components/HumanInTheLoop';
import Overview from './pages/Overview';
import SwarmChat from './pages/SwarmChat';
import Pipeline from './pages/Pipeline';
import Approvals from './pages/Approvals';
import Runs from './pages/Runs';
import Analytics from './pages/Analytics';
import Agents from './pages/Agents';
import Budget from './pages/Budget';
import Settings from './pages/Settings';
import Studio from './pages/Studio';
import Gallery from './pages/Gallery';
import Blog from './pages/Blog';

import Login from './components/Login';

function App() {
    // Check if we are on the /cockpit path (via hash or direct path for SPA support)
    const isCockpitRoute = window.location.hash === '#cockpit' || window.location.pathname === '/cockpit';

    const [currentPath, setPath] = useState(isCockpitRoute ? '/overview' : '/blog');
    const [isAuthenticated, setIsAuthenticated] = useState(localStorage.getItem('im_auth') === 'true');

    const renderPage = () => {
        switch (currentPath) {
            case '/overview':
                return <Overview />;
            case '/chat':
                return <SwarmChat />;
            case '/pipeline':
                return <Pipeline />;
            case '/approvals':
                return <Approvals />;
            case '/runs':
                return <Runs setPath={setPath} />;
            case '/studio':
                return <Studio />;
            case '/gallery':
                return <Gallery />;
            case '/analytics':
                return <Analytics />;
            case '/agents':
                return <Agents />;
            case '/budget':
                return <Budget />;
            case '/settings':
                return <Settings />;
            case '/blog':
                return <Blog onEnterCockpit={() => setPath('/overview')} />;
            default:
                return <Overview />;
        }
    };

    // Public Blog View (Default)
    if (currentPath === '/blog') {
        return <Blog onEnterCockpit={() => setPath('/overview')} />;
    }

    // Secure Cockpit View
    if (!isAuthenticated) {
        return <Login onLogin={() => setIsAuthenticated(true)} />;
    }

    return (
        <>
            <HumanInTheLoop />
            <Layout currentPath={currentPath} setPath={setPath}>
                {renderPage()}
            </Layout>
        </>
    );
}

export default App;
