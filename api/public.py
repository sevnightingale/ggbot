"""
Public API Endpoints

Public-facing endpoints that require no authentication.
"""

from fastapi import APIRouter

router = APIRouter(prefix="/api/v2/public", tags=["public"])
