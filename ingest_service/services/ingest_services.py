from typing import Any, Iterable
from pydantic import ValidationError
from psycopg_pool import AsyncConnectionPool
import hmac
import hashlib
from schemas.record import Record, IngestResult, DeviceStartup
from db.models.raw_model import insert_raw
from db.models.error_model import upsert_error
from db.models.processed_model import get_record_type_id, insert_processed
from db.models.device_model import get_or_create_device_by_serial, ensure_device_exists_by_id
from config.settings import settings


def _sign_serial(secret: str, serial: str) -> str:
    return hmac.new(secret.encode(), serial.encode(), hashlib.sha256).hexdigest()


def _verify_token(serial: str, token: str) -> bool:
    expected = _sign_serial(settings.provision_secret, serial)
    # constant-time compare
    return hmac.compare_digest(expected, token)


class IngestService:
    def __init__(self, pool: AsyncConnectionPool):
        self.pool = pool

    async def _handle_startup(self, payload: dict[str, Any], raw_id: int) -> IngestResult:
        try:
            startup = DeviceStartup(**payload)
        except ValidationError as ve:
            await upsert_error(self.pool, raw_id, f"startup_validation_error: {ve.errors()}")
            return IngestResult(raw_id=raw_id, status="invalid")

        if not _verify_token(startup.serial, startup.provision_token):
            await upsert_error(self.pool, raw_id, "startup_auth_error: invalid token")
            return IngestResult(raw_id=raw_id, status="unauthorized")

        try:
            device_id = await get_or_create_device_by_serial(self.pool, startup.serial)
            # You could also write an audit row or firmware table here if you like
            return IngestResult(raw_id=raw_id, processed_id=device_id, status="provisioned")
        except Exception as e:
            await upsert_error(self.pool, raw_id, f"startup_db_error: {e}")
            return IngestResult(raw_id=raw_id, status="error")

    async def ingest_one(self, payload: dict[str, Any]) -> IngestResult:
        # device_startup branch keeps logging the raw payload first (tests monkeypatch this)
        if payload.get("event_type") == "device_startup":
            raw_id = await insert_raw(self.pool, payload)
            return await self._handle_startup(payload, raw_id)

        # Telemetry path: validate BEFORE any DB writes so invalid payloads do not touch DB
        try:
            evt = Record(**payload)
        except ValidationError as ve:
            # In unit tests we may not have a pool; just report invalid without DB writes
            if self.pool is None:
                return IngestResult(status="invalid")
            # If a pool exists, optionally record raw + error for observability
            raw_id = await insert_raw(self.pool, payload)
            await upsert_error(self.pool, raw_id, f"validation_error: {ve.errors()}")
            return IngestResult(raw_id=raw_id, status="invalid")

        # Valid telemetry: proceed with DB writes
        raw_id = await insert_raw(self.pool, payload)
        try:
            type_id = await get_record_type_id(self.pool, evt.event_type)
            # Ensure the device row exists for legacy generators that send numeric ids
            await ensure_device_exists_by_id(self.pool, evt.device_id)

            pid = await insert_processed(
                self.pool,
                device_id=evt.device_id,
                raw_id=raw_id,
                timestamp_sec=evt.timestamp,
                type_id=type_id,
                value=float(evt.value),
            )
            return IngestResult(raw_id=raw_id, processed_id=pid, status="ok")
        except Exception as e:
            await upsert_error(self.pool, raw_id, f"db_error: {e}")
            return IngestResult(raw_id=raw_id, status="error")

    async def ingest_many(self, payloads: Iterable[dict]) -> list[IngestResult]:
        return [await self.ingest_one(p) for p in payloads]
