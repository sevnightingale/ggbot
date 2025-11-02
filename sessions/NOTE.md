
source .venv-agent/bin/activate

API_BASE_URL=http://localhost:8000 python agent/run_agent.py \
--config-id=d13d5536-2498-4f27-b2bc-e4f98958e1d8 \
--mode=strategy_definition

python agent/chat.py --config-id=d13d5536-2498-4f27-b2bc-e4f98958e1d8

 tail -f /home/sev/ggbot/logs/agent-debug.log

API_BASE_URL=http://localhost:8000 python agent/run_agent.py --config-id=d13d5536-2498-4f27-b2bc-e4f98958e1d8 --mode=strategy_definition


python agent/run_agent.py --config-id=d13d5536-2498-4f27-b2bc-e4f98958e1d8 --mode=autonomous