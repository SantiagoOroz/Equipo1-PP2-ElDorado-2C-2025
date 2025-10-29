/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./src/**/*.{js,jsx,ts,tsx}"],
  theme: {
    extend: {
      colors: {
        doradoBlue: "#1B263B",    // Azul gris oscuro
        doradoLightBlue: "#415A77", // Azul medio
        doradoOrange: "#F28C28",   // Naranja El Dorado
        doradoWhite: "#F8FAFC",    // Blanco cálido
      },
    },
  },
  plugins: [],
};
