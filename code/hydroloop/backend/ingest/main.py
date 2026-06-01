import asyncio
import os
from typing import Optional
import structlog
from .db import make_pool, insert_reading
from .pubsub import Hub
from .schemas import parse_payload
from .mock import generate_tick

log = structlog.get_logger()
HUB = Hub()

def _parse_topic(topic: str) -> Optional[tuple[str, str, str]]:
    parts = topic.split("/")
    if len(parts) != 4 or parts[0] != "hydroloop":
        return None
    _, node_type, node_id, metric = parts
    return node_type, node_id, metric

async def handle_message(pool, hub: Hub, *, topic: str, raw: bytes) -> None:
    parsed = _parse_topic(topic)
    if parsed is None:
        log.warning("bad_topic", topic=topic)
        return
    _, device_id, metric = parsed
    try:
        reading = parse_payload(metric, raw)
    except Exception as e:
        log.warning("bad_payload", topic=topic, err=str(e))
        return
    payload = reading.model_dump(mode="json", exclude={"ts"})
    await insert_reading(pool, device_id, metric, reading.ts, payload)
    await hub.publish({
        "device_id": device_id, "metric": metric,
        "ts": reading.ts.isoformat(), "payload": payload,
    })

async def _run_mqtt(pool) -> None:
    import aiomqtt
    host = os.environ["MQTT_HOST"]
    port = int(os.environ.get("MQTT_PORT", "1883"))
    async with aiomqtt.Client(host, port=port) as client:
        await client.subscribe("hydroloop/+/+/+", qos=1)
        log.info("mqtt_subscribed", host=host, port=port)
        async for msg in client.messages:
            await handle_message(pool, HUB, topic=str(msg.topic), raw=msg.payload)

async def _run_mock(pool) -> None:
    while True:
        for r in generate_tick():
            await insert_reading(pool, r["device_id"], r["metric"], r["ts"], r["payload"])
            await HUB.publish({
                "device_id": r["device_id"], "metric": r["metric"],
                "ts": r["ts"].isoformat(), "payload": r["payload"],
            })
        await asyncio.sleep(10)

async def main() -> None:
    dsn = (
        f"postgresql://{os.environ['POSTGRES_USER']}:{os.environ['POSTGRES_PASSWORD']}"
        f"@{os.environ['POSTGRES_HOST']}:{os.environ['POSTGRES_PORT']}/{os.environ['POSTGRES_DB']}"
    )
    pool = await make_pool(dsn)
    if os.environ.get("MOCK") == "1":
        log.info("ingest_mode", mode="mock")
        await _run_mock(pool)
    else:
        log.info("ingest_mode", mode="mqtt")
        await _run_mqtt(pool)

if __name__ == "__main__":
    asyncio.run(main())
