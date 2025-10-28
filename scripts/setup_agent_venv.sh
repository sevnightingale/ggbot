#!/bin/bash
# Setup script for agent service virtual environment
# This creates a separate venv to avoid dependency conflicts with main ggbot app

set -e  # Exit on error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
AGENT_VENV="$PROJECT_ROOT/.venv-agent"

echo "🤖 Setting up autonomous trading agent virtual environment..."
echo ""

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: python3 not found. Please install Python 3.10 or later."
    exit 1
fi

# Check Python version
PYTHON_VERSION=$(python3 --version | cut -d ' ' -f 2 | cut -d '.' -f 1,2)
echo "✓ Found Python $PYTHON_VERSION"

# Remove old venv if it exists
if [ -d "$AGENT_VENV" ]; then
    echo "⚠️  Existing agent venv found at $AGENT_VENV"
    read -p "Remove and recreate? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "🗑️  Removing old venv..."
        rm -rf "$AGENT_VENV"
    else
        echo "❌ Setup cancelled."
        exit 1
    fi
fi

# Create new virtual environment
echo "📦 Creating virtual environment at $AGENT_VENV..."
python3 -m venv "$AGENT_VENV"

# Activate venv
echo "🔧 Activating virtual environment..."
source "$AGENT_VENV/bin/activate"

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip

# Install agent dependencies
echo "📥 Installing agent dependencies from requirements-agent.txt..."
pip install -r "$PROJECT_ROOT/requirements-agent.txt"

echo ""
echo "✅ Agent virtual environment setup complete!"
echo ""
echo "📋 Next steps:"
echo "   1. Activate agent venv:"
echo "      source .venv-agent/bin/activate"
echo ""
echo "   2. Test installation:"
echo "      python -c 'import claude_agent_sdk; print(\"✓ Claude Agent SDK installed\")'"
echo ""
echo "   3. Verify agent module:"
echo "      python -c 'from agent.permissions import is_agent_enabled; print(\"✓ Agent module working\")'"
echo ""
echo "   4. Configure environment (.env):"
echo "      ANTHROPIC_API_KEY=\"sk-ant-xxxxx\""
echo "      AGENT_WHITELIST_USER_ID=\"your-user-id\""
echo ""
