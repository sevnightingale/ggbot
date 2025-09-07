module.exports = {
  apps: [
    {
      name: 'ggbot',
      script: '/home/sev/ggbot/ggbot.py',
      interpreter: '/home/sev/ggbot/.venv/bin/python',
      cwd: '/home/sev/ggbot',
      instances: 1,
      exec_mode: 'fork',
      autorestart: true,
      watch: false,
      max_memory_restart: '1G',
      env: {
        NODE_ENV: 'production',
        PYTHONPATH: '/home/sev/ggbot',
        DEVELOPMENT_MODE: 'false',
        HBOT_USERNAME: 'sev',
        HBOT_PASSWORD: '7nyhi93cT0Ow2X7S'
      },
      error_file: '/home/sev/.pm2/logs/ggbot-error.log',
      out_file: '/home/sev/.pm2/logs/ggbot-out.log',
      log_date_format: 'YYYY-MM-DD HH:mm:ss Z',
      merge_logs: true,
      min_uptime: '10s',
      max_restarts: 10,
      restart_delay: 4000
    },
    // Uncomment these when ready to add more services
    /*
    {
      name: 'ggshot-filter',
      script: '/home/sev/ggbot/ggshot/filter_service.py',
      interpreter: '/home/sev/ggbot/.venv/bin/python',
      cwd: '/home/sev/ggbot',
      instances: 1,
      exec_mode: 'fork',
      autorestart: true,
      watch: false
    },
    {
      name: 'ccxt-mcp-server',
      script: '/home/sev/ggbot/core/mcp/servers/ccxt_mcp_server.py',
      interpreter: '/home/sev/ggbot/.venv/bin/python',
      cwd: '/home/sev/ggbot',
      instances: 1,
      exec_mode: 'fork',
      autorestart: true,
      watch: false
    }
    */
  ]
};