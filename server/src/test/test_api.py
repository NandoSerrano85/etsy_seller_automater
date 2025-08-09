"""
Tests for the API module.
"""
import pytest
from fastapi import FastAPI
from server.src.api import register_routes


class TestAPI:
    """Test cases for API module."""
    
    def test_register_routes(self):
        """Test that all routes are registered properly."""
        app = FastAPI()
        register_routes(app)
        
        # Check that routes are registered
        route_paths = [route.path for route in app.routes]
        
        # Expected route prefixes based on the router imports
        expected_prefixes = [
            "/auth",
            "/third-party", 
            "/user",
            "/templates",
            "/canvas-sizes",
            "/dashboard",
            "/size-config",
            "/orders",
            "/designs",
            "/mockups"
        ]
        
        # Verify that routes with expected prefixes exist
        for prefix in expected_prefixes:
            matching_routes = [path for path in route_paths if path.startswith(prefix)]
            assert len(matching_routes) > 0, f"No routes found for prefix: {prefix}"
    
    def test_app_creation_with_routes(self, client):
        """Test that the app is created successfully with all routes."""
        # The client fixture already includes registered routes
        response = client.get("/")
        # We expect a 404 for root path since it's not defined
        assert response.status_code == 404
        
        # Test that the app has the expected number of routes
        assert len(client.app.routes) > 10  # Should have multiple routes registered
