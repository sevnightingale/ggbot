"""
Run the Decision API server.
"""
import os
import sys
import uvicorn

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from decision.api import app

if __name__ == "__main__":
    # Get configuration from environment
    host = os.environ.get("DECISION_API_HOST", "0.0.0.0")
    port = int(os.environ.get("DECISION_API_PORT", "5002"))
    
    print(f"Starting Decision API on {host}:{port}")
    print("API docs available at: http://localhost:5002/docs")
    
    # Run the server
    uvicorn.run(
        app,
        host=host,
        port=port,
        reload=True,  # Enable auto-reload for development
        log_level="info"
    )