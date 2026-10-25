import { defineConfig } from "vite";

export default defineConfig({
  esbuild: { jsx: "transform", jsxFactory: "React.createElement", jsxFragment: "React.Fragment" },
  build: {
    outDir: "../dist",
    emptyOutDir: true,
    lib: { entry: "src/index.tsx", formats: ["es"], fileName: () => "client.js" },
    rollupOptions: {
      external: (id) => id === "react" || id.startsWith("react/")
        || id === "react-dom" || id.startsWith("react-dom/")
        || id === "@more-brain/plugin-sdk",
    },
  },
});
