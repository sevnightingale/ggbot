import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  trailingSlash: false,
  poweredByHeader: false,
  async rewrites() {
    return {
      // Host-based rewrites run first
      beforeFiles: [
        // arena.ggbots.ai serves /arena page
        {
          source: '/',
          has: [{ type: 'host', value: 'arena.ggbots.ai' }],
          destination: '/arena',
        },
      ],
      // Regular rewrites
      afterFiles: [
        {
          source: '/api/:path*',
          destination: 'https://ggbots-api.nightingale.business/api/:path*',
        },
        {
          source: '/agent/:path*',
          destination: 'https://ggbots-api.nightingale.business/agent/:path*',
        },
        {
          source: '/dashboard/:path*',
          destination: 'https://ggbots-api.nightingale.business/dashboard/:path*',
        },
        {
          source: '/extraction/:path*',
          destination: 'https://ggbots-api.nightingale.business/extraction/:path*',
        },
        {
          source: '/health',
          destination: 'https://ggbots-api.nightingale.business/health',
        },
      ],
      fallback: [],
    };
  },
};

export default nextConfig;
