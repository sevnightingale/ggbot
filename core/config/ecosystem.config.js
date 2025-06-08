module.exports = {
  apps : [{
    name   : "ccxt-mcp-server",
    script : "/home/sev/ggbot/core/mcp/servers/ccxt_mcp_server.py",
    interpreter: "/home/sev/ggbot/.venv/bin/python",
    env: {
      "EXCHANGE_NAME": "bitmex",
      "TESTNET": "1",
      // The following will be set by the test before connecting
      // "EXCHANGE_API": "",  
      // "EXCHANGE_SECRET": "",
    },
    watch: false,
    max_memory_restart: "200M",
    log_date_format: "YYYY-MM-DD HH:mm:ss Z",
    args: "--config /home/sev/ggbot/core/config/ccxt-accounts.json"
  }]
}