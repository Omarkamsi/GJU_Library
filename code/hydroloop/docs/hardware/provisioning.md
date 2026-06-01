# Provisioning a Device

1. On the cloud host: `infra/scripts/provision-device.sh <node_id>` →
   produces `device-<node_id>.env` with MQTT_USER/MQTT_PASS.
2. Edit `firmware/<node>/src/main.cpp`, replace the constants block with
   values from `device-<node_id>.env` plus your Wi-Fi creds.
3. `pio run -t upload` to flash.
4. `pio device monitor` to verify Wi-Fi + MQTT connect.
5. From cloud host: `mosquitto_sub -t 'hydroloop/+/<node_id>/#'`
   should show messages within 30s.
