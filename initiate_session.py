# initiate_session.py
import asyncio
import json
import os
from dotenv import load_dotenv
from cryptography.fernet import Fernet

# Import Browser-use components.
from browser_use import Browser, BrowserConfig, BrowserContextConfig, Agent
# Use LangChain’s LlamaCpp to wrap your CPU inference model.
from langchain.llms import LlamaCpp

load_dotenv()  # Loads environment variables from .env

# 1. Load the local 4-bit quantized TinyLlama model via LlamaCpp.
model_path = "/root/ggbot/models/tinyllama-quantized.gguf"  # Adjust path if needed.
llm = LlamaCpp(model_path=model_path, n_ctx=2048, n_threads=4)

# 2. Decrypt TradingView credentials.
# Ensure ENCRYPTION_KEY is set in your .env file.
key = os.getenv("ENCRYPTION_KEY").encode()
cipher = Fernet(key)
with open("/root/ggbot/tv_credentials.enc", "rb") as f:
    decrypted = cipher.decrypt(f.read())
credentials = json.loads(decrypted.decode())

async def initiate_session():
    # Configure the BrowserContext to save session cookies.
    ctx_config = BrowserContextConfig(cookies_file="/root/ggbot/tv_cookies.json")
    
    # Launch the browser in headful mode (headless=False).
    # Ensure Xvfb is running and DISPLAY is set.
    browser = Browser(config=BrowserConfig(headless=False, new_context_config=ctx_config))
    
    # Craft a login task prompt using your TradingView credentials.
    login_task = (
        f"Go to tradingview.com and log in with username '{credentials['username']}' "
        f"and password '{credentials['password']}'."
    )
    
    # Create the agent with the task, using the local LLM.
    agent = Agent(
        task=login_task,
        llm=llm,
        browser=browser
    )

    # Run the agent to perform the login and then close the browser (saving cookies).
    await agent.run()
    await browser.close()

if __name__ == "__main__":
    asyncio.run(initiate_session())
    print("Session login script completed.")
