"""FastAPI REST API."""

from .app import create_app, app
from .routes import router

__all__ = [
    "create_app",
    "app",
    "router",
]
