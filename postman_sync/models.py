"""Domain models for postman-sync."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum


class HttpMethod(Enum):
    """HTTP methods supported by Fastify."""
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    PATCH = "PATCH"
    DELETE = "DELETE"
    OPTIONS = "OPTIONS"
    HEAD = "HEAD"


@dataclass
class RouteSchema:
    """JSON schema for route validation."""
    body: Optional[Dict[str, Any]] = None
    querystring: Optional[Dict[str, Any]] = None
    params: Optional[Dict[str, Any]] = None
    headers: Optional[Dict[str, Any]] = None
    response: Optional[Dict[int, Dict[str, Any]]] = None  # Response by status code


@dataclass
class RateLimitConfig:
    """Rate limiting configuration for a route."""
    max: int
    time_window: str  # e.g., "1 minute", "15 minutes"


@dataclass
class RouteMetadata:
    """Metadata about route extraction."""
    file_path: str
    file_name: str
    line_number: int
    is_protected: bool  # Has authVerifyHook
    rate_limit: Optional[RateLimitConfig] = None
    extracted_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class Route:
    """Represents a parsed Fastify route."""
    method: HttpMethod
    path: str
    full_path: str  # With /api prefix
    handler_name: str
    description: Optional[str] = None
    schema: Optional[RouteSchema] = None
    metadata: Optional[RouteMetadata] = None

    @property
    def unique_id(self) -> str:
        """Generate unique identifier for route matching."""
        return f"{self.method.value}:{self.full_path}"

    @property
    def folder_name(self) -> str:
        """Get folder name from metadata file name."""
        if not self.metadata:
            return "Routes"

        # Convert file name to title case
        # e.g., "auth.ts" -> "Auth", "user-management.ts" -> "User Management"
        name = self.metadata.file_name.replace(".ts", "").replace(".js", "")
        words = name.replace("-", " ").replace("_", " ").split()
        return " ".join(word.capitalize() for word in words)

    @property
    def request_name(self) -> str:
        """Generate request name for Postman."""
        # Convert path to readable name
        # e.g., "/api/auth/token" -> "Generate Token" (for POST)
        #       "/api/health" -> "Health Check" (for GET)

        path_parts = [p for p in self.full_path.split('/') if p and p != 'api']

        if not path_parts:
            return f"{self.method.value} Root"

        # Method-specific prefixes
        method_prefix = {
            HttpMethod.GET: "Get",
            HttpMethod.POST: "Create" if len(path_parts) == 1 else "Generate",
            HttpMethod.PUT: "Update",
            HttpMethod.PATCH: "Update",
            HttpMethod.DELETE: "Delete",
        }.get(self.method, self.method.value)

        # Convert path parts to title case
        readable_parts = []
        for part in path_parts:
            # Replace parameters like :id with {id}
            if part.startswith(':'):
                part = f"{{{part[1:]}}}"
            # Convert kebab-case to Title Case
            words = part.replace("-", " ").replace("_", " ").split()
            readable_parts.append(" ".join(word.capitalize() for word in words))

        name = " ".join(readable_parts)

        # Special cases
        if "health" in name.lower():
            return "Health Check"
        if "verify" in name.lower():
            return f"Verify {name.replace('Verify', '').strip()}"

        return f"{method_prefix} {name}"


@dataclass
class SyncResult:
    """Result of a sync operation."""
    routes_added: List[Route] = field(default_factory=list)
    routes_updated: List[Route] = field(default_factory=list)
    routes_deprecated: List[str] = field(default_factory=list)  # unique_ids
    routes_removed: List[str] = field(default_factory=list)  # unique_ids
    errors: List[str] = field(default_factory=list)
    synced_at: datetime = field(default_factory=datetime.utcnow)

    @property
    def has_errors(self) -> bool:
        """Check if sync had errors."""
        return len(self.errors) > 0

    @property
    def has_changes(self) -> bool:
        """Check if sync made any changes."""
        return (
            len(self.routes_added) > 0
            or len(self.routes_updated) > 0
            or len(self.routes_deprecated) > 0
            or len(self.routes_removed) > 0
        )

    def summary(self) -> str:
        """Get human-readable summary."""
        lines = []
        if self.routes_added:
            lines.append(f"  ✅ Added: {len(self.routes_added)} routes")
        if self.routes_updated:
            lines.append(f"  🔄 Updated: {len(self.routes_updated)} routes")
        if self.routes_deprecated:
            lines.append(f"  ⚠️  Deprecated: {len(self.routes_deprecated)} routes")
        if self.routes_removed:
            lines.append(f"  🗑️  Removed: {len(self.routes_removed)} routes")
        if self.errors:
            lines.append(f"  ❌ Errors: {len(self.errors)}")

        return "\n".join(lines) if lines else "  No changes"
