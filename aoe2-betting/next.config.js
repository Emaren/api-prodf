const withPWA = require("next-pwa")({
  dest: "public",
  register: true,
  skipWaiting: true,
});

const isDocker = process.env.DOCKER === 'true';

module.exports = withPWA({
  reactStrictMode: true,

  env: {
    BACKEND_API: "http://192.168.219.28:8000",
    REPLAY_API: "http://192.168.219.28:5001",
  },


  async rewrites() {
    return [
      {
        source: '/api/game_stats',
        destination: isDocker
          ? 'http://aoe2-backend:8002/api/game_stats'
          : 'http://localhost:8002/api/game_stats',
      },
    ];
  }
});
