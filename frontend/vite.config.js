import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
    plugins: [react()],
    server: {
        host: '0.0.0.0',
        port: 3000,
        allowedHosts: true,
        watch: {
            usePolling: true, // Crucial for Docker volumes on some VPS
        },
        hmr: {
            clientPort: 443,
            protocol: 'wss',
            // We remove the hardcoded host to let Vite detect it
            // or we use the domain if known, but removing it is safer
            overlay: false, // Disables the red screen overlay that reloads the page
        },
    },
})
