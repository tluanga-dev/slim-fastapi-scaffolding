"""Simple authentication endpoint for demo purposes"""
from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr

# Simple JWT functionality without dependencies
import json
import base64
from datetime import datetime

router = APIRouter()

# WARNING: This is a development-only authentication system
# DO NOT USE IN PRODUCTION
# Replace with proper JWT authentication, user management, and database integration

# For development purposes only - no hardcoded credentials in production
DEMO_USERS = {}


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    success: bool
    data: dict
    message: str


def create_simple_token(user_data: dict) -> str:
    """Create a simple token for demo purposes"""
    payload = {
        "sub": user_data["email"],
        "user_id": user_data["id"],
        "permissions": [p["code"] for p in user_data["role"]["permissions"]],
        "exp": (datetime.utcnow() + timedelta(hours=24)).timestamp()
    }
    # Simple base64 encoding (not secure, just for demo)
    token_str = json.dumps(payload)
    return base64.b64encode(token_str.encode()).decode()


@router.post("/login", response_model=LoginResponse)
async def login(login_data: LoginRequest):
    """Development-only login endpoint - Replace with proper authentication"""
    # NOTE: This is a development-only endpoint
    # In production, implement proper user authentication with:
    # - Database user lookup
    # - Password hashing verification
    # - JWT token generation
    # - User role/permission management
    
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Authentication system not implemented. Please implement proper user management."
    )


@router.post("/refresh")
async def refresh_token():
    """Demo refresh endpoint"""
    return {"success": True, "message": "Token refreshed"}


@router.get("/me")
async def get_current_user():
    """Development-only current user endpoint"""
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="User management not implemented. Please implement proper user authentication."
    )


@router.post("/logout")
async def logout():
    """Demo logout endpoint"""
    return {"success": True, "message": "Logged out successfully"}
