"""Generate Postman test scripts for routes."""

from typing import List
from ..models import Route, HttpMethod


class TestScriptGenerator:
    """Generates test scripts for Postman requests."""

    def generate_test_script(self, route: Route) -> List[str]:
        """
        Generate test script lines for a route.

        Args:
            route: Route to generate tests for

        Returns:
            List of JavaScript lines for Postman test script
        """
        tests = []

        # Status code test
        tests.extend([
            'pm.test("Status code is 200", function () {',
            '    pm.response.to.have.status(200);',
            '});',
            ''
        ])

        # Response structure test based on schema
        if route.schema and route.schema.response:
            # Get 200 response schema if it exists
            success_schema = route.schema.response.get(200)
            if success_schema:
                tests.extend(self._generate_structure_tests())

        # Method-specific tests
        if route.method == HttpMethod.POST:
            tests.extend(self._generate_post_tests(route))
        elif route.method == HttpMethod.GET:
            tests.extend(self._generate_get_tests(route))

        return tests

    def _generate_structure_tests(self) -> List[str]:
        """Generate response structure validation tests."""
        return [
            'pm.test("Response has correct structure", function () {',
            '    var jsonData = pm.response.json();',
            '    pm.expect(jsonData).to.be.an("object");',
            '});',
            ''
        ]

    def _generate_post_tests(self, route: Route) -> List[str]:
        """Generate POST-specific tests."""
        tests = []

        # For token generation
        if 'token' in route.path.lower():
            tests.extend([
                'pm.test("Response contains token", function () {',
                '    var jsonData = pm.response.json();',
                '    pm.expect(jsonData).to.have.property("token");',
                '});',
                '',
                '// Save token to collection variable',
                'if (pm.response.code === 200) {',
                '    var jsonData = pm.response.json();',
                '    pm.collectionVariables.set("jwtToken", jsonData.token);',
                '}',
                ''
            ])
        else:
            # Generic POST test
            tests.extend([
                'pm.test("Resource created successfully", function () {',
                '    pm.expect(pm.response.code).to.be.oneOf([200, 201]);',
                '});',
                ''
            ])

        return tests

    def _generate_get_tests(self, route: Route) -> List[str]:
        """Generate GET-specific tests."""
        tests = []

        # For health checks
        if 'health' in route.path.lower():
            tests.extend([
                'pm.test("Service is healthy", function () {',
                '    var jsonData = pm.response.json();',
                '    pm.expect(jsonData.status).to.eql("ok");',
                '});',
                ''
            ])

        return tests

    def generate_prerequest_auth_script(self) -> List[str]:
        """
        Generate pre-request script for JWT authentication.

        Returns:
            List of JavaScript lines
        """
        return [
            '// Auto-generated: Add JWT authorization header',
            'const token = pm.collectionVariables.get("jwtToken");',
            '',
            'if (token) {',
            '    pm.request.headers.add({',
            '        key: "Authorization",',
            '        value: `Bearer ${token}`',
            '    });',
            '} else {',
            '    console.warn("JWT token not found. Generate token first.");',
            '}'
        ]
