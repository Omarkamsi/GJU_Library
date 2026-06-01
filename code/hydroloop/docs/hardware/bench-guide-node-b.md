# Node B (Building Flow Meter) — Procurement & Bench Guide

**Goal:** Build one working flow meter prototype that publishes real readings to the HydroLoop dashboard. Then replicate it five more times for the six campus buildings.

**Total elapsed time:** 2-3 weeks from order placement to first working prototype, depending on customs. Calendar-driven, not effort-driven — most of the time is shipping wait.

**Effort:** ~6 hours hands-on once parts arrive.

---

## Phase 0 — Tools you need before anything arrives

These should already be in any hardware lab. If GJU's electronics lab has them, we don't buy any of these. Otherwise budget ~$60 of spend (one-time, not in the $1,400 BOM).

| Tool | Notes |
|---|---|
| Soldering iron (25-40 W) + solder (0.6-0.8 mm rosin core) | For sensor leads and headers |
| Wire strippers | 22-26 AWG range |
| Digital multimeter | Continuity + voltage check |
| Breadboard (full size, 830 tie points) | First prototype lives here before soldering |
| Jumper wires (M-M, M-F, F-F) | At least 30 of each |
| USB-A → Micro-USB cable, **data-capable** (not charge-only) | For flashing ESP32 DevKit-C; pure-charge cables silently fail |
| 5L bucket or 2L water bottle, kitchen scale | For flow-rate calibration |
| Laptop with USB port | For PlatformIO; Linux/macOS/Windows all OK |

**Watch out for:** "data-capable" Micro-USB cables. Most cheap cables shipped with phones/chargers are charge-only. If `pio device list` shows no serial port when the ESP32 is plugged in, swap the cable before swapping the ESP32.

---

## Phase 1 — Procurement (Week 1, Day 1)

### Round 1 — Single-prototype shopping list (~$25)

Buy *one* of each first. Don't bulk-order until the prototype works.

| # | Part | Spec | Qty | ~Unit $ | Notes |
|---|---|---|---|---|---|
| 1 | ESP32 DevKit-C | ESP-WROOM-32 module, 30-pin or 38-pin | 2 | $6 | Order **2** — kill ratio is real; you will brick one |
| 2 | YF-S201 flow sensor | ½″ G-thread Hall-effect, 1-30 L/min range | 1 | $7 | Confirm thread matches the building's water inlet |
| 3 | 5V/1A USB power supply | Micro-USB output, mains plug | 1 | $5 | Any phone charger works; CE-marked preferred for permanent install |
| 4 | IP54 plastic project box, ~120×80×50 mm | Translucent or grey, with mounting flanges | 1 | $4 | Roomy enough for ESP32 + cabling |
| 5 | Cable glands PG7 (3.5-6 mm) | Plastic, pre-tapped | 2 | $0.50 | One for power in, one for sensor out |
| 6 | 22 AWG silicone hookup wire, red/black/yellow | 1 m each colour | — | $3 | For sensor pigtail extension if needed |
| 7 | Heat-shrink tubing assortment | 2-6 mm | — | $2 | Strain relief at sensor leads |

**Budget impact:** ~$25 of the $480 you've earmarked for "Flow sensor + ESP32 + enclosure ×6". You'll come in well under because most components are < $10 each at AliExpress prices.

### Where to buy in Jordan

1. **First, ask GJU's Electrical/Mechatronics Engineering department** if they have ESP32s, breadboards, and basic electronics in stock. Many do — borrow what you can.

2. **Local Amman electronics shops** (verify these still operate before driving across town — store status changes):
   - **Wadi Saqra** electronics street (downtown Amman) — many small shops, ESP32 boards available, prices ~2× AliExpress but no shipping wait. Best for filler items: cables, headers, breadboards.
   - **TIDB / Robotech / Maker Hub Jordan** (search current addresses on Google Maps) — better for sensor modules.
   - Ask in the **GJU Mechatronics WhatsApp group** or **Robotics Club** if any team members already buy from a trusted local shop.

3. **AliExpress** — cheapest by 50-70%. 2-3 weeks shipping to Amman, customs fees ~10-15% over $75 declared value. Use **AliExpress Standard Shipping** (tracked); avoid the unbranded "free shipping" tier (untrackable, 4-6 weeks).

4. **Amazon.ae (UAE) → Aramex** — middle ground. ~7-10 days, slightly more expensive than AliExpress but faster and more reliable.

**Pragmatic plan:**
- Buy ESP32 + breadboard + jumper wires **locally** (today, while you wait)
- Buy YF-S201 + cable glands + enclosure on **AliExpress** Day 1 of Week 1
- This way bench coding starts in 2 days, not 3 weeks.

### Round 2 — Replicating to 6 buildings (Week 4-5)

Only place this order **after** the prototype works end-to-end. Items 1-7 from Round 1, ×5 quantities. Spend ~$120-180.

---

## Phase 2 — While parts ship (Days 1-7)

Use the wait productively. By the time parts arrive, the dev environment is ready and the firmware builds.

### Day 1 — Install toolchain

On the build laptop:

```bash
# Install PlatformIO
python3 -m pip install platformio --break-system-packages
# or follow https://platformio.org/install/cli

pio --version    # should print v6.x or later
```

### Day 2 — Clone the repo

```bash
git clone https://github.com/Omarkamsi/GJU-Hydroloop.git
cd GJU-Hydroloop
```

### Day 3 — Run the local stack with mock data

```bash
docker compose up -d timescaledb mosquitto
cd backend
python3 -m pip install -e ".[dev]" --break-system-packages
export POSTGRES_USER=hydroloop POSTGRES_PASSWORD=changeme POSTGRES_DB=hydroloop
export POSTGRES_HOST=localhost POSTGRES_PORT=5432
export MQTT_HOST=localhost MQTT_PORT=1883 MOCK=0
uvicorn api.main:app --port 8000 &      # API
python -m ingest.main &                  # ingest subscribed to MQTT (not mock)

cd ../frontend
npm install
npm run build
NEXT_PUBLIC_API_BASE=http://localhost:8000 npm run start -- -p 3001 &
```

Open http://localhost:3001. Tiles will read 0 because no device is publishing yet — that's the point. We'll fix it when the ESP32 arrives.

### Day 4-7 — Read the firmware code

Open `firmware/node_b_flow/src/main.cpp` in your editor of choice. Read end-to-end. Make sure each team member understands:

- The `onPulse()` ISR that increments `pulses` on every rising edge of GPIO4
- The 10-second tick that converts pulses → liters → L/min
- The ISO-8601 timestamp logic (relies on NTP; falls back to epoch-zero before sync)
- The MQTT topic shape: `hydroloop/flow/<NODE_ID>/flow`

Try compiling without an ESP32 attached:

```bash
cd firmware/node_b_flow
pio run         # downloads ESP32 toolchain on first run, ~5 min
```

Expected: `[SUCCESS]`. The `.pio/build/esp32dev/firmware.bin` is what we'll flash in Phase 4.

---

## Phase 3 — Build the first prototype (Day ~14, when parts arrive)

### Step 3.1 — Verify ESP32 boots

1. Plug ESP32 into laptop with the data-capable Micro-USB cable.
2. `pio device list` — should show a serial port like `/dev/ttyUSB0` (Linux), `/dev/cu.usbserial-…` (macOS), or `COM3` (Windows).
3. If nothing appears, install the **CP210x** or **CH340** USB-serial driver (most ESP32 DevKit-C boards use one of those chips — check the silkscreen near the USB connector).

```bash
pio device monitor    # baud auto-detected; usually 115200
```

Press the EN/RST button on the ESP32. You should see boot output. Disconnect (Ctrl-C, then Ctrl-]).

### Step 3.2 — Wire on a breadboard

YF-S201 sensor has three wires:
- **Red** → 5V on ESP32 (the `5V`/`VIN` pin, NOT 3.3V)
- **Black** → GND on ESP32
- **Yellow** → GPIO4 on ESP32, with a 10 kΩ pull-up resistor to 3.3V (the firmware uses internal pull-up, so the resistor is optional but a nice belt-and-braces)

Layout on the breadboard:
```
  ESP32 DevKit-C
  ┌────────────┐
  │ EN     GND │── BLACK ─── YF-S201 black
  │ 3V3        │── (10kΩ to yellow if external pull-up)
  │ GPIO4      │── YELLOW ── YF-S201 yellow
  │            │
  │ VIN (5V)   │── RED ───── YF-S201 red
  └────────────┘
```

Double-check polarity with the multimeter before powering on. The YF-S201 will physically spin its rotor when water flows; without water it does nothing — that's normal.

### Step 3.3 — Smoke test before flashing real firmware

Flash a simple "blink + serial print every pulse" sketch first to confirm the sensor is alive:

```cpp
// quick-test.cpp — TEMPORARY, do not commit
volatile uint32_t pulses = 0;
void IRAM_ATTR isr() { pulses++; }
void setup() {
  Serial.begin(115200);
  pinMode(4, INPUT_PULLUP);
  attachInterrupt(digitalPinToInterrupt(4), isr, RISING);
}
void loop() {
  Serial.printf("pulses: %u\n", pulses);
  delay(1000);
}
```

Pour water through the sensor (or blow into it gently — the rotor spins from air too). The pulse count should climb. If it doesn't:
- Verify VCC is 5V, not 3.3V
- Confirm GPIO4 is the right pin (the silkscreen on cheap clones is sometimes wrong)
- Try a different ESP32 — sensors are usually fine, ESP32s are sometimes DOA

When pulses count reliably, you're ready for the real firmware.

---

## Phase 4 — Flash the real HydroLoop firmware

### Step 4.1 — Provision MQTT credentials for this node

On the laptop running the local stack (which has the Mosquitto broker):

```bash
cd /path/to/GJU-Hydroloop
infra/scripts/provision-device.sh flow-lib       # or another flow-XXX from infra/timescaledb/init.sql
cat device-flow-lib.env                          # copy NODE_ID, MQTT_USER, MQTT_PASS
```

### Step 4.2 — Replace constants in firmware

Open `firmware/node_b_flow/src/main.cpp`. Replace the constants block at top:

```cpp
#define NODE_ID    "flow-lib"
#define WIFI_SSID  "<your local Wi-Fi SSID>"
#define WIFI_PASS  "<your local Wi-Fi password>"
#define MQTT_HOST  "<your laptop's LAN IP, e.g. 192.168.1.42>"
#define MQTT_PORT  1883
#define MQTT_USER  "flow-lib"
#define MQTT_PASS  "<paste from device-flow-lib.env>"
```

Find your laptop's LAN IP with `ip a` (Linux/macOS) or `ipconfig` (Windows) — look for the wireless adapter, e.g. `192.168.1.42`. Both ESP32 and laptop must be on the same Wi-Fi network for bench testing.

### Step 4.3 — Flash

```bash
cd firmware/node_b_flow
pio run -t upload     # builds and flashes
pio device monitor    # tail serial output
```

Within ~10 seconds you should see:
```
WiFi connected, IP: 192.168.1.55
MQTT connected
[publishing every 10s]
```

If WiFi fails: check SSID/password (no surprises — case-sensitive, no quotes in the source).
If MQTT fails: check the broker is running (`docker compose ps mosquitto`), and that no firewall on the laptop blocks port 1883 from the local subnet.

---

## Phase 5 — Verify end-to-end on the dashboard

### Step 5.1 — Subscribe to the topic from the laptop

```bash
docker compose exec mosquitto mosquitto_sub -t 'hydroloop/flow/flow-lib/#' -v
```

Expected: a message every 10 seconds:
```
hydroloop/flow/flow-lib/flow {"ts":"2026-05-09T12:00:00Z","lpm":0.00,"total_l":0.00}
```

(`lpm` is 0 unless you're actively pouring water through the sensor.)

### Step 5.2 — Check the database

```bash
docker compose exec timescaledb psql -U hydroloop -d hydroloop \
  -c "SELECT ts, payload FROM readings WHERE device_id='flow-lib' ORDER BY ts DESC LIMIT 5;"
```

Expected: 5 most recent readings, with non-null payloads.

### Step 5.3 — Open the dashboard

Browse to http://localhost:3001/buildings/flow-lib.

You should see:
- "Library" as the building name
- A green status badge with "Xs ago"
- The "Now" tile reading 0 L/min (until you pour water)
- The 24-hour chart populating after a few minutes

**Pour water through the sensor** (over a sink — connect a hose if you have one). The "Now" tile should jump within ~10 seconds and stay non-zero while water flows.

---

## Phase 6 — Calibrate

The `PULSES_PER_LITER = 450.0` constant in firmware is a YF-S201 datasheet typical. Real sensors vary by ±10%.

1. Tare a kitchen scale or use a 2 L bottle filled to a known mark.
2. Reset the sensor's running total: power-cycle the ESP32 (the firmware doesn't persist `total_l` across reboots — by design).
3. Pour exactly **1.000 L** through the sensor at a steady rate.
4. Read `total_l` from the dashboard or MQTT.

If `total_l` reports `1.05` after pouring 1 L, then the real sensor pulses-per-liter is `450 × 1.05 = 472.5`. Update the constant:

```cpp
#define PULSES_PER_LITER 472.5
```

Re-flash. Re-test with a second known volume (2 L). Done when the reading is within ±2% of poured volume.

Save calibration values per-sensor in a spreadsheet — each YF-S201 will be slightly different.

---

## Phase 7 — Replicate ×5 (Week 4)

Once one prototype works end-to-end:

1. Order parts for the remaining 5 buildings (Round 2 procurement above).
2. For each building, run `provision-device.sh flow-XXX` to get fresh credentials. The seeded device IDs are:
   - `flow-eng-bldg`
   - `flow-cs`
   - `flow-arch`
   - `flow-business`
   - `flow-medical`
   - (`flow-lib` is the prototype, already provisioned)
3. Edit `main.cpp` constants for each, flash, calibrate, drop into IP54 enclosure, label.
4. Each building install needs:
   - Coordination with GJU facilities (it's a permission ask for the water entry point — easier than the wheel because no admin/MoU drama, just talk to whoever runs the building)
   - A 5V USB outlet within ~3 m of the inlet pipe
   - A spot to mount the enclosure (zip ties on a pipe support, or screws into the wall — facilities may have opinions)

**Don't try to install all six on the same day.** Plan one per day; expect each to take 1-2 hours of on-site work plus 30 min on the laptop verifying the readings show up.

---

## Phase 8 — Looking ahead to Node A (the wheel)

This is the harder build, deferred until the campus flow network is online and proven. When you're ready, the second bench guide will cover:

- Splicing the PZEM-004T's CT clamp around the wheel motor's live wire (mains voltage — needs a qualified person)
- Mounting the JSN-SR04T waterproof ultrasonic above the water surface
- Pole-mounting the BME280 weather sensor
- All inside a single IP65 enclosure on a nearby lamppost (post-MoU)

Don't start Node A procurement until at least 2 buildings of Node B are running in production. The lessons learned from Node B (cable strain relief, enclosure sealing, NTP reliability) will apply directly.

---

## Troubleshooting cheat sheet

| Symptom | Likely cause | Fix |
|---|---|---|
| `pio device list` shows nothing | Charge-only USB cable | Use a known-data cable |
| ESP32 boots but `WiFi.begin()` hangs | Wrong SSID/password, 5GHz network | ESP32 only does 2.4 GHz; check |
| MQTT connect fails with -2 | Broker unreachable | Verify laptop IP, port 1883 open, broker running |
| MQTT connect fails with 4 (bad creds) | Username/password mismatch | Re-run provision-device.sh, copy carefully |
| `pulses` never increments | Wrong GPIO, no pull-up, dead sensor | Smoke-test sketch from Phase 3.3 |
| `total_l` drifts over time without water | EMI on the ISR pin | Add a 10kΩ pull-up resistor + 0.1 µF cap to GND |
| Dashboard "last_seen" stays in the past | NTP not synced; ts is 1970 | Wait 30s after boot for NTP, or hardcode `configTime` to a Jordanian NTP server like `0.jordan.pool.ntp.org` |
| Readings spike to absurd values | ISR firing on noise, or poor sensor mounting | Mount with vertical flow direction; debounce in firmware |

---

## Summary timeline

| Week | Activity | Spend |
|---|---|---|
| 1 | Tools check, place AliExpress order, buy local ESP32 + breadboard | ~$30 |
| 2 | Toolchain install, code reading, mock-mode dashboard | $0 |
| 3 | Parts arrive, build prototype, flash, calibrate `flow-lib` | already spent |
| 4 | Order ×5 more units after prototype proven | ~$120 |
| 5 | Build & deploy ×5 buildings | $0 |
| 6 | All 6 buildings live; start Node A planning | — |

By end of week 6, the dashboard at http://localhost:3001 (and eventually a public URL) shows real water flow from six GJU buildings.
