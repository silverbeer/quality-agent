"""FastAPI application entry point.

This module initializes the FastAPI application with:
- Structured logging
- Health check endpoint
- CORS middleware
- Exception handling
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.logging_config import configure_logging, get_logger
from app.webhook_receiver import handle_github_webhook

# Configure logging before anything else
configure_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager.

    Handles startup and shutdown events for the application.

    Args:
        app: FastAPI application instance

    Yields:
        None (context manager)
    """
    # Startup
    logger.info(
        "application_startup",
        environment=settings.environment,
        port=settings.port,
        log_level=settings.log_level,
    )

    yield

    # Shutdown
    logger.info("application_shutdown")


# Create FastAPI application
app = FastAPI(
    title="Quality Agent",
    description="AI-powered GitHub PR analysis service for test coverage and quality insights",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.is_development else None,  # Disable docs in production
    redoc_url="/redoc" if settings.is_development else None,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://github.com"],  # Only allow GitHub
    allow_credentials=False,
    allow_methods=["POST"],  # Only POST for webhooks
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Global exception handler for unhandled errors.

    Logs all unhandled exceptions and returns a generic error response.

    Args:
        request: The incoming request
        exc: The exception that was raised

    Returns:
        JSON response with error details
    """
    logger.error(
        "unhandled_exception",
        exc_info=exc,
        path=request.url.path,
        method=request.method,
    )

    # Don't expose internal errors in production
    if settings.is_production:
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"},
        )

    # Show details in development
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "error": str(exc),
            "type": type(exc).__name__,
        },
    )


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint.

    Returns the health status of the service. Used by load balancers,
    orchestrators, and monitoring tools.

    Returns:
        Dictionary with status

    Example:
        ```bash
        curl http://localhost:8000/health
        ```
    """
    logger.debug("health_check_called")
    return {"status": "healthy", "version": "0.1.0"}


@app.get("/")
async def root() -> dict[str, str]:
    """Root endpoint.

    Provides basic information about the service.

    Returns:
        Dictionary with service information
    """
    return {
        "service": "quality-agent",
        "version": "0.1.0",
        "description": "AI-powered GitHub PR analysis service",
        "docs": "/docs" if settings.is_development else "disabled",
    }


@app.post("/webhook/github")
async def github_webhook_endpoint(
    request: Request,
    x_hub_signature_256: str = Header(..., alias="X-Hub-Signature-256"),
    x_github_event: str = Header(..., alias="X-GitHub-Event"),
    x_github_delivery: str = Header(..., alias="X-GitHub-Delivery"),
) -> dict[str, str | int]:
    """GitHub webhook endpoint for pull request events.

    Receives and processes GitHub webhooks for pull request events.
    All webhooks are verified using HMAC SHA-256 signature verification.

    Headers required:
        - X-Hub-Signature-256: GitHub signature for payload verification
        - X-GitHub-Event: Event type (must be "pull_request")
        - X-GitHub-Delivery: Unique delivery ID

    Returns:
        Dictionary with processing status and message

    Raises:
        HTTPException:
            - 400: Missing required headers or invalid payload
            - 401: Invalid webhook signature

    Example:
        This endpoint is called by GitHub when PR events occur.
        See docs/guides/github-webhook-setup.md for configuration.
    """
    return await handle_github_webhook(
        request, x_hub_signature_256, x_github_event, x_github_delivery
    )
