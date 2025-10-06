from fastapi import APIRouter
from psycopg.rows import dict_row
from db.pool import get_pool
from fastapi.responses import StreamingResponse
import asyncio
import json

router = APIRouter(prefix="/metrics", tags=["metrics"])


async def _query(sql: str):
    pool = await get_pool()
    async with pool.connection() as conn:
        async with conn.cursor(row_factory=dict_row) as cur:
            await cur.execute(sql)
            rows = await cur.fetchall()
            return rows


@router.get("/avg-extension-mm")
async def avg_extension_mm():
    return await _query("SELECT * FROM metric_avg_extension_mm ORDER BY device_id")


@router.get("/extension-vs-retraction")
async def extension_vs_retraction():
    return await _query("SELECT * FROM metric_extension_vs_retraction ORDER BY device_id")


@router.get("/battery-summary")
async def battery_summary():
    return await _query("SELECT * FROM metric_battery_summary ORDER BY device_id")


@router.get("/platform-height")
async def platform_height():
    return await _query("SELECT * FROM metric_platform_height ORDER BY device_id")


@router.get("/stream")
async def stream_metrics():
    async def event_generator():
        while True:
            try:
                avg = await _query("SELECT * FROM metric_avg_extension_mm ORDER BY device_id")
                exr = await _query("SELECT * FROM metric_extension_vs_retraction ORDER BY device_id")
                bat = await _query("SELECT * FROM metric_battery_summary ORDER BY device_id")
                hgt = await _query("SELECT * FROM metric_platform_height ORDER BY device_id")
                payload = {"avg": avg, "exret": exr, "battery": bat, "height": hgt}
                yield f"data: {json.dumps(payload, default=str)}\n\n"
            except Exception as e:
                yield f"event: error\ndata: {json.dumps({'error': str(e)})}\n\n"
            await asyncio.sleep(1)

    return StreamingResponse(event_generator(), media_type="text/event-stream")


