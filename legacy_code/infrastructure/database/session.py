from src.infrastructure.database.database import get_session as get_db

# Re-export for easier imports
__all__ = ["get_db"]
