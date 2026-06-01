# Node A (Wheel Observatory) — Procurement & Bench Guide

**Goal:** Build a single integrated sensor unit that monitors the GJU central water wheel — power, water level, weather, presence — and publishes everything to MQTT.

**Total elapsed time:** 4 weeks from order to bench-proven prototype, plus 1 day of on-site install once the MoU lands.

**Effort:** ~14 hours hands-on (more than Node B because four sensors and weatherproofing).

**Prerequisite:** At least one Node B flow meter has been running in production for a week. The lessons from Node B (Wi-Fi reliability, NTP, enclosure sealing, MQTT flake-recovery) directly inform Node A. Don't skip this — building Node A first inverts the risk.

---

## ⚠️ Safety: This Project Touches Mains AC

The PZEM-004T sensor measures the wheel motor's mains current. The CT (current transformer) clamp itself is non-invasive — it clamps around an existing wire without cutting it — but the sensor also has **voltage-tap leads that must connect to the live phase and neutral**. That's mains AC at 230 V in Jordan. **People die from it.**

**Hard rules:**
1. **For the actual on-site install: hire or borrow a licensed electrician.** GJU facilities has them; ask. The project budget has $200+ contingency that can pay for an hour of their time. This is not optional.
2. For the bench-build phase described in this guide, we use a **bench-top motor or a 12 V hobby motor** — not mains. We never plug the PZEM into a wall socket on the bench. Calibration is done with the manufacturer's rated test points only.
3. Treat the PZEM v3 module as a measurement instrument. Don't open the case, don't modify the CT.
4. If at any point you're unsure: stop and ask. Bad outcomes are not recoverable.

The rest of this guide assumes you're doing the bench build with low-voltage stand-ins.

---

## Phase 0 — Tools you need before anything arrives

In addition to the Node B toolset:

| Tool | Notes |
|---|---|
| Hot-glue gun + glue sticks | Strain relief inside the enclosure |
| Drill + step drill bit (4-32 mm) | For cable gland holes in the enclosure |
| Silicone sealant (clear, neutral cure) | Edges of the enclosure lid; gland threads |
| Cable ties (100 mm, 200 mm) + screw mounts | Mounting cables to lampposts |
| Clamp meter (DC/AC, 0-20 A) | For verifying CT readings independently |
| Bench DC supply (5 V, 2 A min) | Powers the sensor unit during bench testing |
| 12 V DC hobby motor + 12 V supply, **OR** a bench AC source with safety isolation | Stands in for the wheel motor during bench tests of the PZEM |
| 5 L plastic water bucket | Stands in for the wheel reservoir during ultrasonic tests |

**If GJU has an electrical safety lab:** use it. Many universities require it for any project involving 230 V mains, even on a bench.

---

## Phase 1 — Procurement

### Round 1 — Single-unit shopping list (~$155 of parts + $25 mounting)

| # | Part | Spec | Qty | ~Unit $ | Notes |
|---|---|---|---|---|---|
| 1 | ESP32 DevKit-C | Same as Node B | 2 | $6 | Buy 2; one is the spare |
| 2 | ESP32-CAM | OV2640 module + USB programmer board | 1 | $10 | Separate node, posts presence boolean only |
| 3 | PZEM-004T v3 | 100 A clamp CT, with 4-pin TTL UART output | 1 | $20 | Confirm v3 (5V logic compatible). v1 has different wiring. |
| 4 | JSN-SR04T waterproof ultrasonic + transducer | 25 cm to 4.5 m range | 1 | $7 | The transducer is on a 2.5 m cable already |
| 5 | BME280 sensor | I2C, 3.3-5 V tolerant breakout, address 0x76 | 1 | $5 | Adafruit clone is fine |
| 6 | IP65 ABS enclosure, 200×150×80 mm | Hinged lid, gasketed, with mounting flanges | 1 | $12 | Bigger than Node B because four sensor cables enter |
| 7 | Cable glands PG7 + PG9 | 3 × PG7, 1 × PG9 | — | $3 | One per sensor cable + power |
| 8 | DIN rail and clips, 100 mm | For ESP32 + PZEM mounting inside enclosure | 1 | $4 | Optional but tidy |
| 9 | Pole-mount bracket (U-bolt or strap clamp) | Fits 80-120 mm diameter lamppost | 1 | $5 | Match GJU's lamppost diameter — measure first |
| 10 | 5V/2A weatherproof PSU | IP67 outdoor switching supply, mains in / 5V DC out | 1 | $25 | Mean Well RS-15-5 or equivalent |
| 11 | Mains tap with appropriate breaker | 6 A breaker, terminals for the PSU | — | $20 | **Electrician-installed only** at the site |
| 12 | UV-resistant cable, 4-core, 5 m | For the sensor pigtail to the JSN-SR04T | 1 | $8 | Outdoor rated |

### Where to buy

- **PZEM-004T v3, JSN-SR04T, BME280, ESP32-CAM** → **AliExpress** is by far the cheapest. 2-3 weeks shipping. Order Day 1 of the build week.
- **Outdoor enclosure, cable glands, weatherproof PSU** → either AliExpress or **a local electrical supply shop in Amman**. Examples: shops on Wadi Saqra electronics street; for industrial parts try Industrial City zones.
- **U-bolts, drill bits, silicone, hot glue** → any DIY/hardware store; same-day.

### Round 2 — None needed

Node A is one unit, not six. There's no "scale-up order" — just the prototype, then deploy.

---

## Phase 2 — While parts ship (Days 1-21)

### Days 1-7 — Read & extend the firmware

Open `firmware/node_a_wheel/src/main.cpp`. Compared to Node B, this firmware:

- Initializes 4 sensors (PZEM, JSN-SR04T, BME280, optionally ESP32-CAM externally)
- Publishes 4 separate topics every 10 seconds (`power`, `level`, `weather`, status every 60 s)
- Uses `Wire.begin()` for I2C with the BME280
- Uses `Serial2` (UART) for the PZEM
- Uses two GPIOs for ultrasonic (TRIG/ECHO)

Try compiling without hardware:
```bash
cd firmware/node_a_wheel
pio run
```

Expected: `[SUCCESS]`. PlatformIO downloads the PZEM, BME280, and Adafruit Unified Sensor libraries automatically per `platformio.ini`.

### Days 8-14 — Read the PZEM-004T datasheet

This is the only sensor that anyone on the team is unlikely to have used before. Skim the PZEM-004T v3 datasheet (a PDF is on the manufacturer's site; also good third-party explainers on YouTube — search "PZEM-004T v3 ESP32"). Specifically understand:

- Pinout of the 4-pin TTL header: TX, RX, 5V, GND
- Modbus-RTU protocol used by the v3 (the `PZEM004Tv30` Arduino library handles this transparently)
- That the CT clamp must encircle **only one** of the live conductors (a single phase wire, not phase + neutral together — that would cancel and read zero)
- The voltage-tap leads (red/black on the PZEM body) must connect to phase and neutral of the same circuit

### Days 15-21 — Plan the enclosure layout

Sketch on paper how all the components fit inside the IP65 box:

```
┌────────────────────────────────────────┐
│  [PSU 5V/2A]    [PZEM-004T module]    │
│                                        │
│  [ESP32 DevKit on DIN clip]            │
│                                        │
│  [BME280 on a small standoff,          │
│   near a vented gland]                 │
│                                        │
│  Cable entries (left side):            │
│  ◯ PG9 mains in                        │
│  ◯ PG7 ultrasonic cable                │
│  ◯ PG7 CT lead-through                 │
│  ◯ PG7 spare                           │
└────────────────────────────────────────┘
```

The BME280 needs **air contact** to read humidity and pressure correctly. Either drill a small vent hole protected by a mesh filter, OR mount the BME280 outside the enclosure under a Stevenson-screen-style sun shield. The latter is more accurate; the former is fine for a 3-month project.

---

## Phase 3 — Build the bench prototype (Day ~21, when parts arrive)

### Step 3.1 — Wire the four sensors to the ESP32 on a breadboard

Pin assignments (must match the firmware constants in `main.cpp`):

| ESP32 pin | Connects to | Note |
|---|---|---|
| GPIO16 | PZEM TX (→ ESP32 RX) | UART2 RX |
| GPIO17 | PZEM RX (→ ESP32 TX) | UART2 TX |
| GPIO5  | JSN-SR04T TRIG | Output |
| GPIO18 | JSN-SR04T ECHO | Input — keep cable < 3 m for clean pulses |
| GPIO21 | BME280 SDA | I2C; pull-ups already on most BME280 breakouts |
| GPIO22 | BME280 SCL | I2C |
| 5V (VIN) | All sensor VCCs | Use a single 5V rail on the breadboard |
| GND | All sensor GNDs | Common ground |

Triple-check before powering on. PZEM **does not** get its mains-voltage taps wired during bench tests — leave the red/black voltage leads disconnected. The CT clamp by itself can sit on the bench.

### Step 3.2 — Smoke-test each sensor in isolation

Bring sensors up one at a time. For each, write a 10-line throwaway sketch that prints to serial. This isolates "is my wiring right" from "is the integrated firmware right."

**BME280 first:**
```cpp
#include <Wire.h>
#include <Adafruit_BME280.h>
Adafruit_BME280 bme;
void setup() { Serial.begin(115200); Wire.begin(); bme.begin(0x76); }
void loop() {
  Serial.printf("T=%.1f  RH=%.1f  P=%.1f\n",
    bme.readTemperature(), bme.readHumidity(), bme.readPressure()/100.0);
  delay(1000);
}
```
Expected: temperature near room temp, humidity 30-70%, pressure ~1013 mbar. If `bme.begin()` fails, try address 0x77 (some breakouts strap differently); if both fail, check SDA/SCL not swapped, and that you wired 3V3 not 5V (the chip is 3.3V; some breakouts have a regulator that accepts 5V, others don't).

**JSN-SR04T next:** similar to standard HC-SR04 code; the firmware's `readUltraCm()` function already does it. Stand the transducer over a bucket of water at known depth (50 cm). Expect readings within ±2 cm.

**PZEM-004T third (no mains):** wire only TX/RX/5V/GND. The library will throw timeouts if no AC is present (expected). Confirm the ESP32 sees the module's address by calling `pzem.address()` — non-zero means the UART link is alive.

**ESP32-CAM is a separate device** — flash its own firmware on its own ESP32-CAM module (not the DevKit). Its wiring isn't on the breadboard with the others. Defer it; it's the lowest-priority signal in the system.

### Step 3.3 — Bench test PZEM with a 12 V hobby motor (low-voltage proxy for the wheel)

The PZEM is rated for AC, but it will read **DC currents** through the CT clamp at low precision — enough to confirm the ISR and UART work. Set up a 12 V DC supply driving a small DC motor (a hobbyist motor that pulls 0.5-1 A). Clamp the PZEM CT around the **positive** wire (one wire only). The voltage taps stay disconnected.

Run the firmware. The `power` topic should publish messages with non-zero current values when the motor runs and zero when it's off. **Voltage will read 0** because no AC reference — that's expected for the bench test. We're proving the UART and ISR plumbing, not the absolute accuracy.

For final accuracy testing, the PZEM only validates correctly against an AC source. If GJU's lab has an isolation transformer + a known-load test bench, use it. Otherwise, on-site validation against a clamp-meter reading is good enough for the IEEE deliverable.

---

## Phase 4 — Flash the integrated firmware

Same flow as Node B Phase 4:

```bash
infra/scripts/provision-device.sh wheel-01
cat device-wheel-01.env
# replace constants in firmware/node_a_wheel/src/main.cpp
cd firmware/node_a_wheel
pio run -t upload
pio device monitor
```

Expected serial output within ~15 seconds of boot:
```
WiFi connected, IP: 192.168.1.56
NTP synced
PZEM ready
BME280 ready
MQTT connected
[publishing 4 topics every 10s]
```

If only some sensors initialize, the missing ones likely have wiring or I2C-address issues — go back to Phase 3.2 and retest in isolation.

---

## Phase 5 — Verify end-to-end on the dashboard

```bash
docker compose exec mosquitto mosquitto_sub -t 'hydroloop/wheel/wheel-01/#' -v
```

Expected: 4 topic streams, ~every 10 s for `power`/`level`/`weather`, every 60 s for `status`.

```
hydroloop/wheel/wheel-01/power   {"ts":"...","v":0.0,"i":0.5,"p":0.0,"e":0.0,"pf":0.0}
hydroloop/wheel/wheel-01/level   {"ts":"...","cm":48.2}
hydroloop/wheel/wheel-01/weather {"ts":"...","t":24.3,"rh":35.7,"p":1011.5}
hydroloop/wheel/wheel-01/status  {"ts":"...","rssi":-58,"uptime_s":120,"fw":"0.1.0"}
```

(`v=0, p=0` because no AC during bench — current reads through CT but voltage reference is missing. Once on-site with mains taps wired, all five power fields populate.)

Open http://localhost:3001/wheel:
- Four tiles populate (Power, Energy, Water level, Air temp)
- Charts populate within a few minutes
- Status badge shows green

---

## Phase 6 — Calibrate

Each of the four sensors needs its own validation:

| Sensor | Reference | Acceptance |
|---|---|---|
| **BME280 temperature** | Lab-grade thermometer or known-good weather station | ±0.5 °C |
| **BME280 humidity** | Lab hygrometer | ±5% RH |
| **BME280 pressure** | Local meteorological pressure (Amman airport METAR) corrected to Madaba elevation | ±2 mbar |
| **JSN-SR04T water level** | Steel ruler in the bucket | ±1 cm at 30-100 cm range |
| **PZEM voltage** | Wall outlet measured with a separate multimeter (electrician supervised) | ±2% at 230 V |
| **PZEM current** | Calibrated clamp meter on the same conductor | ±5% at expected load |

Document each calibration in a per-device JSON file:
```bash
echo '{"device":"wheel-01","calibrated_at":"2026-...","temp_offset":0.0,"rh_offset":0.0,...}' > calibrations/wheel-01.json
```

Commit this. The dashboard doesn't apply offsets yet (M0 doesn't need them), but recording is enough for now and the M1 backend will read it.

---

## Phase 7 — Weatherproof for outdoor

Now you're moving from breadboard to permanent enclosure.

### Step 7.1 — Final enclosure assembly

1. **Drill cable gland holes** with the step drill, sized per gland (PG7 = 12 mm, PG9 = 16 mm). All on the enclosure's bottom or side, never the top.
2. **Mount the DIN rail** on the bottom face. Clip on the ESP32 (with its own DIN-clip adapter, or hot-glued to a small DIN segment) and the PZEM module (some PZEM enclosures have built-in DIN tabs).
3. **Mount the PSU** with screws to the bottom face.
4. **Run sensor cables** through their respective glands, leaving 5-10 cm slack inside the box for strain relief. Pull each cable so the gland gasket compresses; tighten the gland nut.
5. **Mount the BME280 outside** under a small printed sun-shield, or accept the indoor reading. If outside, drill one extra PG7 gland for the I2C cable (4 wires: 3V3, GND, SDA, SCL).
6. **Hot-glue the inside of each gland** for a second layer of moisture protection. Don't seal them entirely — you may need to re-pull a cable later.
7. **Apply silicone sealant** to the lid gasket. Close the lid finger-tight first, let it cure 24 h before final tightening.
8. **Pole-mount bracket** screws onto the back face. U-bolt size depends on lamppost diameter (you measured this in Phase 1 — measure again to be sure).

### Step 7.2 — Indoor pre-deployment soak test

Leave the assembled, sealed enclosure powered up indoors for **48 hours straight**. Watch the dashboard. The acceptance criteria:

- Status is green continuously (no >2-min gaps in `last_seen`)
- Wi-Fi RSSI stays above -75 dBm
- Temperature/humidity values look stable (don't jump randomly — that indicates poor sensor mounting or EMI)
- No reboots in serial output (`uptime_s` always increases, never resets)

If any of those fail, fix at the bench before sending it outdoors. Once sealed and screwed to a lamppost, every fix becomes 10× more painful.

---

## Phase 8 — Site deployment (post-MoU)

This phase happens **only after** GJU facilities/admin gives written authorization to mount the unit near the wheel. Until then, the unit lives indoors as part of the public dashboard demo.

### What facilities needs to approve

1. Mounting one IP65 enclosure to a public lamppost within 5 m of the wheel motor.
2. An electrician (theirs or one we pay) tapping a dedicated 6 A breaker off the lamppost circuit for the PSU.
3. Routing one 5 m cable from the lamppost to the wheel motor housing for the PZEM CT clamp.
4. Routing the JSN-SR04T transducer cable (already 2.5 m) into the wheel reservoir housing — the transducer hangs ~10 cm above the maximum water surface, pointing down.

Hand them this guide + the architecture doc (`docs/architecture.md`) + the BOM. Most resistance disappears once they see we're not modifying the wheel itself, only observing it.

### Install day checklist

| Step | Owner | Notes |
|---|---|---|
| Mount enclosure on lamppost (U-bolt) | Hardware team | 30 min |
| Run mains feed from breaker to PSU | Licensed electrician | 1-2 h, photographs everything |
| Clamp PZEM CT around motor's live wire | Electrician | 15 min |
| Wire PZEM voltage taps to phase + neutral | Electrician | 30 min |
| Position JSN-SR04T transducer above water | Hardware team | 30 min |
| Power up; verify dashboard goes live | Software team (you) | 15 min |
| Take "before" photos for IEEE submission | Whoever has the best phone | — |

### Day-after sanity check

Open http://localhost:3001/wheel from a desk:
- All four tiles should now show real values (power non-zero when wheel is running, level matching the reservoir depth, temp/humidity matching outside conditions).
- The 24-hour chart should reveal the wheel's daily duty cycle (off most of the night, running 9-2 weekdays per the original observation).
- Within a week, you'll have enough data for the IEEE final report's "measured energy consumption" graph.

---

## Troubleshooting cheat sheet

| Symptom | Likely cause | Fix |
|---|---|---|
| BME280 not detected | Wrong I2C address, swapped SDA/SCL | Try 0x77; verify with `i2cdetect` sketch |
| PZEM reads 0.0 for everything | Voltage taps not wired (bench), CT not clamped, or clamped around both wires | Confirm CT around one conductor; on bench, current-only is normal |
| JSN-SR04T returns -1 | Cable too long (>5 m), surface too rough, sensor inverted | Shorten cable; mount perpendicular to flat water |
| ESP32 reboots randomly | Brown-out from undersized PSU | Verify PSU is 5V/2A min; 5V/1A is not enough for 4 sensors + Wi-Fi |
| Dashboard "wheel" tile never updates | All four metrics fail to publish | Check serial monitor for which sensor is hanging `setup()` |
| Tiles update but values are obviously wrong | Sensor reads junk, firmware not parsing correctly | Compare raw serial output to MQTT payload — gap is in firmware |
| WiFi RSSI < -85 dBm at the lamppost | Distance from AP, building between | Add a dedicated outdoor AP, or fall back to LoRa gateway (in BOM) |

---

## Summary timeline

| Week | Activity |
|---|---|
| 1 | Order parts; read PZEM datasheet; sketch enclosure |
| 2 | Toolchain + firmware compile; smoke-test sensors as parts arrive piecemeal |
| 3 | Bench-prototype all four sensors integrated; flash; verify dashboard |
| 4 | Calibrate each sensor; assemble final enclosure; 48 h soak test |
| 5 | (gated on MoU) Site install with electrician; first real wheel data |
| 6+ | Collect 1+ week of data for IEEE submission graphs |

---

## When this guide ends

After Phase 8 succeeds:
- `wheel-01` is publishing real measurements every 10 seconds, 24/7.
- The `/wheel` page is the centrepiece of the IEEE demo.
- You have hard data to back the cost-savings claims in the institutional proposal that's part of the grant deliverable.

Then: archive this guide as the "build record" for the IEEE submission, and start the M1 milestone (anomaly detection, evaporation modelling, retrofit-proposal report generation).
