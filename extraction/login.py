import asyncio
import os
from browser_use import Agent, Browser, BrowserConfig, BrowserContextConfig
from langchain_community.llms import LlamaCpp
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from dotenv import load_dotenv

# Load environment variables from /root/ggbot/.env
load_dotenv()

# Retrieve TradingView credentials from environment variables
username = os.getenv("TVIEW_USERNAME")
password = os.getenv("TVIEW_PASSWORD")

# Ensure credentials are set
if not username or not password:
    raise ValueError("TVIEW_USERNAME or TVIEW_PASSWORD not set in .env")

# Custom chat model wrapper for LlamaCpp
class LlamaCppChatModel(BaseChatModel):
    def __init__(self, llm):
        super().__init__()  # Initialize the base class
        self.llm = llm

    def _generate(self, messages, stop=None, run_manager=None, **kwargs):
        # Convert messages to a prompt string based on the chat template
        prompt = ""
        for message in messages:
            if isinstance(message, SystemMessage):
                prompt += f"<|system|>\n{message.content}</s>\n"
            elif isinstance(message, HumanMessage):
                prompt += f"<|user|>\n{message.content}</s>\n"
            elif isinstance(message, AIMessage):
                prompt += f"<|assistant|>\n{message.content}</s>\n"
        prompt += "<|assistant|>\n"  # Add generation prompt
        # Generate response using the underlying LlamaCpp model
        response = self.llm(prompt, stop=stop, **kwargs)
        return AIMessage(content=response)

    @property
    def _llm_type(self):
        return "llama_cpp_chat"

async def main():
    print("Starting script...")
    MODEL_PATH = "/root/ggbot/models/tinyllama-quantized.gguf"
    
    print("Initializing LlamaCpp model...")
    llm = LlamaCpp(
        model_path=MODEL_PATH,
        temperature=0.7,
        max_tokens=512,
        top_p=1,
        verbose=True
    )
    print("LlamaCpp model initialized.")
    
    print("Creating chat model wrapper...")
    chat_model = LlamaCppChatModel(llm)
    print("Chat model created.")
    
    print("Setting up browser...")
    ctx_config = BrowserContextConfig(cookies_file="/root/ggbot/extraction/tv_cookies.json")
    browser = Browser(config=BrowserConfig(headless=False, new_context_config=ctx_config))
    print("Browser configured.")
    
    task = f"Go to tradingview.com, log in with username {username} and password {password}, and save the session"
    print("Initializing agent...")
    agent = Agent(task=task, llm=chat_model, browser=browser)
    print("Agent initialized.")
    
    print("Running agent...")
    await agent.run()
    print("Agent run complete.")
    
    print("Closing browser...")
    await browser.close()
    print("Script finished.")
    
    # Wrap LlamaCpp in the custom chat model
    chat_model = LlamaCppChatModel(llm)
    
    # Configure browser in headful mode for initial testing
    ctx_config = BrowserContextConfig(cookies_file="/root/ggbot/extraction/tv_cookies.json")
    browser = Browser(config=BrowserConfig(headless=False, new_context_config=ctx_config))
    
    # Define the login task with credentials
    task = f"Go to tradingview.com, log in with username {username} and password {password}, and save the session"
    agent = Agent(
        task=task,
        llm=chat_model,
        browser=browser
    )
    
    # Run the agent and save cookies
    await agent.run()
    await browser.close()  # Ensures cookies are written to tv_cookies.json

if __name__ == "__main__":
    asyncio.run(main())