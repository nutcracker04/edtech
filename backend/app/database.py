from supabase import create_client, Client
from app.config import settings

# Initialize Supabase client with service role key
# This bypasses RLS for server-side operations
supabase: Client = create_client(
    settings.supabase_url,
    settings.supabase_service_key
)


def get_supabase() -> Client:
    """
    Dependency to get Supabase client.
    Use this in routes that need database access.
    """
    return supabase


def get_user_supabase(token: str) -> Client:
    """
    Create a Supabase client with user's JWT token.
    This respects RLS policies.
    """
    return create_client(
        settings.supabase_url,
        settings.supabase_service_key,
        options={
            "headers": {
                "Authorization": f"Bearer {token}"
            }
        }
    )
