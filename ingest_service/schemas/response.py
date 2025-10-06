"""
Response schemas for the IoT Ingest Service API.

This module defines Pydantic models for API responses, providing:
- Type validation
- Automatic serialization to JSON
- OpenAPI schema generation
"""
from pydantic import BaseModel


class StatusResponse(BaseModel):
    """
    Simple status response model.
    
    This is used primarily by the health check endpoint to indicate
    that the service is running correctly.
    
    Attributes:
        status: Status string, defaults to "ok"
    """
    status: str = "ok"
