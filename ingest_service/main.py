from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from db.pool import init_pool, close_pool
from routes.status import router as status_router
from routes.ingest import router as ingest_router
from routes.metrics import router as metrics_router
import logging

log = logging.getLogger(__name__)

app = FastAPI(title="IoT Ingest API")

app.include_router(status_router)
app.include_router(ingest_router)
app.include_router(metrics_router)

# Serve a tiny static dashboard
app.mount("/dashboard", StaticFiles(directory="static", html=True), name="dashboard")


@app.on_event("startup")
async def on_startup():
    log.info("Starting up IoT Ingest API...")
    await init_pool()   # <- runs connectivity check here


@app.on_event("shutdown")
async def on_shutdown():
    await close_pool()
