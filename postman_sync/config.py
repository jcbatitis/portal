"""Configuration management for postman-sync tool."""

import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv


class ConfigError(Exception):
    """Configuration validation error."""
    pass


class Config:
    """Application configuration loaded from environment variables."""

    def __init__(self):
        """Initialize configuration from environment."""
        # Load .env file if it exists
        load_dotenv()

        # Postman API settings
        self.postman_api_key = self._get_env("POSTMAN_API_KEY", required=True)
        self.postman_collection_id = self._get_env("POSTMAN_COLLECTION_ID", required=True)
        self.postman_workspace_id = self._get_env("POSTMAN_WORKSPACE_ID", required=False)

        # Path settings (relative to backend directory)
        backend_root = Path(__file__).parent.parent
        self.routes_directory = backend_root / self._get_env("POSTMAN_ROUTES_DIR", default="src/routes")
        self.collection_file = backend_root / self._get_env(
            "POSTMAN_COLLECTION_FILE",
            default="postman/tracker-backend-api.postman_collection.json"
        )
        self.repo_root = backend_root.parent

        # Sync settings
        self.deprecation_days = int(self._get_env("POSTMAN_DEPRECATION_DAYS", default="30"))
        self.auto_stage = self._get_env("POSTMAN_AUTO_STAGE", default="true").lower() == "true"
        self.fail_on_error = self._get_env("POSTMAN_FAIL_ON_ERROR", default="true").lower() == "true"

        # Logging
        self.log_level = self._get_env("POSTMAN_LOG_LEVEL", default="INFO").upper()

        # Validate configuration
        self.validate()

    def _get_env(self, key: str, default: Optional[str] = None, required: bool = False) -> str:
        """Get environment variable with optional default."""
        value = os.getenv(key, default)

        if required and not value:
            raise ConfigError(f"Required environment variable {key} is not set")

        return value or ""

    def validate(self) -> None:
        """Validate configuration values."""
        # Validate API key format
        if not self.postman_api_key.startswith("PMAK-"):
            raise ConfigError(
                f"Invalid Postman API key format. Expected key starting with 'PMAK-', "
                f"got: {self.postman_api_key[:10]}..."
            )

        # Validate paths exist
        if not self.routes_directory.exists():
            raise ConfigError(f"Routes directory not found: {self.routes_directory}")

        if not self.routes_directory.is_dir():
            raise ConfigError(f"Routes path is not a directory: {self.routes_directory}")

        collection_dir = self.collection_file.parent
        if not collection_dir.exists():
            raise ConfigError(f"Collection directory not found: {collection_dir}")

        # Validate deprecation days
        if self.deprecation_days < 1:
            raise ConfigError(f"POSTMAN_DEPRECATION_DAYS must be >= 1, got: {self.deprecation_days}")

        # Validate log level
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if self.log_level not in valid_levels:
            raise ConfigError(
                f"Invalid log level: {self.log_level}. Must be one of: {', '.join(valid_levels)}"
            )

    @classmethod
    def from_env(cls) -> "Config":
        """Create Config instance from environment variables."""
        return cls()

    def __repr__(self) -> str:
        """String representation (hide sensitive data)."""
        return (
            f"Config(collection_id={self.postman_collection_id}, "
            f"routes_dir={self.routes_directory}, "
            f"deprecation_days={self.deprecation_days})"
        )
