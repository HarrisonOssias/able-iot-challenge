"""
Core service for ingesting IoT device telemetry and provisioning messages.

This module handles:
- Device provisioning with HMAC token verification
- Telemetry ingestion for both legacy and new formats
- Data validation and error handling
- Database write operations
- Support for both single events and batches

The service is designed to be resilient, handling various error conditions
and providing clear status codes for all operations.
"""
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
    """
    Generate an HMAC-SHA256 signature for a device serial number.
    
    Args:
        secret: The secret key for HMAC signing
        serial: The device serial number to sign
        
    Returns:
        str: Hexadecimal digest of the HMAC signature
    """
    return hmac.new(secret.encode(), serial.encode(), hashlib.sha256).hexdigest()


def _verify_token(serial: str, token: str) -> bool:
    """
    Verify a device provisioning token against its serial number.
    
    This function:
    1. Generates the expected token using the shared secret
    2. Compares it to the provided token using constant-time comparison
       to prevent timing attacks
    
    Args:
        serial: The device serial number
        token: The provisioning token to verify
        
    Returns:
        bool: True if the token is valid, False otherwise
    """
    expected = _sign_serial(settings.provision_secret, serial)
    # Use constant-time comparison to prevent timing attacks
    return hmac.compare_digest(expected, token)


class IngestService:
    """
    Service for processing IoT device messages.
    
    This service handles both device provisioning and telemetry messages,
    validating them and storing them in the database.
    """
    
    def __init__(self, pool: AsyncConnectionPool):
        """
        Initialize the service with a database connection pool.
        
        Args:
            pool: PostgreSQL connection pool for database operations
        """
        self.pool = pool

    async def _handle_startup(self, payload: dict[str, Any], raw_id: int) -> IngestResult:
        """
        Process a device startup/provisioning message.
        
        This method:
        1. Validates the startup message schema
        2. Verifies the provisioning token
        3. Creates or retrieves the device record
        
        Args:
            payload: Raw device startup message
            raw_id: ID of the raw record in the database
            
        Returns:
            IngestResult: Processing result with status code
        """
        try:
            # Validate the startup message schema
            startup = DeviceStartup(**payload)
        except ValidationError as ve:
            # Log validation errors and return invalid status
            await upsert_error(self.pool, raw_id, f"startup_validation_error: {ve.errors()}")
            return IngestResult(raw_id=raw_id, status="invalid")

        # Verify the provisioning token
        if not _verify_token(startup.serial, startup.provision_token):
            await upsert_error(self.pool, raw_id, "startup_auth_error: invalid token")
            return IngestResult(raw_id=raw_id, status="unauthorized")

        try:
            # Create or retrieve the device record
            device_id = await get_or_create_device_by_serial(self.pool, startup.serial)
            # You could also write an audit row or firmware table here if you like
            return IngestResult(raw_id=raw_id, processed_id=device_id, status="provisioned")
        except Exception as e:
            # Log database errors
            await upsert_error(self.pool, raw_id, f"startup_db_error: {e}")
            return IngestResult(raw_id=raw_id, status="error")

    async def ingest_one(self, payload: dict[str, Any]) -> IngestResult:
        """
        Process a single IoT device message (telemetry or startup).
        
        This method handles the entire ingestion pipeline:
        1. Routes startup events to the provisioning flow
        2. Validates telemetry events before database operations
        3. Stores valid events in both raw and processed tables
        4. Handles errors at all stages
        
        The method is designed to fail gracefully, recording errors
        and returning appropriate status codes.
        
        Args:
            payload: Raw device message (telemetry or startup)
            
        Returns:
            IngestResult: Processing result with status code
        """
        # Special handling for device_startup events
        if payload.get("event_type") == "device_startup":
            # Always log the raw payload first for startup events
            raw_id = await insert_raw(self.pool, payload)
            return await self._handle_startup(payload, raw_id)

        # Telemetry path: validate BEFORE any DB writes to avoid storing invalid data
        try:
            # Validate against the Record schema
            evt = Record(**payload)
        except ValidationError as ve:
            # Handle validation errors
            if self.pool is None:
                # For unit tests without a DB pool
                return IngestResult(status="invalid")
                
            # Log the raw payload and error for observability
            raw_id = await insert_raw(self.pool, payload)
            await upsert_error(self.pool, raw_id, f"validation_error: {ve.errors()}")
            return IngestResult(raw_id=raw_id, status="invalid")

        # Valid telemetry: proceed with DB writes
        raw_id = await insert_raw(self.pool, payload)
        try:
            # Get the record type ID (creates if needed)
            type_id = await get_record_type_id(self.pool, evt.event_type)
            
            # Ensure the device exists (auto-creates for legacy numeric IDs)
            await ensure_device_exists_by_id(self.pool, evt.device_id)

            # Insert the processed record
            pid = await insert_processed(
                self.pool,
                device_id=evt.device_id,
                raw_id=raw_id,
                timestamp_sec=evt.timestamp,
                type_id=type_id,
                value=float(evt.value),  # Ensure consistent float type
            )
            return IngestResult(raw_id=raw_id, processed_id=pid, status="ok")
        except Exception as e:
            # Log database errors
            await upsert_error(self.pool, raw_id, f"db_error: {e}")
            return IngestResult(raw_id=raw_id, status="error")

    async def ingest_many(self, payloads: Iterable[dict]) -> list[IngestResult]:
        """
        Process multiple IoT device messages in sequence.
        
        This method processes each message individually, collecting
        the results into a list.
        
        Args:
            payloads: Iterable of raw device messages
            
        Returns:
            list[IngestResult]: List of processing results
        """
        return [await self.ingest_one(p) for p in payloads]
