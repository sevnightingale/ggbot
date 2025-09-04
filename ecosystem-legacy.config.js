module.exports = {
  apps: [
    {
      name: 'ggbots-api',
      script: 'main_api.py',
      interpreter: '/home/sev/ggbot/.venv/bin/python',
      cwd: '/home/sev/ggbot',
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '1G',
      env: {
        PYTHONPATH: '/home/sev/ggbot',
        NODE_ENV: 'production'
      },
      log: false,
      time: true
    },
    {
      name: 'ggshot-filter',
      script: 'ggshot/ggshot_service.py',
      interpreter: '/home/sev/ggbot/.venv/bin/python',
      cwd: '/home/sev/ggbot',
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '512M',
      env: {
        PYTHONPATH: '/home/sev/ggbot'
      },
      log: false,
      time: true
    },
    {
      name: 'ccxt-mcp-server',
      script: 'core/mcp/servers/ccxt_mcp_server.py',
      interpreter: '/home/sev/ggbot/.venv/bin/python',
      cwd: '/home/sev/ggbot',
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '128M',
      env: {
        PYTHONPATH: '/home/sev/ggbot'
      },
      log: false,
      time: true
    }
  ]
};