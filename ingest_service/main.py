"""
Main FastAPI application entry point for the IoT Ingest Service.

This module sets up the FastAPI application with all routers, middleware,
and lifecycle event handlers. It's responsible for:
1. Initializing and closing the database connection pool
2. Mounting all API routes (status, ingest, metrics)
3. Serving the static dashboard for real-time monitoring
"""
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from db.pool import init_pool, close_pool
from routes.status import router as status_router
from routes.ingest import router as ingest_router
from routes.metrics import router as metrics_router
import logging

log = logging.getLogger(__name__)

# Create the FastAPI application with metadata
app = FastAPI(title="IoT Ingest API")

# Register all route handlers
app.include_router(status_router)
app.include_router(ingest_router)
app.include_router(metrics_router)

# Serve a static dashboard for real-time monitoring via SSE
app.mount("/dashboard", StaticFiles(directory="static", html=True), name="dashboard")


@app.on_event("startup")
async def on_startup():
    """
    Application startup handler that initializes resources.
    
    This runs when the FastAPI app starts and:
    - Sets up logging
    - Initializes the database connection pool
    - Performs a health check on the database
    """
    log.info("Starting up IoT Ingest API...")
    await init_pool()   # <- runs connectivity check here


@app.on_event("shutdown")
async def on_shutdown():
    """
    Application shutdown handler that cleans up resources.
    
    This runs when the FastAPI app shuts down and:
    - Closes the database connection pool gracefully
    """
    await close_pool()
