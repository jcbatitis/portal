"""Sync engine orchestrates the complete postman-sync workflow."""

import json
from pathlib import Path
from typing import Optional

from ..config import Config
from ..parser import TypeScriptParser, ParserError
from ..postman.merger import CollectionMerger, MergerError
from ..postman.api_client import PostmanAPIClient, PostmanAPIError
from ..git.stage_manager import GitStageManager, GitStageError
from ..models import SyncResult
from ..utils.logger import get_logger
from ..utils.validators import ValidationError

logger = get_logger("sync")


class SyncError(Exception):
    """Sync operation failed."""
    pass


class SyncEngine:
    """
    Orchestrates the complete postman-sync workflow.

    Workflow:
    1. Parse TypeScript routes
    2. Load local collection JSON
    3. Merge routes into collection
    4. Write updated JSON locally
    5. Sync to Postman API
    6. Auto-stage updated JSON
    """

    def __init__(self, config: Config):
        """
        Initialize sync engine.

        Args:
            config: Application configuration
        """
        self.config = config
        self.parser = TypeScriptParser()
        self.merger = CollectionMerger(deprecation_days=config.deprecation_days)
        self.api_client = PostmanAPIClient(config.postman_api_key)
        self.git_manager = GitStageManager(config.repo_root)

    def run_sync(self) -> SyncResult:
        """
        Execute complete sync workflow.

        Returns:
            SyncResult with changes and errors

        Raises:
            SyncError: If sync fails (when fail_on_error=True)
        """
        logger.info("🔄 Starting Postman collection sync")

        try:
            # Step 1: Parse routes
            logger.info(f"📂 Parsing routes from {self.config.routes_directory}")
            routes = self.parser.parse_directory(self.config.routes_directory)

            if not routes:
                logger.warning("⚠️  No routes found in source files")
                return SyncResult(errors=["No routes found"])

            logger.info(f"✅ Found {len(routes)} routes")

            # Step 2: Load local collection
            logger.info(f"📖 Loading collection from {self.config.collection_file}")

            if not self.config.collection_file.exists():
                raise SyncError(f"Collection file not found: {self.config.collection_file}")

            with open(self.config.collection_file, 'r', encoding='utf-8') as f:
                local_collection = json.load(f)

            # Step 3: Merge
            logger.info("🔀 Merging routes into collection")
            updated_collection, result = self.merger.merge(local_collection, routes)

            if not result.has_changes:
                logger.info("✅ No changes needed")
                return result

            # Step 4: Write local JSON
            logger.info("💾 Writing updated collection to local file")
            self._write_collection(self.config.collection_file, updated_collection)

            # Step 5: Sync to Postman
            if self.config.postman_collection_id:
                logger.info("☁️  Syncing to Postman API")
                try:
                    self.api_client.update_collection(
                        self.config.postman_collection_id,
                        updated_collection
                    )
                    logger.info("✅ Synced to Postman successfully")
                except PostmanAPIError as e:
                    error_msg = f"Postman API error: {e}"
                    logger.error(error_msg)
                    result.errors.append(error_msg)

                    if self.config.fail_on_error:
                        raise SyncError(error_msg) from e

            # Step 6: Auto-stage
            if self.config.auto_stage:
                logger.info("📌 Auto-staging updated collection")
                try:
                    self.git_manager.stage_files([self.config.collection_file])
                    logger.info("✅ Collection file staged for commit")
                except GitStageError as e:
                    error_msg = f"Git staging error: {e}"
                    logger.error(error_msg)
                    result.errors.append(error_msg)

                    if self.config.fail_on_error:
                        raise SyncError(error_msg) from e

            # Summary
            logger.info("=" * 60)
            logger.info("✅ Sync completed successfully")
            logger.info(result.summary())
            logger.info("=" * 60)

            return result

        except (ParserError, MergerError, ValidationError) as e:
            error_msg = f"Sync failed: {e}"
            logger.error(error_msg)

            if self.config.fail_on_error:
                raise SyncError(error_msg) from e

            return SyncResult(errors=[error_msg])

        except Exception as e:
            error_msg = f"Unexpected error during sync: {e}"
            logger.error(error_msg, exc_info=True)

            if self.config.fail_on_error:
                raise SyncError(error_msg) from e

            return SyncResult(errors=[error_msg])

    def _write_collection(self, path: Path, collection: dict) -> None:
        """
        Write collection to JSON file with formatting.

        Args:
            path: Path to write to
            collection: Collection data
        """
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(collection, f, indent=2, ensure_ascii=False)
            f.write('\n')  # Add trailing newline

    def validate_setup(self) -> list[str]:
        """
        Validate sync setup and configuration.

        Returns:
            List of validation errors (empty if valid)
        """
        errors = []

        # Check routes directory
        if not self.config.routes_directory.exists():
            errors.append(f"Routes directory not found: {self.config.routes_directory}")

        # Check collection file directory
        if not self.config.collection_file.parent.exists():
            errors.append(f"Collection directory not found: {self.config.collection_file.parent}")

        # Check Git repository
        if not (self.config.repo_root / ".git").exists():
            errors.append(f"Not a Git repository: {self.config.repo_root}")

        # Test Postman API
        try:
            collections = self.api_client.list_collections()
            logger.debug(f"Postman API accessible: {len(collections)} collections found")
        except PostmanAPIError as e:
            errors.append(f"Postman API error: {e}")

        return errors
