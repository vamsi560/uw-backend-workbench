"""
Minimal Guidewire Data APIs for testing
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any

# Create router for testing
test_guidewire_router = APIRouter(prefix="/api/guidewire-test", tags=["Guidewire Test"])

@test_guidewire_router.get("/status")
async def get_test_status():
    """Test endpoint to verify router loading"""
    return {
        "status": "success", 
        "message": "Guidewire test router is working"
    }

@test_guidewire_router.get("/ping")
async def ping():
    """Simple ping endpoint"""
    return {"ping": "pong"}