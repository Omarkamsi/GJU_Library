// HydroLoop Node B — Building Flow Meter
// YF-S201: ~7.5 pulses per L/min. Counts pulses on interrupt.

#include <WiFi.h>
#include <PubSubClient.h>

#define NODE_ID    "flow-lib"
#define WIFI_SSID  "GJU-IoT"
#define WIFI_PASS  "changeme"
#define MQTT_HOST  "10.0.0.10"
#define MQTT_PORT  1883
#define MQTT_USER  "flow-lib"
#define MQTT_PASS  "changeme"

#define PIN_FLOW   4
#define PULSES_PER_LITER 450.0   // YF-S201 ~7.5 Hz at 1 L/min → 450 pulses/L

WiFiClient wifi;
PubSubClient mqtt(wifi);

volatile uint32_t pulses = 0;
double total_liters = 0;
unsigned long lastTick = 0, lastStatus = 0;

void IRAM_ATTR onPulse() { pulses++; }

static void connectWifi() {
  WiFi.begin(WIFI_SSID, WIFI_PASS);
  while (WiFi.status() != WL_CONNECTED) delay(250);
}

static void connectMqtt() {
  mqtt.setServer(MQTT_HOST, MQTT_PORT);
  while (!mqtt.connected()) {
    if (mqtt.connect(NODE_ID, MQTT_USER, MQTT_PASS)) break;
    delay(1000);
  }
}

static String isoNow() {
  time_t t = time(nullptr);
  if (t < 1704067200) return String("1970-01-01T00:00:00Z");
  char buf[32]; strftime(buf, sizeof(buf), "%FT%TZ", gmtime(&t));
  return String(buf);
}

void setup() {
  Serial.begin(115200);
  pinMode(PIN_FLOW, INPUT_PULLUP);
  attachInterrupt(digitalPinToInterrupt(PIN_FLOW), onPulse, RISING);
  connectWifi();
  configTime(0, 0, "pool.ntp.org");
  connectMqtt();
}

void loop() {
  if (!mqtt.connected()) connectMqtt();
  mqtt.loop();
  unsigned long now = millis();

  if (now - lastTick >= 10000) {
    lastTick = now;
    noInterrupts();
    uint32_t p = pulses; pulses = 0;
    interrupts();
    double liters = p / PULSES_PER_LITER;
    total_liters += liters;
    double lpm = liters * 6.0;       // 10s window → liters/min
    String ts = isoNow();
    String topic = String("hydroloop/flow/") + NODE_ID + "/flow";
    String payload = String("{\"ts\":\"") + ts + "\",\"lpm\":" + lpm +
                     ",\"total_l\":" + total_liters + "}";
    mqtt.publish(topic.c_str(), payload.c_str(), false);
  }
  if (now - lastStatus >= 60000) {
    lastStatus = now;
    String topic = String("hydroloop/flow/") + NODE_ID + "/status";
    String payload = String("{\"ts\":\"") + isoNow() + "\",\"rssi\":" + WiFi.RSSI() +
                     ",\"uptime_s\":" + (now/1000) + ",\"fw\":\"0.1.0\"}";
    mqtt.publish(topic.c_str(), payload.c_str(), false);
  }
}
