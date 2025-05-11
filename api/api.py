from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Any, Optional
import os
import json
import logging
from pydantic import BaseModel

# Import registry and search modules
from AutonomousSphere.registry import registry
from AutonomousSphere.search import router as search_router, startup_event

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="AutonomousSphere API",
    description="API for communicating with the Autonomous Sphere Matrix AppService",
    version="0.1.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Modify in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Root endpoint
@app.get("/")
async def root():
    return {"message": "Welcome to AutonomousSphere API"}

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# Include registry routes
app.include_router(registry.router, prefix="/registry", tags=["registry"])

# Include search routes
app.include_router(search_router, prefix="/search", tags=["search"])

# Register startup event
@app.on_event("startup")
async def on_startup():
    await startup_event()

# Error handling
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {str(exc)}")
    return {"error": "Internal server error", "detail": str(exc)}, 500

# Main function to run the app
def start_api(host="0.0.0.0", port=8000):
    import uvicorn
    uvicorn.run(app, host=host, port=port)

if __name__ == "__main__":
    start_api()