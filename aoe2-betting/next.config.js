const withPWA = require("next-pwa")({
  dest: "public",
  register: true,
  skipWaiting: true,
});

const isDocker = process.env.DOCKER === 'true';

module.exports = withPWA({
  reactStrictMode: true,

  eslint: {
    ignoreDuringBuilds: true,
  },

  env: {
    BACKEND_API: process.env.NEXT_PUBLIC_API_BASE_URL,
    REPLAY_API: process.env.REPLAY_API || '', // optional
  },

  async rewrites() {
    return [
      {
        source: '/api/game_stats',
        destination: isDocker
          ? 'http://aoe2-backend:8002/api/game_stats'
          : `${process.env.NEXT_PUBLIC_API_BASE_URL}/api/game_stats`,
      },
      {
        source: '/admin/users',
        destination: isDocker
          ? 'http://aoe2-backend:8002/admin/users'
          : `${process.env.NEXT_PUBLIC_API_BASE_URL}/admin/users`,
      },
      {
        source: '/api/parse_replay',
        destination: isDocker
          ? 'http://aoe2-backend:8002/api/parse_replay'
          : `${process.env.NEXT_PUBLIC_API_BASE_URL}/api/parse_replay`,
      }
    ];
  }
});
