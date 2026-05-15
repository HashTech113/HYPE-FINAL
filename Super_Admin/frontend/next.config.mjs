/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // Pin tracing root to this folder so the root-level package-lock.json
  // (used only for `concurrently`) doesn't confuse Next's workspace inference.
  outputFileTracingRoot: import.meta.dirname,
  experimental: {
    optimizePackageImports: ["lucide-react", "date-fns", "recharts"],
  },
};

export default nextConfig;
