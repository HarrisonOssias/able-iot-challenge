# routes/ingest.py
from fastapi import APIRouter, Request
from typing import Any
from db.pool import get_pool
from services.ingest_services import IngestService

router = APIRouter(prefix="/ingest", tags=["ingest"])


@router.post("")
async def ingest(req: Request):
    pool = await get_pool()           # ← guarantees pool exists
    svc = IngestService(pool)
    try:
        body: Any = await req.json()
    except Exception:
        raw_text = (await req.body()).decode("utf-8", errors="replace")
        return [await svc.ingest_one({"_raw": raw_text})]
    if isinstance(body, list):
        return await svc.ingest_many(body)
    return [await svc.ingest_one(body)]
