"""Validation utilities for postman-sync."""

from pathlib import Path
from typing import Any, Dict, Optional


class ValidationError(Exception):
    """Validation failed."""
    pass


def validate_postman_collection(data: Dict[str, Any]) -> None:
    """
    Validate Postman collection structure.

    Args:
        data: Collection JSON data

    Raises:
        ValidationError: If collection structure is invalid
    """
    # Check required top-level fields
    if "info" not in data:
        raise ValidationError("Collection missing 'info' field")

    if "item" not in data:
        raise ValidationError("Collection missing 'item' field")

    # Validate info structure
    info = data["info"]
    if not isinstance(info, dict):
        raise ValidationError("Collection 'info' must be an object")

    if "name" not in info:
        raise ValidationError("Collection info missing 'name' field")

    # Validate items structure
    items = data["item"]
    if not isinstance(items, list):
        raise ValidationError("Collection 'item' must be an array")


def validate_route_path(path: str) -> None:
    """
    Validate route path format.

    Args:
        path: Route path (e.g., '/api/users/:id')

    Raises:
        ValidationError: If path format is invalid
    """
    if not path:
        raise ValidationError("Route path cannot be empty")

    if not path.startswith('/'):
        raise ValidationError(f"Route path must start with '/': {path}")

    # Check for invalid characters
    invalid_chars = [' ', '\t', '\n']
    for char in invalid_chars:
        if char in path:
            raise ValidationError(f"Route path contains invalid character: {repr(char)}")


def validate_http_method(method: str) -> None:
    """
    Validate HTTP method.

    Args:
        method: HTTP method (GET, POST, etc.)

    Raises:
        ValidationError: If method is invalid
    """
    valid_methods = ['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'OPTIONS', 'HEAD']

    if method.upper() not in valid_methods:
        raise ValidationError(
            f"Invalid HTTP method: {method}. "
            f"Must be one of: {', '.join(valid_methods)}"
        )


def validate_file_exists(path: Path, file_type: str = "file") -> None:
    """
    Validate that file or directory exists.

    Args:
        path: Path to validate
        file_type: Type description for error message

    Raises:
        ValidationError: If path doesn't exist
    """
    if not path.exists():
        raise ValidationError(f"{file_type} not found: {path}")


def validate_json_schema(schema: Optional[Dict[str, Any]]) -> None:
    """
    Validate JSON schema structure.

    Args:
        schema: JSON schema object

    Raises:
        ValidationError: If schema is invalid
    """
    if schema is None:
        return

    if not isinstance(schema, dict):
        raise ValidationError("JSON schema must be an object")

    # Check for type field
    if "type" not in schema:
        raise ValidationError("JSON schema missing 'type' field")
