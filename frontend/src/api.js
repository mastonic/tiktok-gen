// Centralized API URL configuration
// In production, we use the environment variable VITE_API_URL.
// For the VPS, this should be https://api.crewai972.xyz
// If it's missing, we try to guess it from the current location to avoid Mixed Content errors.

const getBaseUrl = () => {
    // 1. Check if VITE_API_URL is set (standard Vite way)
    if (import.meta.env.VITE_API_URL) {
        return import.meta.env.VITE_API_URL;
    }

    // 2. Fallback for VPS: If we are on crewai972.xyz, the API is on api.crewai972.xyz
    if (window.location.hostname === 'crewai972.xyz' || window.location.hostname === 'www.crewai972.xyz') {
        return 'https://api.crewai972.xyz';
    }

    // 3. Fallback for local development
    return 'http://localhost:5656';
};

export const API_URL = getBaseUrl();
export default API_URL;
