from datetime import datetime
import json
from typing import Union
from pydantic import BaseModel

class _Base(BaseModel):
    ts: datetime

class PowerReading(_Base):
    v: float; i: float; p: float; e: float; pf: float

class LevelReading(_Base):
    cm: float

class FlowReading(_Base):
    lpm: float
    total_l: float

class WeatherReading(_Base):
    t: float
    rh: float
    p: float

class PresenceReading(_Base):
    present: bool

class StatusReading(_Base):
    rssi: int
    uptime_s: int
    fw: str

Reading = Union[PowerReading, LevelReading, FlowReading,
                WeatherReading, PresenceReading, StatusReading]

_DISPATCH: dict[str, type[BaseModel]] = {
    "power":    PowerReading,
    "level":    LevelReading,
    "flow":     FlowReading,
    "weather":  WeatherReading,
    "presence": PresenceReading,
    "status":   StatusReading,
}

def parse_payload(metric: str, raw: bytes) -> Reading:
    cls = _DISPATCH.get(metric)
    if cls is None:
        raise ValueError(f"unknown metric: {metric}")
    return cls.model_validate(json.loads(raw))
