import asyncio
import pytest

from services.ingest_services import IngestService


@pytest.mark.asyncio
async def test_ingest_invalid_schema(monkeypatch):
    """Records with out-of-range values are rejected by Pydantic validation.

    We intentionally send battery_charge=1234 (invalid) and assert the
    service returns status="invalid" without attempting DB writes.
    """
    service = IngestService(pool=None)  # pool not used due to early validation failure
    # battery_charge out-of-range value triggers validation error
    result = await service.ingest_one({
        "device_id": 1,
        "event_type": "battery_charge",
        "value": 1234,
        "timestamp": 1.0,
    })
    assert result.status == "invalid"


@pytest.mark.asyncio
async def test_route_startup_happy(monkeypatch):
    """device_startup is routed to the provisioning branch and returns device id."""
    service = IngestService(pool=None)

    # insert_raw returns a raw_id
    raw_f = asyncio.Future(); raw_f.set_result(10)
    monkeypatch.setattr("services.ingest_services.insert_raw", lambda pool, payload: raw_f, raising=False)
    # bypass token check
    monkeypatch.setattr("services.ingest_services._verify_token", lambda s, t: True, raising=False)
    # provisioning returns device id
    dev_f = asyncio.Future(); dev_f.set_result(42)
    monkeypatch.setattr("services.ingest_services.get_or_create_device_by_serial", lambda pool, s: dev_f, raising=False)

    result = await service.ingest_one({
        "event_type": "device_startup",
        "serial": "SER",
        "provision_token": "TOK",
        "timestamp": 1.0,
    })
    assert result.status == "provisioned"
    assert result.processed_id == 42


@pytest.mark.asyncio
async def test_telemetry_happy(monkeypatch):
    """Happy path telemetry: raw -> type lookup -> ensure device -> processed insert."""
    service = IngestService(pool=None)

    raw_f = asyncio.Future(); raw_f.set_result(11)
    monkeypatch.setattr("services.ingest_services.insert_raw", lambda pool, payload: raw_f, raising=False)

    type_f = asyncio.Future(); type_f.set_result(3)
    monkeypatch.setattr("services.ingest_services.get_record_type_id", lambda pool, et: type_f, raising=False)

    noop = asyncio.Future(); noop.set_result(None)
    monkeypatch.setattr("services.ingest_services.ensure_device_exists_by_id", lambda pool, did: noop, raising=False)

    pid_f = asyncio.Future(); pid_f.set_result(99)
    monkeypatch.setattr("services.ingest_services.insert_processed", lambda pool, **kw: pid_f, raising=False)

    result = await service.ingest_one({
        "device_id": 1,
        "event_type": "battery_charge",
        "value": 50.0,
        "timestamp": 1.0,
    })
    assert result.status == "ok"
    assert result.processed_id == 99


@pytest.mark.asyncio
async def test_legacy_ticks_vs_new_mm(monkeypatch):
    """Legacy ticks and new mm both flow through, using the same pipeline.

    We don't hit the DB; instead we ensure that for ticks and mm we still call
    type lookup and insert_processed with the provided float value. Conversion
    to mm happens in SQL views, not at write-time, so here we just verify
    that both event types pass validation and reach insert_processed.
    """
    service = IngestService(pool=None)

    raw_f = asyncio.Future(); raw_f.set_result(21)
    monkeypatch.setattr("services.ingest_services.insert_raw", lambda pool, payload: raw_f, raising=False)

    type_calls = []
    async def fake_get_type(pool, et):
        type_calls.append(et); f=asyncio.Future(); f.set_result(7); return f
    monkeypatch.setattr("services.ingest_services.get_record_type_id", fake_get_type, raising=False)

    monkeypatch.setattr("services.ingest_services.ensure_device_exists_by_id", lambda pool, did: asyncio.Future(), raising=False)

    inserted = []
    async def fake_insert_processed(pool, **kw):
        inserted.append(kw); f=asyncio.Future(); f.set_result(555); return f
    monkeypatch.setattr("services.ingest_services.insert_processed", fake_insert_processed, raising=False)

    # legacy ticks
    res1 = await service.ingest_one({
        "device_id": 1,
        "event_type": "platform_extension_ticks",
        "value": 1000,
        "timestamp": 1.0,
    })
    # new mm
    res2 = await service.ingest_one({
        "device_id": 1,
        "event_type": "platform_extension_mm",
        "value": 12.5,
        "timestamp": 1.0,
    })

    assert res1.status == res2.status == "ok"
    # we looked up both types
    assert set(type_calls) == {"platform_extension_ticks", "platform_extension_mm"}
    # both inserts were attempted with the provided values (conversion is a view concern)
    values = [i["value"] for i in inserted]
    assert 1000.0 in values and 12.5 in values


