import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

export default defineConfig({
  // Pin the automatic JSX runtime. Without this, plugin-react's auto-detection
  // fell back to the classic runtime in Vercel's build and emitted bare
  // React.createElement calls with no React import -> "React is not defined".
  plugins: [react({ jsxRuntime: "automatic" }), tailwindcss()],
  esbuild: { jsx: "automatic", jsxImportSource: "react" }, // belt-and-suspenders if the plugin is ever bypassed
});
