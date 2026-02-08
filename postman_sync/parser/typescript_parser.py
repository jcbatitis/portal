"""TypeScript parser using tree-sitter for route extraction."""

from pathlib import Path
from typing import List, Optional
import tree_sitter_typescript as tstypescript
from tree_sitter import Language, Parser, Node

from ..models import Route, HttpMethod
from ..utils.logger import get_logger
from ..utils.validators import validate_file_exists
from .route_extractor import RouteExtractor

logger = get_logger("parser")


class ParserError(Exception):
    """Parser operation failed."""
    pass


class TypeScriptParser:
    """
    Parse TypeScript files to extract Fastify route definitions.

    Uses tree-sitter for robust AST-based parsing.
    """

    # HTTP methods to look for
    FASTIFY_METHODS = {
        'get': HttpMethod.GET,
        'post': HttpMethod.POST,
        'put': HttpMethod.PUT,
        'patch': HttpMethod.PATCH,
        'delete': HttpMethod.DELETE,
        'options': HttpMethod.OPTIONS,
        'head': HttpMethod.HEAD,
    }

    def __init__(self):
        """Initialize TypeScript parser."""
        try:
            # Load TypeScript language (pointer + name required in 0.21.x)
            self.language = Language(tstypescript.language_typescript(), 'typescript')
            self.parser = Parser()
            self.parser.set_language(self.language)
            logger.info("TypeScript parser initialized")
        except Exception as e:
            raise ParserError(f"Failed to initialize TypeScript parser: {e}")

    def parse_file(self, file_path: Path) -> List[Route]:
        """
        Parse a single TypeScript file and extract routes.

        Args:
            file_path: Path to TypeScript file

        Returns:
            List of extracted Route objects

        Raises:
            ParserError: If parsing fails
        """
        try:
            validate_file_exists(file_path, "TypeScript file")

            # Read source code
            source_code = file_path.read_text(encoding='utf-8')

            # Parse with tree-sitter
            tree = self.parser.parse(bytes(source_code, 'utf-8'))

            # Extract routes
            routes = self._extract_routes_from_tree(
                tree.root_node,
                str(file_path),
                file_path.name,
                source_code
            )

            logger.info(f"Parsed {file_path.name}: found {len(routes)} routes")
            return routes

        except Exception as e:
            raise ParserError(f"Failed to parse {file_path}: {e}")

    def parse_directory(self, directory: Path, pattern: str = "*.ts") -> List[Route]:
        """
        Parse all TypeScript files in a directory.

        Args:
            directory: Directory to search
            pattern: File pattern (default: *.ts)

        Returns:
            List of all extracted routes

        Raises:
            ParserError: If directory doesn't exist
        """
        validate_file_exists(directory, "Directory")

        if not directory.is_dir():
            raise ParserError(f"Not a directory: {directory}")

        all_routes = []
        files = list(directory.glob(pattern))

        if not files:
            logger.warning(f"No TypeScript files found in {directory}")
            return []

        logger.info(f"Parsing {len(files)} files in {directory}")

        for file_path in files:
            try:
                routes = self.parse_file(file_path)
                all_routes.extend(routes)
            except ParserError as e:
                logger.error(f"Failed to parse {file_path.name}: {e}")
                # Continue with other files
                continue

        logger.info(f"Total routes extracted: {len(all_routes)}")
        return all_routes

    def _extract_routes_from_tree(
        self,
        root_node: Node,
        file_path: str,
        file_name: str,
        source_code: str
    ) -> List[Route]:
        """
        Extract routes from parsed AST.

        Args:
            root_node: Root node of syntax tree
            file_path: Path to source file
            file_name: Name of source file
            source_code: Full source code

        Returns:
            List of Route objects
        """
        routes = []
        extractor = RouteExtractor(file_path, file_name, source_code)

        # Traverse tree looking for fastify route definitions
        for node in self._traverse_tree(root_node):
            if self._is_fastify_route(node):
                method = self._extract_method(node)
                if method:
                    route = extractor.extract_route(node, method)
                    if route:
                        routes.append(route)

        return routes

    def _traverse_tree(self, node: Node):
        """
        Depth-first traversal of syntax tree.

        Args:
            node: Current node

        Yields:
            All nodes in tree
        """
        yield node
        for child in node.children:
            yield from self._traverse_tree(child)

    def _is_fastify_route(self, node: Node) -> bool:
        """
        Check if node is a fastify route definition.

        Pattern: fastify.get(...), fastify.post(...), etc.

        Args:
            node: AST node to check

        Returns:
            True if node is a route definition
        """
        if node.type != 'call_expression':
            return False

        # Get function being called
        function_node = node.child_by_field_name('function')
        if not function_node or function_node.type != 'member_expression':
            return False

        # Check for fastify.METHOD pattern
        object_node = function_node.child_by_field_name('object')
        property_node = function_node.child_by_field_name('property')

        if not object_node or not property_node:
            return False

        # Check object is 'fastify'
        object_name = object_node.text.decode('utf-8')
        if object_name != 'fastify':
            return False

        # Check property is a valid HTTP method
        method_name = property_node.text.decode('utf-8').lower()
        return method_name in self.FASTIFY_METHODS

    def _extract_method(self, node: Node) -> Optional[HttpMethod]:
        """
        Extract HTTP method from route definition node.

        Args:
            node: call_expression node

        Returns:
            HttpMethod or None
        """
        function_node = node.child_by_field_name('function')
        if not function_node:
            return None

        property_node = function_node.child_by_field_name('property')
        if not property_node:
            return None

        method_name = property_node.text.decode('utf-8').lower()
        return self.FASTIFY_METHODS.get(method_name)
