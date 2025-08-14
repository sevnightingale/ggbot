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
      error_file: './logs/ggbots-api.error.log',
      out_file: './logs/ggbots-api.out.log',
      log_file: './logs/ggbots-api.combined.log',
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
      error_file: './logs/ggshot-filter.error.log',
      out_file: './logs/ggshot-filter.out.log',
      log_file: './logs/ggshot-filter.combined.log',
      time: true
    },
    {
      name: 'bot-monitor',
      script: 'core/monitoring/service_runner.py',
      interpreter: '/home/sev/ggbot/.venv/bin/python',
      cwd: '/home/sev/ggbot',
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '256M',
      env: {
        PYTHONPATH: '/home/sev/ggbot'
      },
      error_file: './logs/bot-monitor.error.log',
      out_file: './logs/bot-monitor.out.log',
      log_file: './logs/bot-monitor.combined.log',
      time: true
    },
    {
      name: 'ccxt-mcp-server',
      script: 'core/mcp/ccxt_server.py',
      interpreter: '/home/sev/ggbot/.venv/bin/python',
      cwd: '/home/sev/ggbot',
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '128M',
      env: {
        PYTHONPATH: '/home/sev/ggbot'
      },
      error_file: './logs/ccxt-mcp-server.error.log',
      out_file: './logs/ccxt-mcp-server.out.log',
      log_file: './logs/ccxt-mcp-server.combined.log',
      time: true
    }
  ]
};