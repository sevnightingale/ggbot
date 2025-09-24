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
      max_memory_restart: '2G',
      env: {
        NODE_ENV: 'production',
        PYTHONPATH: '/home/sev/ggbot',
        DEVELOPMENT_MODE: 'false',
        HBOT_USERNAME: process.env.HBOT_USERNAME,
        HBOT_PASSWORD: process.env.HBOT_PASSWORD,
        DATABASE_URL: process.env.DATABASE_URL,
        SUPABASE_URL: process.env.SUPABASE_URL,
        SUPABASE_SERVICE_KEY: process.env.SUPABASE_SERVICE_KEY,
        OPENAI_API_KEY: process.env.OPENAI_API_KEY,
        DEEPSEEK_API_KEY: process.env.DEEPSEEK_API_KEY
      },
      error_file: '/home/sev/.pm2/logs/ggbot-error.log',
      out_file: '/home/sev/.pm2/logs/ggbot-out.log',
      log_date_format: 'YYYY-MM-DD HH:mm:ss Z',
      merge_logs: true,
      log_type: 'json',
      max_log_files: 7,        // Keep 7 rotated log files (7-day retention)
      max_log_size: '10M',     // Rotate when log reaches 10MB
      min_uptime: '30s',
      max_restarts: 20,
      restart_delay: 4000
    },
    // Signal processing services (V2 ggShot integration)
    {
      name: 'signal-listener',
      script: '/home/sev/ggbot/signals/listener_service.py',
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
        SERVICE_TYPE: 'signal_listener',
        TG_API_ID: process.env.TG_API_ID,
        TG_API_HASH: process.env.TG_API_HASH,
        GGSHOT_CHANNEL: process.env.GGSHOT_CHANNEL,
        DATABASE_URL: process.env.DATABASE_URL,
        SUPABASE_URL: process.env.SUPABASE_URL,
        SUPABASE_SERVICE_KEY: process.env.SUPABASE_SERVICE_KEY
      },
      error_file: '/home/sev/.pm2/logs/signal-listener-error.log',
      out_file: '/home/sev/.pm2/logs/signal-listener-out.log',
      log_date_format: 'YYYY-MM-DD HH:mm:ss Z',
      merge_logs: true,
      log_type: 'json',
      max_log_files: 7,        // Keep 7 rotated log files (7-day retention)
      max_log_size: '10M',     // Rotate when log reaches 10MB
      min_uptime: '30s',
      max_restarts: 20,
      restart_delay: 4000
    },
    {
      name: 'signal-publisher', 
      script: '/home/sev/ggbot/signals/publishing_service.py',
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
        SERVICE_TYPE: 'signal_publisher',
        DATABASE_URL: process.env.DATABASE_URL,
        SUPABASE_URL: process.env.SUPABASE_URL,
        SUPABASE_SERVICE_KEY: process.env.SUPABASE_SERVICE_KEY
      },
      error_file: '/home/sev/.pm2/logs/signal-publisher-error.log',
      out_file: '/home/sev/.pm2/logs/signal-publisher-out.log',
      log_date_format: 'YYYY-MM-DD HH:mm:ss Z',
      merge_logs: true,
      log_type: 'json',
      max_log_files: 7,        // Keep 7 rotated log files (7-day retention)
      max_log_size: '10M',     // Rotate when log reaches 10MB
      min_uptime: '30s',
      max_restarts: 20,
      restart_delay: 4000
    }
    // Uncomment when ready to add more services
    /*
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