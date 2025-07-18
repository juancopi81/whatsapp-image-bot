"""FastAPI application for the WhatsApp Image Stylization Bot.

This module creates and configures the FastAPI application,
registers the API routes, and includes routes for the root endpoint and a simple health check.
The API documentation is automatically generated and available at /docs.
"""

from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel

from .api import api_router
from .config import Config
from .services.image_processor import shutdown_clients
from .utils.logger import get_logger

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage startup and shutdown events."""
    yield
    logger.info("Application shutting down. Closing clients.")
    await shutdown_clients()


# --- Pydantic Models for Responses ---
class HealthResponse(BaseModel):
    """Health check response model."""

    status: str = "ok"


# --- FastAPI Application Instance ---
# The 'app' object is the main point of interaction to create all your API.
# Title, description, and version will appear in the automatic docs.
app = FastAPI(
    title="WhatsApp Image Styler API",
    description="API for processing and stylizing images from WhatsApp.",
    version="0.1.0",
    lifespan=lifespan,
)


# Load configuration (can be used in other parts of the app if needed)
app_config = Config()

# --- Include API Routes ---
# This makes all routes defined in api_router available
# under the /api prefix.
app.include_router(api_router, prefix="/api")

# --- API Endpoints ---


@app.get("/")
def read_root():
    """Root endpoint that returns a welcome message."""
    return {"message": "Welcome to the Image Styler API!"}


@app.get("/health", response_model=HealthResponse)
def health_check():
    """Returns the operational status of the application.

    This is used by monitoring services to check if the app is alive.
    """
    return HealthResponse()


# --- Run the App ---
if __name__ == "__main__":
    uvicorn.run(
        "src.whatsapp_image_bot.app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
