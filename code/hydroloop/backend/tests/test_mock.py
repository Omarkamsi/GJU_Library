from ingest.mock import generate_tick

def test_tick_yields_one_reading_per_seeded_device():
    tick = list(generate_tick())
    device_ids = {r["device_id"] for r in tick}
    assert "wheel-01" in device_ids
    assert "flow-lib" in device_ids
    assert all("metric" in r and "payload" in r for r in tick)

def test_flow_payload_shape():
    tick = list(generate_tick())
    flow = next(r for r in tick if r["device_id"] == "flow-lib" and r["metric"] == "flow")
    assert "lpm" in flow["payload"]
    assert "total_l" in flow["payload"]
    assert flow["payload"]["lpm"] >= 0

def test_power_payload_shape():
    tick = list(generate_tick())
    power = next(r for r in tick if r["device_id"] == "wheel-01" and r["metric"] == "power")
    assert {"v","i","p","e","pf"} <= power["payload"].keys()
