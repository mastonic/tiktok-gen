/** @type {import('tailwindcss').Config} */
export default {
    content: [
        "./index.html",
        "./src/**/*.{js,ts,jsx,tsx}",
    ],
    theme: {
        extend: {
            colors: {
                brand: {
                    black: '#050505',
                    blue: '#3B82F6',
                    white: '#FFFFFF',
                },
                navy: {
                    900: '#050505', // Deep Black
                    800: '#111827', // Charcoal panels
                    700: '#1f2937',
                    600: '#374151',
                },
                cyan: {
                    400: '#3B82F6', // Electric Blue
                    500: '#0ea5e9',
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
