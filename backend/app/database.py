from typing import Any, Optional

from supabase import Client, create_client

from app.config import settings


class MissingSupabaseConfigurationError(RuntimeError):
    """Raised when code needs Supabase but local config is missing."""


def _ensure_supabase_configured() -> None:
    if settings.supabase_url and settings.supabase_service_key:
        return

    raise MissingSupabaseConfigurationError(
        "Supabase is not configured. Set SUPABASE_URL and SUPABASE_SERVICE_KEY "
        "to use database-backed endpoints."
    )


def _create_supabase_client() -> Client:
    _ensure_supabase_configured()
    return create_client(
        settings.supabase_url,
        settings.supabase_service_key,
    )


class LazySupabaseClient:
    """Delay Supabase initialization until a request actually needs it."""

    def __init__(self) -> None:
        self._client: Optional[Client] = None

    def is_configured(self) -> bool:
        return bool(settings.supabase_url and settings.supabase_service_key)

    def get_client(self) -> Client:
        if self._client is None:
            self._client = _create_supabase_client()
        return self._client

    def __getattr__(self, name: str) -> Any:
        return getattr(self.get_client(), name)


supabase = LazySupabaseClient()


def get_supabase() -> Client:
    """
    Dependency to get Supabase client.
    Use this in routes that need database access.
    """
    return supabase.get_client()


def get_user_supabase(token: str) -> Client:
    """
    Create a Supabase client with user's JWT token.
    This respects RLS policies.
    """
    _ensure_supabase_configured()
    return create_client(
        settings.supabase_url,
        settings.supabase_service_key,
        options={
            "headers": {
                "Authorization": f"Bearer {token}"
            }
        }
    )
