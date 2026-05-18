// frontend/next.config.js
/** @type {import('next').NextConfig} */
const nextConfig = {
  output: "standalone",
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: `${process.env.BACKEND_URL || "http://backend:8000"}/:path*`,
      },
    ];
  },
  images: {
    domains: ["api.sofascore.com", "media.api-sports.io"],
  },
};

module.exports = nextConfig;
