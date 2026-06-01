#!/usr/bin/env bash
# infra/scripts/provision-device.sh <node_id>
# Generates a per-device MQTT password and writes a device.env
# the hardware team can pour into the firmware build.

set -euo pipefail
NODE_ID="${1:?usage: provision-device.sh <node_id>}"
PASS="$(openssl rand -base64 18 | tr -d '=+/' | cut -c1-22)"

OUT="device-${NODE_ID}.env"
cat > "$OUT" <<EOF
# Generated $(date -Iseconds)
NODE_ID=${NODE_ID}
MQTT_USER=${NODE_ID}
MQTT_PASS=${PASS}
EOF
chmod 600 "$OUT"

# Add user to mosquitto password file (run inside the container)
docker compose exec mosquitto mosquitto_passwd -b /mosquitto/data/passwd "${NODE_ID}" "${PASS}"

# Append ACL line
ACL=/mosquitto/data/acl
docker compose exec mosquitto sh -c "
  grep -q '^user ${NODE_ID}\$' ${ACL} 2>/dev/null || cat >> ${ACL} <<EOT
user ${NODE_ID}
topic readwrite hydroloop/${NODE_ID%%-*}/${NODE_ID}/#
EOT
  kill -HUP 1
"

echo "Wrote $OUT — give to hardware team. ACL + passwd updated, broker reloaded."
