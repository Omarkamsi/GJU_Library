# Node A — Wheel Observatory

Publishes power/level/weather/status to MQTT every 10s (60s for status).

## Build & flash
```bash
pio run -t upload
pio device monitor
```

## Provisioning
Replace `NODE_ID`, `WIFI_*`, `MQTT_*` constants in `src/main.cpp` with values
from `device.env` produced by `infra/scripts/provision-device.sh wheel-01`.

## Wiring
| ESP32 | Sensor      |
|-------|-------------|
| GPIO16/17 | PZEM-004T TX/RX |
| GPIO5/18  | JSN-SR04T TRIG/ECHO |
| GPIO21/22 | BME280 SDA/SCL |
| 5V / GND  | All sensors |
