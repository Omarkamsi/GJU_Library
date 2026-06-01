import pytest
from pydantic import ValidationError
from ingest.schemas import (
    PowerReading, LevelReading, FlowReading, WeatherReading,
    PresenceReading, StatusReading, parse_payload,
)

def test_power_reading_valid():
    p = PowerReading.model_validate({
        "ts": "2026-05-08T10:00:00Z", "v": 420.5, "i": 1.9,
        "p": 798.0, "e": 12.43, "pf": 0.97,
    })
    assert p.p == 798.0

def test_flow_reading_valid():
    f = FlowReading.model_validate({
        "ts": "2026-05-08T10:00:00Z", "lpm": 4.2, "total_l": 1842.5,
    })
    assert f.lpm == 4.2

def test_parse_payload_dispatches_by_metric():
    obj = parse_payload("flow", b'{"ts":"2026-05-08T10:00:00Z","lpm":4.2,"total_l":1.0}')
    assert isinstance(obj, FlowReading)

def test_invalid_payload_raises():
    with pytest.raises(ValidationError):
        PowerReading.model_validate({"ts": "not-a-date"})
