"""
postman-sync: Sync Fastify TypeScript routes to Postman collections.

This package automatically parses your Fastify backend routes and keeps
your Postman collection in sync, preserving manual test scripts and customizations.
"""

__version__ = "1.0.0"
__author__ = "Tracker Team"

from .config import Config, ConfigError
from .sync.engine import SyncEngine, SyncError
from .parser import TypeScriptParser, ParserError

__all__ = [
    "Config",
    "ConfigError",
    "SyncEngine",
    "SyncError",
    "TypeScriptParser",
    "ParserError",
]
