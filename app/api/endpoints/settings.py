from fastapi import APIRouter, Depends, HTTPException, Body
from typing import Dict, Any
from app.db.database import get_supabase
from app.api.endpoints.users import get_current_user
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/{key}")
def get_setting(key: str, supabase = Depends(get_supabase)):
    """
    Fetch a public setting by key (e.g., 'customer_support').
    """
    try:
        res = supabase.table("app_settings").select("value, description").eq("key", key).execute()
        if not res.data:
            raise HTTPException(status_code=404, detail=f"Setting '{key}' not found")
        return res.data[0]
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error fetching setting {key}: {e}")
        # Return empty struct if DB table doesn't exist yet to prevent hard crashes before migration
        if "relation \"public.app_settings\" does not exist" in str(e):
             return {"value": {"enabled": False, "text": "Support settings pending database migration."}}
        raise HTTPException(status_code=500, detail="Failed to fetch setting")

@router.put("/{key}")
def update_setting(
    key: str, 
    value: Dict[str, Any] = Body(...),
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """
    Update a setting. Requires admin privileges.
    """
    if current_user.get('role') != 'admin':
        raise HTTPException(status_code=403, detail="Only admins can modify global settings")
        
    try:
        # Upsert the setting
        payload = {
            "key": key,
            "value": value
        }
        res = supabase.table("app_settings").upsert(payload, on_conflict="key").execute()
        return {"status": "success", "message": f"Setting '{key}' configured successfully"}
    except Exception as e:
        logger.error(f"Error updating setting {key}: {e}")
        if "relation \"public.app_settings\" does not exist" in str(e):
             raise HTTPException(status_code=500, detail="Please run the settings.sql migration in Supabase first.")
        raise HTTPException(status_code=500, detail=str(e))
