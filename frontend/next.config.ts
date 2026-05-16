import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Emits a self-contained server bundle at .next/standalone — required
  // by the production Dockerfile (multi-cloud deployment).
  output: "standalone",
};

export default nextConfig;
