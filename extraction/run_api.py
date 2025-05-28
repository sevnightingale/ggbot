"""
Run the Extraction API server.
"""
import os
import sys
import uvicorn

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from extraction.api import app

if __name__ == "__main__":
    # Get configuration from environment
    host = os.environ.get("EXTRACTION_API_HOST", "0.0.0.0")
    port = int(os.environ.get("EXTRACTION_API_PORT", "5001"))
    
    print(f"Starting Extraction API on {host}:{port}")
    print("API docs available at: http://localhost:5001/docs")
    
    # Run the server
    uvicorn.run(
        app,
        host=host,
        port=port,
        reload=True,  # Enable auto-reload for development
        log_level="info"
    )