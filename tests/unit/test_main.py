"""Tests for FastAPI application."""

from fastapi.testclient import TestClient


class TestHealthEndpoint:
    """Test suite for health check endpoint."""

    def test_health_check_returns_200(self, client: TestClient) -> None:
        """Test that health check endpoint returns 200 OK."""
        # Arrange & Act
        response = client.get("/health")

        # Assert
        assert response.status_code == 200

    def test_health_check_returns_correct_data(self, client: TestClient) -> None:
        """Test that health check returns correct response data."""
        # Arrange & Act
        response = client.get("/health")
        data = response.json()

        # Assert
        assert data["status"] == "healthy"
        assert data["version"] == "0.1.0"

    def test_health_check_has_correct_content_type(self, client: TestClient) -> None:
        """Test that health check returns JSON content type."""
        # Arrange & Act
        response = client.get("/health")

        # Assert
        assert response.headers["content-type"] == "application/json"


class TestRootEndpoint:
    """Test suite for root endpoint."""

    def test_root_returns_200(self, client: TestClient) -> None:
        """Test that root endpoint returns 200 OK."""
        # Arrange & Act
        response = client.get("/")

        # Assert
        assert response.status_code == 200

    def test_root_returns_service_info(self, client: TestClient) -> None:
        """Test that root endpoint returns service information."""
        # Arrange & Act
        response = client.get("/")
        data = response.json()

        # Assert
        assert data["service"] == "quality-agent"
        assert data["version"] == "0.1.0"
        assert data["description"] == "AI-powered GitHub PR analysis service"
        assert "docs" in data

    def test_root_shows_docs_in_development(self, client: TestClient) -> None:
        """Test that root shows docs link in development environment."""
        # Arrange & Act
        response = client.get("/")
        data = response.json()

        # Assert (test environment is development)
        assert data["docs"] == "/docs"


class TestOpenAPIDocumentation:
    """Test suite for OpenAPI documentation endpoints."""

    def test_docs_endpoint_available_in_development(self, client: TestClient) -> None:
        """Test that /docs endpoint is available in development."""
        # Arrange & Act
        response = client.get("/docs")

        # Assert
        assert response.status_code == 200

    def test_openapi_json_available(self, client: TestClient) -> None:
        """Test that OpenAPI JSON schema is available."""
        # Arrange & Act
        response = client.get("/openapi.json")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["info"]["title"] == "Quality Agent"
        assert data["info"]["version"] == "0.1.0"


class TestCORSMiddleware:
    """Test suite for CORS middleware configuration."""

    def test_cors_headers_present_for_github(self, client: TestClient) -> None:
        """Test that CORS headers are set for GitHub origin."""
        # Arrange & Act
        response = client.options(
            "/health",
            headers={
                "Origin": "https://github.com",
                "Access-Control-Request-Method": "POST",
            }
        )

        # Assert
        assert response.status_code == 200
        assert "access-control-allow-origin" in response.headers


class TestErrorHandling:
    """Test suite for global error handling."""

    def test_404_for_unknown_endpoint(self, client: TestClient) -> None:
        """Test that unknown endpoints return 404."""
        # Arrange & Act
        response = client.get("/unknown-endpoint")

        # Assert
        assert response.status_code == 404

    def test_405_for_wrong_method(self, client: TestClient) -> None:
        """Test that wrong HTTP methods return 405."""
        # Arrange & Act
        response = client.post("/health")  # GET only

        # Assert
        assert response.status_code == 405
