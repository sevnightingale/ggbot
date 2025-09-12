# Manual Trigger Interactive Setup

To run the interactive Telegram setup for the manual trigger, follow these steps:

## Interactive Setup for Manual Trigger

**Step 1: Navigate and activate environment**
```bash
cd /home/sev/ggbot
source .venv/bin/activate
```

**Step 2: Run a test script to set up the manual trigger session**
```bash
python -c "
import asyncio
import os
from dotenv import load_dotenv
from telethon import TelegramClient

async def setup_manual_session():
    load_dotenv()
    
    api_id = int(os.getenv('TG_API_ID'))
    api_hash = os.getenv('TG_API_HASH')
    
    # This will create the manual_trigger_session
    session_path = 'sessions/manual_trigger_session'
    
    client = TelegramClient(session_path, api_id, api_hash)
    await client.start()
    
    print(' Manual trigger session created successfully!')
    await client.disconnect()

asyncio.run(setup_manual_session())
"
```

**Step 3: Follow the authentication prompts**
- Enter your phone number (with country code)
- Enter the verification code from SMS/Telegram
- Enter 2FA password if you have one

**Step 4: Test the manual trigger**
Once the session is created, try the Manual Trigger button in your frontend.

This will create a separate `manual_trigger_session` file so it won't conflict with your existing `ggshot_session` used by the signal-listener service.