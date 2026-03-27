import logging
from supabase import create_client, Client
from app.core.config import settings

logger = logging.getLogger(__name__)

def get_supabase() -> Client:
    """Dependency for returning a fresh Supabase client."""
    if not settings.SUPABASE_URL or not settings.SUPABASE_URL.startswith("http"):
        logger.error("SUPABASE_URL is missing or invalid in environment variables")
        raise ValueError("SUPABASE_URL is not set")
    if not settings.SUPABASE_KEY:
        logger.error("SUPABASE_KEY is missing in environment variables")
        raise ValueError("SUPABASE_KEY is not set")
        
    try:
        return create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
    except Exception as e:
        logger.error(f"Failed to initialize Supabase client: {str(e)}")
        raise
