// Centralized API URL configuration
// In production, we use the environment variable VITE_API_URL.
// For the VPS, this should be https://api.crewai972.xyz
// If it's missing, we try to guess it from the current location to avoid Mixed Content errors.

const getBaseUrl = () => {
    const hostname = window.location.hostname;
    const protocol = window.location.protocol;
    const isLocal = hostname === 'localhost' || hostname === '127.0.0.1';

    console.log("📍 Host Identity:", { hostname, protocol, isLocal });

    // 1. Check if VITE_API_URL is set and if it's usable
    const envApiUrl = import.meta.env.VITE_API_URL;
    if (envApiUrl && envApiUrl.length > 0) {
        // If we are on production HTTPS, but the env var is HTTP Localhost, IGNORE IT
        if (!isLocal && envApiUrl.includes('localhost')) {
            console.warn("⚠️ Ignoring Localhost API URL on Production Host");
        } else {
            console.log("🔗 API (Env Mode):", envApiUrl);
            return envApiUrl;
        }
    }

    // 2. Dynamic Detection for VPS/Production
    if (!isLocal) {
        // Check for common domains
        if (hostname.includes('crewai972.xyz')) {
            const url = `https://api.crewai972.xyz`;
            console.log("🔗 API (Hardcoded Domain Mode):", url);
            return url;
        }

        const isIP = /^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$/.test(hostname);
        if (isIP) {
            // Enforce HTTPS for IP addresses if not local
            const url = `https://${hostname}:5656`;
            console.log("🔗 API (IP Mode):", url);
            return url;
        }

        const baseDomain = hostname.replace('www.', '');
        // Enforce HTTPS for dynamic domains if not local
        const url = `https://api.${baseDomain}`;
        console.log("🔗 API (Dynamic Domain Mode):", url);
        return url;
    }

    // 3. Fallback for local development
    if (protocol === 'https:') {
        const url = `https://api.crewai972.xyz`;
        console.log("🔗 API (Forced HTTPS Fallback):", url);
        return url;
    }
    console.log("🔗 API (Local Fallback): http://localhost:5656");
    return 'http://localhost:5656';
};

export const API_URL = getBaseUrl();
export default API_URL;

console.log("🚀 [API Config] v1.2 (Hardened API Detection)");
