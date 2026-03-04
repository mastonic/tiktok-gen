/** @type {import('tailwindcss').Config} */
export default {
    content: [
        "./index.html",
        "./src/**/*.{js,ts,jsx,tsx}",
    ],
    theme: {
        extend: {
            colors: {
                navy: {
                    900: '#0a0f1c', // Deep navy background
                    800: '#111827', // Charcoal panels
                    700: '#1f2937',
                    600: '#374151',
                },
                cyan: {
                    400: '#06b6d4', // Electric cyan accent
                    500: '#0ea5e9', // Soft blue accent
                },
            },
            fontFamily: {
                sans: ['Inter', 'ui-sans-serif', 'system-ui', 'sans-serif'],
            }
        },
    },
    plugins: [
        require('@tailwindcss/typography'),
    ],
}
