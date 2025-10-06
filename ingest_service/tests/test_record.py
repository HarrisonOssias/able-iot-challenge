import pytest

from schemas.record import Record, DeviceStartup


def test_record_valid_mm():
    r = Record(device_id=1, event_type="platform_extension_mm", value=10.5, timestamp=123.0)
    assert r.value == 10.5


@pytest.mark.parametrize("val", [-151, 151.1])
def test_record_mm_out_of_range(val):
    with pytest.raises(ValueError):
        Record(device_id=1, event_type="platform_extension_mm", value=val, timestamp=1.0)


def test_startup_event_type_enforced():
    with pytest.raises(ValueError):
        DeviceStartup(event_type="battery_charge", serial="S", provision_token="t", timestamp=1.0)


