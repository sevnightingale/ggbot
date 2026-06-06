module.exports = {
  apps: [
    {
      name: 'ggbot',
      namespace: 'gg',
      script: '/home/sev/ggbot/ggbot.py',
      interpreter: '/home/sev/ggbot/.venv/bin/python',
      cwd: '/home/sev/ggbot',
      instances: 1,
      exec_mode: 'fork',
      autorestart: true,
      watch: false,
      max_memory_restart: '2G',
      kill_timeout: 5000,
      env: {
        NODE_ENV: 'production',
        PYTHONPATH: '/home/sev/ggbot',
        DEVELOPMENT_MODE: 'false',
        DATABASE_URL: process.env.DATABASE_URL,
        GGBOT_VAULT_KEY: process.env.GGBOT_VAULT_KEY,
        SERVICE_AUTH_TOKEN: process.env.SERVICE_AUTH_TOKEN,
        SUPABASE_JWT_SECRET: process.env.SUPABASE_JWT_SECRET,
        OPENAI_API_KEY: process.env.OPENAI_API_KEY,
        DEEPSEEK_API_KEY: process.env.DEEPSEEK_API_KEY,
        REDIS_URL: process.env.REDIS_URL
      },
      error_file: '/dev/null',
      out_file: '/dev/null',
      log_date_format: 'YYYY-MM-DD HH:mm:ss Z',
      merge_logs: true,
      min_uptime: '30s',
      max_restarts: 20,
      restart_delay: 4000
    },
    // Error monitoring service
    {
      name: 'error-alerts',
      namespace: 'gg',
      script: '/home/sev/ggbot/core/monitoring/error_alert_service.py',
      interpreter: '/home/sev/ggbot/.venv/bin/python',
      cwd: '/home/sev/ggbot',
      instances: 1,
      exec_mode: 'fork',
      autorestart: true,
      watch: false,
      max_memory_restart: '200M',
      env: {
        NODE_ENV: 'production',
        PYTHONPATH: '/home/sev/ggbot',
        GG_FILTER_TOKEN: process.env.GG_FILTER_TOKEN,
        ERROR_ALERT_CHANNEL_ID: process.env.ERROR_ALERT_CHANNEL_ID,
        DATABASE_URL: process.env.DATABASE_URL,
        SUPABASE_URL: process.env.SUPABASE_URL,
        SUPABASE_SERVICE_KEY: process.env.SUPABASE_SERVICE_KEY
      },
      error_file: '/dev/null',
      out_file: '/dev/null',
      log_date_format: 'YYYY-MM-DD HH:mm:ss Z',
      merge_logs: true,
      min_uptime: '30s',
      max_restarts: 20,
      restart_delay: 4000
    },
    // WebSocket Market Data Service - Real-time candle streaming
    {
      name: 'market-data-ws',
      namespace: 'gg',
      script: '/home/sev/ggbot/core/services/websocket_market_data_service.py',
      interpreter: '/home/sev/ggbot/.venv/bin/python',
      cwd: '/home/sev/ggbot',
      instances: 1,
      exec_mode: 'fork',
      autorestart: true,
      watch: false,
      max_memory_restart: '500M',
      env: {
        NODE_ENV: 'production',
        PYTHONPATH: '/home/sev/ggbot',
        REDIS_URL: process.env.REDIS_URL,
        DATABASE_URL: process.env.DATABASE_URL
      },
      error_file: 'logs/market-data-ws-error.log',
      out_file: 'logs/market-data-ws-out.log',
      log_date_format: 'YYYY-MM-DD HH:mm:ss Z',
      merge_logs: true,
      min_uptime: '30s',
      max_restarts: 50,  // Increased from 20 for resilience
      restart_delay: 5000  // Increased to 5s for backoff
    },
    // Universal Account Monitor - Unified monitoring for paper + hyperliquid
    {
      name: 'account-monitor',
      namespace: 'gg',
      script: '/home/sev/ggbot/core/monitoring/universal_account_monitor.py',
      interpreter: '/home/sev/ggbot/.venv/bin/python',
      cwd: '/home/sev/ggbot',
      instances: 1,
      exec_mode: 'fork',
      autorestart: true,
      watch: false,
      max_memory_restart: '300M',
      env: {
        NODE_ENV: 'production',
        PYTHONPATH: '/home/sev/ggbot',
        DATABASE_URL: process.env.DATABASE_URL,
        GGBOT_VAULT_KEY: process.env.GGBOT_VAULT_KEY,
        REDIS_URL: process.env.REDIS_URL
      },
      error_file: 'logs/account-monitor-error.log',
      out_file: 'logs/account-monitor-out.log',
      log_date_format: 'YYYY-MM-DD HH:mm:ss Z',
      merge_logs: true,
      min_uptime: '30s',
      max_restarts: 20,
      restart_delay: 4000
    },
    // Scheduler process — runs bot cycles independently of API
    {
      name: 'ggbot-scheduler',
      namespace: 'gg',
      script: '/home/sev/ggbot/ggbot_scheduler.py',
      interpreter: '/home/sev/ggbot/.venv/bin/python',
      cwd: '/home/sev/ggbot',
      instances: 1,
      exec_mode: 'fork',
      autorestart: true,
      watch: false,
      max_memory_restart: '1G',
      kill_timeout: 5000,
      env: {
        NODE_ENV: 'production',
        PYTHONPATH: '/home/sev/ggbot',
        DATABASE_URL: process.env.DATABASE_URL,
        GGBOT_VAULT_KEY: process.env.GGBOT_VAULT_KEY,
        SUPABASE_JWT_SECRET: process.env.SUPABASE_JWT_SECRET,
        OPENAI_API_KEY: process.env.OPENAI_API_KEY,
        DEEPSEEK_API_KEY: process.env.DEEPSEEK_API_KEY,
        REDIS_URL: process.env.REDIS_URL
      },
      error_file: '/dev/null',
      out_file: '/dev/null',
      log_date_format: 'YYYY-MM-DD HH:mm:ss Z',
      merge_logs: true,
      min_uptime: '30s',
      max_restarts: 20,
      restart_delay: 4000
    }
  ]
};
