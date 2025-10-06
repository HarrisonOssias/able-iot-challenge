"""
status check route for the IoT Ingest Service.

This module provides a simple status check endpoint that:
- Returns a 200 OK response when the service is statusy
- Can be used by load balancers and monitoring systems
- Does not require database connectivity (DB status is checked separately)
"""
from fastapi import APIRouter
from schemas.response import StatusResponse

# Create router with OpenAPI tag for grouping in documentation
router = APIRouter(tags=["status"])


@router.get("/status", response_model=StatusResponse)
async def status():
    """
    Simple status check endpoint.
    
    Returns a 200 OK response with {"status": "ok"} when the service is running.
    This endpoint is lightweight and doesn't check database connectivity.
    
    Returns:
        StatusResponse: A simple response object with status="ok"
    """
    return StatusResponse()  # Returns {"status": "ok"}
