"""Postman API client for collection management."""

from typing import Dict, Any
import requests

from ..utils.logger import get_logger

logger = get_logger("postman.api")


class PostmanAPIError(Exception):
    """Postman API operation failed."""
    pass


class PostmanAPIClient:
    """Client for Postman REST API."""

    BASE_URL = "https://api.getpostman.com"

    def __init__(self, api_key: str):
        """
        Initialize Postman API client.

        Args:
            api_key: Postman API key (starts with PMAK-)
        """
        self.api_key = api_key
        self.session = requests.Session()
        self.session.headers.update({
            "X-Api-Key": api_key,
            "Content-Type": "application/json"
        })

    def fetch_collection(self, collection_id: str) -> Dict[str, Any]:
        """
        Fetch collection from Postman.

        Args:
            collection_id: Collection ID

        Returns:
            Collection data

        Raises:
            PostmanAPIError: If fetch fails
        """
        url = f"{self.BASE_URL}/collections/{collection_id}"

        try:
            logger.info(f"Fetching collection {collection_id}")
            response = self.session.get(url)
            response.raise_for_status()

            data = response.json()
            collection = data.get("collection")

            if not collection:
                raise PostmanAPIError("Response missing 'collection' field")

            logger.info(f"Successfully fetched collection: {collection.get('info', {}).get('name', 'Unknown')}")
            return collection

        except requests.HTTPError as e:
            if e.response.status_code == 401:
                raise PostmanAPIError("Invalid API key or unauthorized") from e
            elif e.response.status_code == 404:
                raise PostmanAPIError(f"Collection not found: {collection_id}") from e
            elif e.response.status_code == 429:
                raise PostmanAPIError("Rate limit exceeded. Try again later.") from e
            else:
                raise PostmanAPIError(f"HTTP {e.response.status_code}: {e}") from e

        except requests.RequestException as e:
            raise PostmanAPIError(f"Network error: {e}") from e

    def update_collection(self, collection_id: str, collection_data: Dict[str, Any]) -> None:
        """
        Update collection on Postman.

        Args:
            collection_id: Collection ID
            collection_data: Updated collection data

        Raises:
            PostmanAPIError: If update fails
        """
        url = f"{self.BASE_URL}/collections/{collection_id}"

        try:
            logger.info(f"Updating collection {collection_id}")
            response = self.session.put(
                url,
                json={"collection": collection_data}
            )
            response.raise_for_status()

            logger.info("Successfully updated collection on Postman")

        except requests.HTTPError as e:
            if e.response.status_code == 401:
                raise PostmanAPIError("Invalid API key or unauthorized") from e
            elif e.response.status_code == 404:
                raise PostmanAPIError(f"Collection not found: {collection_id}") from e
            elif e.response.status_code == 429:
                raise PostmanAPIError("Rate limit exceeded. Try again later.") from e
            else:
                error_body = e.response.text
                raise PostmanAPIError(
                    f"HTTP {e.response.status_code}: {error_body[:200]}"
                ) from e

        except requests.RequestException as e:
            raise PostmanAPIError(f"Network error: {e}") from e

    def create_collection(self, collection_data: Dict[str, Any], workspace_id: str = None) -> str:
        """
        Create a new collection.

        Args:
            collection_data: Collection data
            workspace_id: Optional workspace ID

        Returns:
            New collection ID

        Raises:
            PostmanAPIError: If creation fails
        """
        url = f"{self.BASE_URL}/collections"
        if workspace_id:
            url += f"?workspace={workspace_id}"

        try:
            logger.info("Creating new collection")
            response = self.session.post(
                url,
                json={"collection": collection_data}
            )
            response.raise_for_status()

            data = response.json()
            collection = data.get("collection", {})
            collection_id = collection.get("uid")

            if not collection_id:
                raise PostmanAPIError("Response missing collection ID")

            logger.info(f"Successfully created collection: {collection_id}")
            return collection_id

        except requests.HTTPError as e:
            raise PostmanAPIError(f"HTTP {e.response.status_code}: {e}") from e

        except requests.RequestException as e:
            raise PostmanAPIError(f"Network error: {e}") from e

    def list_collections(self, workspace_id: str = None) -> list[Dict[str, Any]]:
        """
        List all collections.

        Args:
            workspace_id: Optional workspace ID filter

        Returns:
            List of collection metadata

        Raises:
            PostmanAPIError: If listing fails
        """
        url = f"{self.BASE_URL}/collections"
        if workspace_id:
            url += f"?workspace={workspace_id}"

        try:
            logger.info("Listing collections")
            response = self.session.get(url)
            response.raise_for_status()

            data = response.json()
            collections = data.get("collections", [])

            logger.info(f"Found {len(collections)} collections")
            return collections

        except requests.HTTPError as e:
            raise PostmanAPIError(f"HTTP {e.response.status_code}: {e}") from e

        except requests.RequestException as e:
            raise PostmanAPIError(f"Network error: {e}") from e
