module.exports = {
  apps: [
    {
      name: "lumina-backend",
      cwd: "C:/Work6/lumina-ai/backend",
      script: "C:/Users/rroopani/AppData/Local/Programs/Python/Python312/python.exe",
      args: "-m uvicorn main:app --host 0.0.0.0 --port 8000",
      watch: false,
      autorestart: true,
      restart_delay: 3000,
      env: {
        PYTHONUNBUFFERED: "1",
      },
    },
    {
      name: "lumina-frontend",
      cwd: "C:/Work6/lumina-ai",
      script: "C:/Work6/lumina-ai/start-frontend.js",
      watch: false,
      autorestart: true,
      restart_delay: 3000,
    },
    {
      name: "lumina-tunnel-backend",
      script: "C:/Users/rroopani/AppData/Local/Microsoft/WinGet/Links/devtunnel.exe",
      args: "host lumina-ai-backend",
      watch: false,
      autorestart: true,
      restart_delay: 5000,
    },
    {
      name: "lumina-tunnel-ui",
      script: "C:/Users/rroopani/AppData/Local/Microsoft/WinGet/Links/devtunnel.exe",
      args: "host lumina-ai-ui",
      watch: false,
      autorestart: true,
      restart_delay: 5000,
    },
    {
      name: "lumina-keepalive",
      script: "C:/Work6/lumina-ai/keepalive-tunnels.js",
      cron_restart: "0 */8 * * *",
      autorestart: false,
      watch: false,
    },
  ],
};
