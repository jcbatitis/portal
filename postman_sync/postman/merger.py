"""Smart collection merger that preserves manual changes."""

from typing import Dict, Any, List, Set, Tuple
from datetime import datetime, timedelta
import re

from ..models import Route, SyncResult
from ..utils.logger import get_logger
from ..utils.validators import validate_postman_collection
from .test_generator import TestScriptGenerator

logger = get_logger("postman.merger")


class MergerError(Exception):
    """Collection merge operation failed."""
    pass


class CollectionMerger:
    """
    Intelligently merge routes into Postman collection.

    Preserves:
    - Test scripts
    - Pre-request scripts (except auth scripts we generate)
    - Manual request descriptions
    - Example responses
    - Collection variables
    """

    def __init__(self, deprecation_days: int = 30):
        """
        Initialize merger.

        Args:
            deprecation_days: Days before removing deprecated routes
        """
        self.deprecation_days = deprecation_days
        self.test_generator = TestScriptGenerator()

    def merge(self, collection: Dict[str, Any], routes: List[Route]) -> Tuple[Dict[str, Any], SyncResult]:
        """
        Merge routes into collection with smart conflict resolution.

        Strategy:
        1. Index existing requests by unique_id
        2. For each route: update existing or add new
        3. Mark missing routes as deprecated
        4. Remove old deprecated routes

        Args:
            collection: Current Postman collection
            routes: Parsed routes from source code

        Returns:
            Tuple of (updated collection, sync result)

        Raises:
            MergerError: If merge fails
        """
        try:
            validate_postman_collection(collection)

            # Build index of existing requests
            existing_requests = self._index_requests(collection)
            route_ids = {route.unique_id for route in routes}

            # Track changes
            result = SyncResult()

            # Determine which routes are new (need folders created)
            new_routes = [r for r in routes if r.unique_id not in existing_requests]
            new_routes_by_folder = self._organize_by_folder(new_routes)

            # Only create folders for NEW routes (existing ones stay in their current folder)
            self._ensure_folders(collection, new_routes_by_folder.keys())

            # Process each route
            for route in routes:
                if route.unique_id in existing_requests:
                    # Update existing request
                    request_item = existing_requests[route.unique_id]
                    self._update_request(request_item, route)
                    result.routes_updated.append(route)
                else:
                    # Add new request
                    self._add_request(collection, route)
                    result.routes_added.append(route)

            # Handle deprecation
            deprecated = self._mark_deprecated(collection, existing_requests, route_ids)
            result.routes_deprecated.extend(deprecated)

            # Remove old deprecated
            removed = self._remove_old_deprecated(collection)
            result.routes_removed.extend(removed)

            logger.info(f"Merge complete: {result.summary()}")
            return collection, result

        except Exception as e:
            raise MergerError(f"Failed to merge collection: {e}") from e

    def _index_requests(self, collection: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """
        Build map of request unique_id -> request object.

        Args:
            collection: Postman collection

        Returns:
            Dictionary mapping unique_id to request item
        """
        index = {}

        def index_items(items: List[Dict[str, Any]]):
            for item in items:
                if "request" in item:
                    # Extract method and path
                    method = item["request"]["method"]
                    path = self._extract_path(item["request"].get("url", {}))
                    unique_id = f"{method}:{path}"
                    # Keep first match only (avoid duplicates like "Test Rate Limit")
                    if unique_id not in index:
                        index[unique_id] = item
                    else:
                        logger.debug(f"Skipping duplicate unique_id: {unique_id} ({item.get('name', '?')})")

                # Recurse into folders
                if "item" in item:
                    index_items(item["item"])

        index_items(collection.get("item", []))
        logger.debug(f"Indexed {len(index)} existing requests")
        return index

    def _extract_path(self, url: Any) -> str:
        """Extract path from Postman URL object."""
        if isinstance(url, str):
            # Simple string URL
            return url

        if isinstance(url, dict):
            # Postman URL object
            path_parts = url.get("path", [])
            if isinstance(path_parts, list):
                return "/" + "/".join(path_parts)
            return str(path_parts)

        return ""

    def _organize_by_folder(self, routes: List[Route]) -> Dict[str, List[Route]]:
        """
        Organize routes by folder name.

        Args:
            routes: List of routes

        Returns:
            Dictionary mapping folder name to routes
        """
        folders = {}
        for route in routes:
            folder = route.folder_name
            if folder not in folders:
                folders[folder] = []
            folders[folder].append(route)

        return folders

    def _ensure_folders(self, collection: Dict[str, Any], folder_names: Set[str]):
        """
        Ensure folder structure exists in collection.

        Args:
            collection: Postman collection
            folder_names: Set of folder names needed
        """
        if "item" not in collection:
            collection["item"] = []

        existing_folders = {
            item["name"]: item
            for item in collection["item"]
            if "item" in item  # Is a folder
        }

        for folder_name in folder_names:
            if folder_name not in existing_folders:
                # Create new folder
                folder = {
                    "name": folder_name,
                    "item": []
                }
                collection["item"].append(folder)
                logger.debug(f"Created folder: {folder_name}")

    def _update_request(self, request_item: Dict[str, Any], route: Route):
        """
        Update existing request, preserving manual customizations.

        Args:
            request_item: Existing Postman request
            route: New route data
        """
        request = request_item.get("request", {})

        # Preserve existing manual name (don't overwrite user customizations)

        # Update description with last synced timestamp
        sync_note = f"\n\n_Last synced: {datetime.utcnow().isoformat()}_"
        current_desc = request.get("description", "")

        # Preserve user description
        if "_Last synced:" in current_desc:
            base_desc = current_desc.split("_Last synced:")[0].rstrip()
        else:
            base_desc = current_desc

        # Use route description if no user description
        if not base_desc and route.description:
            base_desc = route.description

        request["description"] = base_desc + sync_note

        # Update URL
        request["url"] = self._build_url(route.full_path)

        # Update method
        request["method"] = route.method.value

        # Add auth pre-request script if protected
        if route.metadata and route.metadata.is_protected:
            self._ensure_auth_prerequest(request_item)

        logger.debug(f"Updated request: {route.unique_id}")

    def _add_request(self, collection: Dict[str, Any], route: Route):
        """
        Create new request from route.

        Args:
            collection: Postman collection
            route: Route to add
        """
        # Find target folder
        folder = None
        for item in collection.get("item", []):
            if item.get("name") == route.folder_name and "item" in item:
                folder = item
                break

        if not folder:
            # Create folder if it doesn't exist
            folder = {
                "name": route.folder_name,
                "item": []
            }
            collection["item"].append(folder)

        # Build request
        request_item = {
            "name": route.request_name,
            "event": [],
            "request": {
                "method": route.method.value,
                "header": [],
                "url": self._build_url(route.full_path),
                "description": route.description or f"{route.method.value} {route.full_path}\n\n_Last synced: {datetime.utcnow().isoformat()}_"
            },
            "response": []
        }

        # Add test script
        test_script = self.test_generator.generate_test_script(route)
        if test_script:
            request_item["event"].append({
                "listen": "test",
                "script": {
                    "exec": test_script,
                    "type": "text/javascript"
                }
            })

        # Add auth pre-request if protected
        if route.metadata and route.metadata.is_protected:
            self._ensure_auth_prerequest(request_item)

        # Add to folder
        folder["item"].append(request_item)
        logger.debug(f"Added new request: {route.unique_id}")

    def _build_url(self, path: str) -> Dict[str, Any]:
        """
        Build Postman URL object.

        Args:
            path: Route path

        Returns:
            Postman URL object
        """
        # Split path into parts
        parts = [p for p in path.split('/') if p]

        return {
            "raw": "{{baseUrl}}" + path,
            "host": ["{{baseUrl}}"],
            "path": parts
        }

    def _ensure_auth_prerequest(self, request_item: Dict[str, Any]):
        """
        Add pre-request script to inject JWT token.

        Args:
            request_item: Postman request item
        """
        if "event" not in request_item:
            request_item["event"] = []

        # Check if pre-request script exists
        has_prerequest = any(
            e.get("listen") == "prerequest"
            for e in request_item["event"]
        )

        if not has_prerequest:
            script = self.test_generator.generate_prerequest_auth_script()
            request_item["event"].append({
                "listen": "prerequest",
                "script": {
                    "exec": script,
                    "type": "text/javascript"
                }
            })

    def _mark_deprecated(
        self,
        collection: Dict[str, Any],
        existing_requests: Dict[str, Dict[str, Any]],
        current_route_ids: Set[str]
    ) -> List[str]:
        """
        Mark requests not found in source as deprecated.

        Args:
            collection: Postman collection
            existing_requests: Indexed existing requests
            current_route_ids: Set of current route IDs

        Returns:
            List of deprecated unique_ids
        """
        deprecated = []

        for unique_id, request_item in existing_requests.items():
            if unique_id not in current_route_ids:
                request = request_item.get("request", {})
                desc = request.get("description", "")

                # Only mark if not already deprecated
                if "**DEPRECATED**" not in desc:
                    deprecation_date = datetime.utcnow().isoformat()
                    new_desc = f"**DEPRECATED** (as of {deprecation_date})\n\n{desc}"
                    request["description"] = new_desc
                    deprecated.append(unique_id)
                    logger.debug(f"Marked as deprecated: {unique_id}")

        return deprecated

    def _remove_old_deprecated(self, collection: Dict[str, Any]) -> List[str]:
        """
        Remove requests deprecated > 30 days ago.

        Args:
            collection: Postman collection

        Returns:
            List of removed unique_ids
        """
        cutoff_date = datetime.utcnow() - timedelta(days=self.deprecation_days)
        removed = []

        def process_items(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
            filtered = []
            for item in items:
                if "request" in item:
                    # Check if deprecated and old
                    desc = item.get("request", {}).get("description", "")
                    if "**DEPRECATED**" in desc:
                        # Extract deprecation date
                        match = re.search(r'\(as of ([\d\-T:\.]+)\)', desc)
                        if match:
                            try:
                                dep_date = datetime.fromisoformat(match.group(1))
                                if dep_date < cutoff_date:
                                    # Remove this request
                                    method = item["request"]["method"]
                                    path = self._extract_path(item["request"].get("url", {}))
                                    unique_id = f"{method}:{path}"
                                    removed.append(unique_id)
                                    logger.debug(f"Removed old deprecated: {unique_id}")
                                    continue
                            except ValueError:
                                pass

                # Recurse into folders
                if "item" in item:
                    item["item"] = process_items(item["item"])

                filtered.append(item)

            return filtered

        collection["item"] = process_items(collection.get("item", []))
        return removed
