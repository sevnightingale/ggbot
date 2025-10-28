"""
Autonomous Trading Agent Module

This module implements Claude Agent SDK integration for autonomous AI trading agents.

Architecture:
- Two-phase system: Conversation Mode → Autonomous Mode
- Two personalities: Guided (user-defined) vs Experimental (self-evolving)
- Single agent per user (initially, designed to scale)

Phase 1: Database & Foundation (current)
Phase 2: MCP Server & Tools
Phase 3: Agent Runner
Phase 4: Frontend & UX
Phase 5: Production Deployment
"""

__version__ = "0.1.0"
