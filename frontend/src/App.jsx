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

function App() {
    const [currentPath, setPath] = useState('/overview');

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
                return <Runs />;
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
            default:
                return <Overview />;
        }
    };

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
