// HydroLoop Node A — Wheel Observatory
// Publishes:
//   hydroloop/wheel/{NODE_ID}/power      every 10s
//   hydroloop/wheel/{NODE_ID}/level      every 10s
//   hydroloop/wheel/{NODE_ID}/weather    every 10s
//   hydroloop/wheel/{NODE_ID}/status     every 60s

#include <WiFi.h>
#include <PubSubClient.h>
#include <Wire.h>
#include <Adafruit_BME280.h>
#include <PZEM004Tv30.h>

// Provisioned at flash time — replace with values from device.env
#define NODE_ID            "wheel-01"
#define WIFI_SSID          "GJU-IoT"
#define WIFI_PASS          "changeme"
#define MQTT_HOST          "10.0.0.10"
#define MQTT_PORT          1883
#define MQTT_USER          "wheel-01"
#define MQTT_PASS          "changeme"

#define PIN_PZEM_RX 16
#define PIN_PZEM_TX 17
#define PIN_ULTRA_TRIG 5
#define PIN_ULTRA_ECHO 18

WiFiClient wifi;
PubSubClient mqtt(wifi);
Adafruit_BME280 bme;
PZEM004Tv30 pzem(Serial2, PIN_PZEM_RX, PIN_PZEM_TX);

unsigned long lastTick = 0, lastStatus = 0;

static void connectWifi() {
  WiFi.begin(WIFI_SSID, WIFI_PASS);
  while (WiFi.status() != WL_CONNECTED) { delay(250); }
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

static void publishJson(const char* metric, const String& payload) {
  String topic = String("hydroloop/wheel/") + NODE_ID + "/" + metric;
  mqtt.publish(topic.c_str(), payload.c_str(), false);
}

static float readUltraCm() {
  digitalWrite(PIN_ULTRA_TRIG, LOW); delayMicroseconds(2);
  digitalWrite(PIN_ULTRA_TRIG, HIGH); delayMicroseconds(10);
  digitalWrite(PIN_ULTRA_TRIG, LOW);
  long us = pulseIn(PIN_ULTRA_ECHO, HIGH, 30000);
  if (us == 0) return -1.0;
  return us / 58.0;
}

void setup() {
  Serial.begin(115200);
  Wire.begin();
  bme.begin(0x76);
  pinMode(PIN_ULTRA_TRIG, OUTPUT);
  pinMode(PIN_ULTRA_ECHO, INPUT);
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
    String ts = isoNow();

    float v = pzem.voltage(), i = pzem.current(), p = pzem.power();
    float e = pzem.energy(), pf = pzem.pf();
    String pwr = String("{\"ts\":\"") + ts + "\",\"v\":" + v + ",\"i\":" + i +
                 ",\"p\":" + p + ",\"e\":" + e + ",\"pf\":" + pf + "}";
    publishJson("power", pwr);

    float cm = readUltraCm();
    if (cm > 0)
      publishJson("level", String("{\"ts\":\"") + ts + "\",\"cm\":" + cm + "}");

    float t = bme.readTemperature();
    float rh = bme.readHumidity();
    float pr = bme.readPressure() / 100.0;
    String w = String("{\"ts\":\"") + ts + "\",\"t\":" + t + ",\"rh\":" + rh +
               ",\"p\":" + pr + "}";
    publishJson("weather", w);
  }

  if (now - lastStatus >= 60000) {
    lastStatus = now;
    String st = String("{\"ts\":\"") + isoNow() + "\",\"rssi\":" + WiFi.RSSI() +
                ",\"uptime_s\":" + (now/1000) + ",\"fw\":\"0.1.0\"}";
    publishJson("status", st);
  }
}
