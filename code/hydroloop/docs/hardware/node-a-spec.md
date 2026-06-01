# Node A — Wheel Observatory Spec

## BOM
- 1× ESP32 DevKit-C
- 1× PZEM-004T v3 (clamp CT)
- 1× JSN-SR04T waterproof ultrasonic + IP65 mount
- 1× BME280 (I2C)
- 1× ESP32-CAM (separate node, publishes presence boolean only)
- 1× IP65 ABS enclosure, glands, DIN clips
- 1× 5V/2A weatherproof PSU

## Wiring
| ESP32 pin | Sensor pin |
|-----------|-----------|
| GPIO16    | PZEM TX |
| GPIO17    | PZEM RX |
| GPIO5     | JSN-SR04T TRIG |
| GPIO18    | JSN-SR04T ECHO |
| GPIO21    | BME280 SDA |
| GPIO22    | BME280 SCL |
| 5V        | All sensor VCC |
| GND       | All sensor GND |

## Firmware
`firmware/node_a_wheel/` — replace `NODE_ID`, `WIFI_*`, `MQTT_*` constants
with values from `device-wheel-01.env` produced by `provision-device.sh`.

## Bench-test acceptance
1. Power up with USB.
2. Within 30s, `mosquitto_sub -h <broker> -t 'hydroloop/wheel/wheel-01/#'`
   shows `power`, `level`, `weather` messages every 10s and `status` every 60s.
3. Cover ultrasonic — `level.cm` drops to ~0.
