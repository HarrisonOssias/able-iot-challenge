"""
Ingest route handler for IoT device telemetry and provisioning.

This module defines the FastAPI route that handles incoming IoT data:
- Accepts both single events and batches
- Handles JSON parsing errors gracefully
- Routes requests to the appropriate service methods
- Returns processing results with status codes
"""
from fastapi import APIRouter, Request
from typing import Any, List
from db.pool import get_pool
from services.ingest_services import IngestService

# Create router with prefix and OpenAPI tag
router = APIRouter(prefix="/ingest", tags=["ingest"])


@router.post("")
async def ingest(req: Request):
    """
    Process incoming IoT device data (telemetry or provisioning).
    
    This endpoint:
    - Accepts both single events and batches as JSON
    - Handles malformed JSON by storing it as raw text
    - Processes each event through validation and storage pipeline
    - Returns processing results with status codes
    
    Returns:
        List of processing results with status codes:
        - "ok": Successfully processed
        - "invalid": Failed validation
        - "error": Database error
        - "provisioned": Device successfully provisioned
        - "unauthorized": Invalid provisioning token
    """
    # Get database connection pool
    pool = await get_pool()  # Guarantees pool exists and is healthy
    
    # Create service instance with DB connection
    svc = IngestService(pool)
    
    try:
        # Try to parse request body as JSON
        body: Any = await req.json()
    except Exception:
        # If JSON parsing fails, treat the body as raw text
        raw_text = (await req.body()).decode("utf-8", errors="replace")
        return [await svc.ingest_one({"_raw": raw_text})]
    
    # Handle both batch and single-event requests
    if isinstance(body, list):
        return await svc.ingest_many(body)
    else:
        # Wrap single events in a list for consistent response format
        return [await svc.ingest_one(body)]
