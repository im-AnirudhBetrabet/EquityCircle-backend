from supabase import create_client, Client
from app.core.config import settings

def get_supabase_client() -> Client:
    """
    Creates and returns a Supabase client instance securely
    using the validated environment variables.
    :return: Client
    """
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)

supabase: Client = get_supabase_client()

auth_client: Client = get_supabase_client()