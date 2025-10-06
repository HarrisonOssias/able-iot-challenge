"""
Data schemas for IoT device telemetry and provisioning.

This module defines Pydantic models that:
- Validate incoming IoT device data
- Enforce data type constraints
- Apply business rules (value ranges)
- Handle both legacy and new message formats
- Support device provisioning flow

The schemas are used for validation before database operations.
"""
from pydantic import BaseModel, Field, field_validator
from typing import Union, List, Optional

# Supported event types for telemetry messages
# These match the types produced by the IoT device generator
EVENT_TYPES = (
    "platform_extension_ticks",  # Legacy format (0-3000 ticks)
    "platform_extension_mm",     # New format (-150 to 150 mm)
    "battery_charge",            # Battery percentage (0-100%)
    "platform_height_mm",        # Platform height (0-200 mm)
)


class DeviceStartup(BaseModel):
    """
    Device provisioning/startup event schema.
    
    This schema validates the initial provisioning message sent by devices
    when they first connect to the system. It includes authentication via
    an HMAC token.
    
    Attributes:
        event_type: Must be exactly "device_startup"
        serial: Unique device serial number
        provision_token: HMAC token for authentication
        firmware: Optional firmware version string
        timestamp: Event timestamp in seconds since epoch
    """
    event_type: str  # Must be "device_startup"
    serial: str      # Unique device identifier
    provision_token: str  # HMAC authentication token
    firmware: Optional[str] = None  # Optional firmware version
    timestamp: float  # Event timestamp

    @field_validator("event_type")
    @classmethod
    def _must_be_startup(cls, v: str) -> str:
        """Ensure event_type is exactly 'device_startup'."""
        if v != "device_startup":
            raise ValueError("event_type must be 'device_startup'")
        return v


class Record(BaseModel):
    """
    IoT device telemetry record schema.
    
    This schema validates telemetry data from IoT devices, including:
    - Device identification
    - Event type classification
    - Value range validation
    - Timestamp validation
    
    It handles both legacy and new format messages through value range validation.
    
    Attributes:
        device_id: Numeric device identifier
        event_type: Type of telemetry event (must be one of EVENT_TYPES)
        value: Numeric measurement value
        timestamp: Event timestamp in seconds since epoch
    """
    device_id: int  # Device identifier
    event_type: str = Field(pattern="^(" + "|".join(EVENT_TYPES) + ")$")  # Event type validation
    value: Union[int, float]  # Measurement value
    timestamp: float  # Event timestamp

    @field_validator("value")
    @classmethod
    def enforce_ranges(cls, v, info):
        """
        Validate value ranges based on event_type.
        
        Different event types have different valid ranges:
        - platform_extension_ticks: 0 to 3000 (legacy format)
        - platform_extension_mm: -150 to 150 (new format, negative = left)
        - battery_charge: 0 to 100 (percentage)
        - platform_height_mm: 0 to 200 (millimeters)
        
        Args:
            v: The value to validate
            info: ValidationInfo object containing other fields
            
        Returns:
            The validated value
            
        Raises:
            ValueError: If the value is outside the valid range for its event_type
        """
        et = info.data.get("event_type")
        val = float(v)
        
        # Validate based on event type
        if et == "platform_extension_ticks" and not (0 <= val <= 3000):
            raise ValueError("ticks out of range 0..3000")
        if et == "platform_extension_mm" and not (-150 <= val <= 150):
            raise ValueError("mm out of range -150..150")
        if et == "battery_charge" and not (0 <= val <= 100):
            raise ValueError("% out of range 0..100")
        if et == "platform_height_mm" and not (0 <= val <= 200):
            raise ValueError("height out of range 0..200")
            
        return v


class IngestResult(BaseModel):
    """
    Result of ingesting a telemetry or provisioning message.
    
    This schema is used for API responses after processing a message.
    
    Attributes:
        raw_id: ID of the raw record in the database (optional)
        processed_id: ID of the processed record or device ID for provisioning (optional)
        status: Processing status ("ok", "invalid", "error", "provisioned", "unauthorized")
    """
    raw_id: Optional[int] = None  # ID in raw_record table
    processed_id: Optional[int] = None  # ID in processed_record table or device ID
    status: str  # Processing status


# Type alias for a single record or list of records
EventOrList = Record | list[Record]
