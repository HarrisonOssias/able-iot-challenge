"""
Metrics API routes for IoT device telemetry.

This module provides endpoints for querying device metrics:
- Average extension in millimeters
- Extension vs. retraction counts
- Battery level summaries
- Platform height statistics
- Real-time metrics via Server-Sent Events (SSE)

All metrics are calculated using SQL views that handle legacy/new format unification.
"""
from fastapi import APIRouter
from psycopg.rows import dict_row
from db.pool import get_pool
from fastapi.responses import StreamingResponse
import asyncio
import json
from typing import List, Dict, Any

# Create router with prefix and OpenAPI tag
router = APIRouter(prefix="/metrics", tags=["metrics"])


async def _query(sql: str) -> List[Dict[str, Any]]:
    """
    Execute a SQL query and return results as a list of dictionaries.
    
    Args:
        sql: SQL query string to execute
        
    Returns:
        List of dictionaries, each representing a row with column names as keys
    """
    pool = await get_pool()
    async with pool.connection() as conn:
        async with conn.cursor(row_factory=dict_row) as cur:
            await cur.execute(sql)
            rows = await cur.fetchall()
            return rows


@router.get("/avg-extension-mm")
async def avg_extension_mm():
    """
    Get average extension in millimeters for each device.
    
    This endpoint queries the metric_avg_extension_mm view which:
    - Unifies legacy ticks and new mm formats at query time
    - Calculates the average extension per device
    - Returns results ordered by device_id
    
    Returns:
        List of objects with device_id and avg_extension_mm fields
    """
    return await _query("SELECT * FROM metric_avg_extension_mm ORDER BY device_id")


@router.get("/extension-vs-retraction")
async def extension_vs_retraction():
    """
    Get counts of extension vs. retraction events for each device.
    
    This endpoint queries the metric_extension_vs_retraction view which:
    - Analyzes sequential readings to detect direction changes
    - Counts extensions (increasing mm) and retractions (decreasing mm)
    - Returns results ordered by device_id
    
    Returns:
        List of objects with device_id, extensions, and retractions fields
    """
    return await _query("SELECT * FROM metric_extension_vs_retraction ORDER BY device_id")


@router.get("/battery-summary")
async def battery_summary():
    """
    Get battery level statistics for each device.
    
    This endpoint queries the metric_battery_summary view which:
    - Calculates min, max, and average battery levels
    - Includes the timestamp of the most recent reading
    - Returns results ordered by device_id
    
    Returns:
        List of objects with device_id, min_pct, max_pct, avg_pct, and last_seen fields
    """
    return await _query("SELECT * FROM metric_battery_summary ORDER BY device_id")


@router.get("/platform-height")
async def platform_height():
    """
    Get platform height statistics for each device.
    
    This endpoint queries the metric_platform_height view which:
    - Calculates min, max, and average platform heights
    - Returns results ordered by device_id
    
    Returns:
        List of objects with device_id, min_height_mm, max_height_mm, and avg_height_mm fields
    """
    return await _query("SELECT * FROM metric_platform_height ORDER BY device_id")


@router.get("/stream")
async def stream_metrics():
    """
    Stream real-time metrics updates using Server-Sent Events (SSE).
    
    This endpoint:
    - Establishes a persistent connection with the client
    - Sends metrics updates every second
    - Formats data as SSE events
    - Handles errors gracefully with error events
    
    The client should use the EventSource API to consume this stream.
    
    Returns:
        StreamingResponse: A streaming HTTP response with text/event-stream content type
    """
    async def event_generator():
        """Generate SSE events with metrics data."""
        while True:
            try:
                # Query all metrics views
                avg = await _query("SELECT * FROM metric_avg_extension_mm ORDER BY device_id")
                exr = await _query("SELECT * FROM metric_extension_vs_retraction ORDER BY device_id")
                bat = await _query("SELECT * FROM metric_battery_summary ORDER BY device_id")
                hgt = await _query("SELECT * FROM metric_platform_height ORDER BY device_id")
                
                # Combine all metrics into a single payload
                payload = {"avg": avg, "exret": exr, "battery": bat, "height": hgt}
                
                # Format as SSE data event
                yield f"data: {json.dumps(payload, default=str)}\n\n"
            except Exception as e:
                # Send error event if something goes wrong
                yield f"event: error\ndata: {json.dumps({'error': str(e)})}\n\n"
                
            # Wait before sending the next update
            await asyncio.sleep(1)

    # Return a streaming response with appropriate content type
    return StreamingResponse(event_generator(), media_type="text/event-stream")

