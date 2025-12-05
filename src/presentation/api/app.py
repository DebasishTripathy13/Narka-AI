"""FastAPI application factory."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from .routes import router
from .middleware import LoggingMiddleware, RateLimitMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup
    print("🚀 Robin API starting up...")
    yield
    # Shutdown
    print("👋 Robin API shutting down...")


def create_app(
    title: str = "Robin Dark Web OSINT API",
    version: str = "2.0.0",
    debug: bool = False
) -> FastAPI:
    """
    Create and configure the FastAPI application.
    
    Args:
        title: API title
        version: API version
        debug: Enable debug mode
        
    Returns:
        Configured FastAPI application
    """
    app = FastAPI(
        title=title,
        description="""
        Robin is an AI-powered dark web OSINT (Open Source Intelligence) tool
        that provides search, scraping, and analysis capabilities for .onion sites.
        
        ## Features
        
        - 🔍 **Search**: Search across multiple dark web search engines
        - 📄 **Scrape**: Extract content from .onion URLs
        - 🤖 **Analyze**: AI-powered analysis and summarization
        - 📊 **Export**: Export results in JSON, CSV, STIX, or PDF formats
        - 🔔 **Alerts**: Set up keyword alerts and scheduled searches
        
        ## Authentication
        
        API key authentication is required for all endpoints.
        Include your API key in the `X-API-Key` header.
        """,
        version=version,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Custom middleware
    app.add_middleware(LoggingMiddleware)
    
    # Include routers
    app.include_router(router, prefix="/api/v1")
    
    return app


# Default application instance
app = create_app()
