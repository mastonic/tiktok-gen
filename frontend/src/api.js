// Centralized API URL configuration
// In production, we use the environment variable VITE_API_URL.
// For the VPS, this should be https://api.crewai972.xyz
// If it's missing, we try to guess it from the current location to avoid Mixed Content errors.

const getBaseUrl = () => {
    // 1. Check if VITE_API_URL is set (standard Vite way)
    if (import.meta.env.VITE_API_URL) {
        return import.meta.env.VITE_API_URL;
    }

    // 2. Dynamic Detection for VPS/Production
    const hostname = window.location.hostname;
    const protocol = window.location.protocol;

    if (hostname !== 'localhost' && hostname !== '127.0.0.1') {
        const isIP = /^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$/.test(hostname);

        // If it's an IP OR if we are on a port-based setup (no reverse proxy)
        // We force port 5656 for the API
        if (isIP || window.location.port === '3000') {
            return `${protocol}//${hostname}:5656`;
        }

        // Production with Traefik/Reverse Proxy (api.domain.com)
        if (hostname.startsWith('www.')) {
            return `${protocol}//api.${hostname.replace('www.', '')}`;
        }
        return `${protocol}//api.${hostname}`;
    }

    // 3. Fallback for local development
    return 'http://localhost:5656';
};

export const API_URL = getBaseUrl();
export default API_URL;
