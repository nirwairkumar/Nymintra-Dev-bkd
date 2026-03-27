from fastapi import APIRouter, Depends, HTTPException, status
from supabase import Client
from app.db.database import get_supabase
from app.schemas.user import UserResponse
from typing import Dict, Any
# Removed jose and settings since we use Supabase Auth directly
from app.api.endpoints.auth import oauth2_scheme

router = APIRouter()

def get_current_user(token: str = Depends(oauth2_scheme), supabase: Client = Depends(get_supabase)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        # Verify token with Supabase Auth
        auth_res = supabase.auth.get_user(token)
        if not auth_res.user:
            raise credentials_exception
            
        user = auth_res.user
        
        # Check metadata first for extremely fast resolution
        cached_role = user.user_metadata.get("role") if user.user_metadata else None
        if cached_role == "admin":
            return {
                "id": user.id,
                "email": user.email,
                "name": user.user_metadata.get("name") or (user.email.split("@")[0] if user.email else "Admin"),
                "phone": user.phone,
                "role": "admin"
            }
        
        # Check if user is a regular User in the public table
        user_data = supabase.table("users").select("*").eq("id", user.id).execute()
        if user_data.data:
            regular_user = user_data.data[0]
            regular_user["role"] = "user"
            return regular_user
            
        # If not in either table, return the auth user object with a default role
        return {
            "id": user.id,
            "email": user.email,
            "name": user.email.split("@")[0] if user.email else "User",
            "phone": user.phone,
            "role": "user"
        }
    except Exception as e:
        err_str = str(e).lower()
        if "timeout" in err_str or "readtimeout" in err_str:
            raise HTTPException(status_code=503, detail="Service timeout, please try again")
        raise credentials_exception

@router.get("/me", response_model=UserResponse)
def read_users_me(current_user: dict = Depends(get_current_user)):
    return current_user
