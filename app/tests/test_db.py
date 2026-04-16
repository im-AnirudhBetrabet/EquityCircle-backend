from app.db.supabase import get_supabase_client
from app.core.config import settings

def test_supabase_client_initialization():
    """
    Ensure the Supabase client initializes correctly with the
    environment variables defined in the settings.
    """
    client = get_supabase_client()

    assert client is not None
    assert str(client.supabase_url).rstrip("/") == str(settings.SUPABASE_URL).rstrip("/")