from supabase import create_client, Client
from app.core.config import settings

def get_supabase() -> Client:
    """Dependency for returning a fresh Supabase client to prevent auth session bleeding."""
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
