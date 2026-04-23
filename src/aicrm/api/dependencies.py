"""
API-specific dependencies that extend core dependencies
Provides a consistent interface for all API routers
"""

from ..core.dependencies import (
    create_access_token,
    get_current_active_user,
    get_current_admin_user,
    get_current_superuser,
)

# Re-export for convenience
get_current_superuser = get_current_superuser
from ..core.dependencies import get_current_user
from ..core.dependencies import get_current_user as get_current_user_from_core
from ..core.dependencies import get_db, get_token_from_header


# Additional convenience functions
def get_current_user_token():
    """Helper to get current user token - imports on demand"""
    from ..core.dependencies import get_token_from_header

    return get_token_from_header


__all__ = [
    "get_db",
    "get_current_user",
    "get_current_active_user",
    "get_current_admin_user",
    "get_current_superuser",
    "create_access_token",
    "get_current_user_from_core",
    "get_current_user_token",
]
