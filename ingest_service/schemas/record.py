from pydantic import BaseModel, Field, field_validator
from typing import Union, List, Optional

EVENT_TYPES = (  # same as defined by IoT generator code
    "platform_extension_ticks",
    "platform_extension_mm",
    "battery_charge",
    "platform_height_mm",
)


class DeviceStartup(BaseModel):
    event_type: str  # must be "device_startup"
    serial: str
    provision_token: str
    firmware: Optional[str] = None
    timestamp: float

    @field_validator("event_type")
    @classmethod
    def _must_be_startup(cls, v: str) -> str:
        if v != "device_startup":
            raise ValueError("event_type must be 'device_startup'")
        return v


class Record(BaseModel):  # using base model for validation and type safety
    device_id: int
    event_type: str = Field(pattern="^(" + "|".join(EVENT_TYPES) + ")$")
    value: Union[int, float]
    timestamp: float

    @field_validator("value")
    @classmethod
    def enforce_ranges(cls, v, info):
        et = info.data.get("event_type")
        val = float(v)
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
    raw_id: int
    processed_id: int | None = None
    status: str


EventOrList = Record | list[Record]
