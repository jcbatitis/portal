"""Route extraction from parsed TypeScript AST."""

from typing import Optional, Dict, Any
from ..models import Route, HttpMethod, RouteSchema, RouteMetadata, RateLimitConfig
from ..utils.logger import get_logger

logger = get_logger("parser.extractor")


class RouteExtractor:
    """Extracts Route objects from TypeScript AST nodes."""

    def __init__(self, file_path: str, file_name: str, source_code: str):
        """
        Initialize extractor.

        Args:
            file_path: Path to source file
            file_name: Name of source file
            source_code: Full source code for text extraction
        """
        self.file_path = file_path
        self.file_name = file_name
        self.source_code = source_code
        self.source_lines = source_code.split('\n')

    def extract_route(self, node: Any, method: HttpMethod) -> Optional[Route]:
        """
        Extract Route from fastify route definition node.

        Args:
            node: Tree-sitter call_expression node
            method: HTTP method

        Returns:
            Route object or None if extraction fails
        """
        try:
            # Extract arguments from fastify.METHOD(path, options, handler)
            arguments = node.child_by_field_name("arguments")
            if not arguments or arguments.child_count == 0:
                logger.debug(f"No arguments found for route at line {node.start_point[0]}")
                return None

            # Filter out punctuation: (, ), and ,
            args = [arg for arg in arguments.children if arg.type not in (',', '(', ')')]

            if len(args) < 2:
                logger.debug(f"Insufficient arguments for route at line {node.start_point[0]}")
                return None

            # First argument: path (string literal)
            path = self._extract_string(args[0])
            if not path:
                logger.warning(f"Could not extract path from route at line {node.start_point[0]}")
                return None

            # Determine if there are 2 or 3 arguments
            # 2 args: fastify.get(path, handler)
            # 3 args: fastify.get(path, options, handler)
            has_options = len(args) >= 3

            # Extract options if present
            schema = None
            rate_limit = None
            is_protected = False

            if has_options:
                options_node = args[1]
                schema = self._extract_schema(options_node)
                rate_limit = self._extract_rate_limit(options_node)
                is_protected = self._check_protected(options_node)

            # Extract handler name
            handler_node = args[-1]  # Last argument is always handler
            handler_name = self._extract_handler_name(handler_node)

            # Extract JSDoc description
            description = self._extract_jsdoc(node)

            # Build full path (add /api prefix from registration)
            full_path = f"/api{path}"

            # Create metadata
            metadata = RouteMetadata(
                file_path=self.file_path,
                file_name=self.file_name,
                line_number=node.start_point[0] + 1,  # 1-indexed
                is_protected=is_protected,
                rate_limit=rate_limit
            )

            # Create route
            route = Route(
                method=method,
                path=path,
                full_path=full_path,
                handler_name=handler_name,
                description=description,
                schema=schema,
                metadata=metadata
            )

            logger.debug(f"Extracted route: {route.unique_id}")
            return route

        except Exception as e:
            logger.error(f"Failed to extract route at line {node.start_point[0]}: {e}")
            return None

    def _extract_string(self, node: Any) -> Optional[str]:
        """Extract string value from string literal node."""
        if node.type in ('string', 'template_string'):
            text = node.text.decode('utf-8')
            # Remove quotes
            if text.startswith(("'", '"', '`')) and text.endswith(("'", '"', '`')):
                return text[1:-1]
            return text
        return None

    def _extract_schema(self, options_node: Any) -> Optional[RouteSchema]:
        """Extract schema from options object."""
        schema_prop = self._find_object_property(options_node, 'schema')
        if not schema_prop:
            return None

        schema = RouteSchema()

        # Extract body schema
        body_node = self._find_object_property(schema_prop, 'body')
        if body_node:
            schema.body = self._parse_json_schema(body_node)

        # Extract querystring schema
        query_node = self._find_object_property(schema_prop, 'querystring')
        if query_node:
            schema.querystring = self._parse_json_schema(query_node)

        # Extract response schema
        response_node = self._find_object_property(schema_prop, 'response')
        if response_node:
            schema.response = self._parse_response_schema(response_node)

        return schema

    def _extract_rate_limit(self, options_node: Any) -> Optional[RateLimitConfig]:
        """Extract rate limit configuration from options."""
        config_node = self._find_object_property(options_node, 'config')
        if not config_node:
            return None

        rate_limit_node = self._find_object_property(config_node, 'rateLimit')
        if not rate_limit_node:
            return None

        # Extract max and timeWindow
        max_node = self._find_object_property(rate_limit_node, 'max')
        time_window_node = self._find_object_property(rate_limit_node, 'timeWindow')

        if not max_node or not time_window_node:
            return None

        max_value = self._extract_number(max_node)
        time_window = self._extract_string(time_window_node)

        if max_value is None or not time_window:
            return None

        return RateLimitConfig(max=max_value, time_window=time_window)

    def _check_protected(self, options_node: Any) -> bool:
        """Check if route has authVerifyHook in preHandler or onRequest."""
        # Check preHandler
        pre_handler = self._find_object_property(options_node, 'preHandler')
        if pre_handler and self._contains_auth_hook(pre_handler):
            return True

        # Check onRequest
        on_request = self._find_object_property(options_node, 'onRequest')
        if on_request and self._contains_auth_hook(on_request):
            return True

        return False

    def _contains_auth_hook(self, node: Any) -> bool:
        """Check if node contains authVerifyHook reference."""
        text = node.text.decode('utf-8')
        return 'authVerifyHook' in text

    def _extract_handler_name(self, node: Any) -> str:
        """Extract handler function name."""
        if node.type == 'identifier':
            return node.text.decode('utf-8')
        elif node.type == 'arrow_function':
            return 'anonymous'
        elif node.type == 'function':
            name_node = node.child_by_field_name('name')
            if name_node:
                return name_node.text.decode('utf-8')
        return 'handler'

    def _extract_jsdoc(self, node: Any) -> Optional[str]:
        """Extract JSDoc comment above node."""
        line_num = node.start_point[0]
        if line_num == 0:
            return None

        # Look backwards for comment
        prev_line = line_num - 1
        while prev_line >= 0:
            line = self.source_lines[prev_line].strip()

            if line.startswith('/**'):
                # Found JSDoc start, collect until */
                comment_lines = []
                for i in range(prev_line, line_num):
                    comment_line = self.source_lines[i].strip()
                    if comment_line.startswith('/**'):
                        continue
                    if comment_line.endswith('*/'):
                        break
                    # Remove leading * and whitespace
                    clean_line = comment_line.lstrip('*').strip()
                    if clean_line:
                        comment_lines.append(clean_line)

                return ' '.join(comment_lines) if comment_lines else None

            if line and not line.startswith('//'):
                # Hit non-comment line
                break

            prev_line -= 1

        return None

    def _find_object_property(self, node: Any, property_name: str) -> Optional[Any]:
        """Find property in object literal by name."""
        if node.type != 'object':
            return None

        for child in node.children:
            if child.type == 'pair':
                key = child.child_by_field_name('key')
                if key and key.text.decode('utf-8') == property_name:
                    return child.child_by_field_name('value')

        return None

    def _parse_json_schema(self, node: Any) -> Dict[str, Any]:
        """Parse JSON schema object literal (simplified)."""
        # For MVP, we'll extract basic structure
        # In production, would recursively parse entire schema
        return {"type": "object", "_raw": node.text.decode('utf-8')[:200]}

    def _parse_response_schema(self, node: Any) -> Dict[int, Dict[str, Any]]:
        """Parse response schema keyed by status code."""
        schemas = {}

        if node.type == 'object':
            for child in node.children:
                if child.type == 'pair':
                    key = child.child_by_field_name('key')
                    value = child.child_by_field_name('value')

                    if key and value:
                        # Try to parse key as status code
                        try:
                            status_code = int(key.text.decode('utf-8'))
                            schemas[status_code] = self._parse_json_schema(value)
                        except ValueError:
                            continue

        return schemas

    def _extract_number(self, node: Any) -> Optional[int]:
        """Extract number from node."""
        if node.type == 'number':
            try:
                return int(node.text.decode('utf-8'))
            except ValueError:
                return None
        return None
