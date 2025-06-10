module.exports = {
  apps: [
    {
      name: 'api-staging',
      script: './start_api.sh',
      cwd: '/var/www/api-staging',
      interpreter: 'bash',
      env: {
        ENV: 'development'
      }
    }
  ]
};
