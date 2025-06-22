module.exports = {
  apps: [
    {
      name: "api-prodf",
      cwd: "/var/www/api-prodf",
      script: "/var/www/api-prodf/venv/bin/python3",
      args: "-m uvicorn app:app --host 0.0.0.0 --port 8003",
      env: {
        GOOGLE_APPLICATION_CREDENTIALS: "/var/www/api-prodf/secrets/serviceAccountKey.json",
        GOOGLE_CLOUD_PROJECT: "aoe2hd"
      },
      restart_delay: 500
    }
  ]
};
