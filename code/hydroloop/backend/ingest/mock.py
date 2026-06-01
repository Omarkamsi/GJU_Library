"""Synthetic data generator. Used when MOCK=1 so frontend dev is unblocked
before real hardware is online. Tracks running totals between ticks."""
import random
from datetime import datetime, timezone
from typing import Iterable

_FLOW_DEVICES = [
    "flow-eng-bldg", "flow-lib", "flow-cs",
    "flow-arch", "flow-business", "flow-medical",
]
_running_total: dict[str, float] = {d: 0.0 for d in _FLOW_DEVICES}
_kwh_total: float = 0.0
_water_level_cm: float = 42.0

def generate_tick() -> Iterable[dict]:
    """Yield one synthetic reading per (device, metric) for a single tick."""
    global _kwh_total, _water_level_cm
    now = datetime.now(timezone.utc)

    # Wheel: power
    p = random.uniform(700, 900)
    _kwh_total += p / 3600 / 1000 * 10
    yield {
        "device_id": "wheel-01", "metric": "power", "ts": now,
        "payload": {
            "v": round(random.uniform(415, 425), 1),
            "i": round(p / 420, 2),
            "p": round(p, 1),
            "e": round(_kwh_total, 3),
            "pf": round(random.uniform(0.94, 0.99), 2),
        },
    }

    # Wheel: level
    drift = -random.uniform(0.0, 0.05)
    if _water_level_cm < 35:
        _water_level_cm = 50.0
    else:
        _water_level_cm += drift
    yield {
        "device_id": "wheel-01", "metric": "level", "ts": now,
        "payload": {"cm": round(_water_level_cm, 1)},
    }

    # Wheel: weather
    yield {
        "device_id": "wheel-01", "metric": "weather", "ts": now,
        "payload": {
            "t":  round(random.uniform(22, 32), 1),
            "rh": round(random.uniform(20, 45), 1),
            "p":  round(random.uniform(1005, 1015), 1),
        },
    }

    # Building flows
    for d in _FLOW_DEVICES:
        lpm = max(0.0, random.gauss(3.5, 1.5))
        _running_total[d] += lpm / 6
        yield {
            "device_id": d, "metric": "flow", "ts": now,
            "payload": {
                "lpm": round(lpm, 2),
                "total_l": round(_running_total[d], 1),
            },
        }
