---
title: "HydroLoop — GJU Water & Energy Intelligence Program"
program: "IEEE Region 8 Sustainable Universities Program (2026)"
institution: "German Jordanian University (GJU), Madaba, Jordan"
date: "2026-04-20"
funding_requested_usd: 1400
funding_cap_usd: 2000
duration_months: 3
status: "Initial proposal — pre-submission draft"
---

# HydroLoop
## GJU Water & Energy Intelligence Program

**Tagline:** *Closing the loop on campus water — an AI + IoT platform that transforms GJU's iconic central water wheel into Jordan's first data-driven campus sustainability showcase, and scales the same intelligence across the university.*

---

## 1. Executive Summary

In the exact geographic center of the German Jordanian University campus sits a decorative rotating water wheel. A large industrial motor drives it during campus hours, five hours per day. The wheel loses water to evaporation in the hot Jordanian climate, and the system is periodically drained and refilled with fresh, potable water. No one currently measures how much electricity the motor consumes. No one measures how many liters of water the wheel loses. Every student at Jordan's only German-model engineering university passes it every day — in the country ranked second-most water-stressed on Earth.

**HydroLoop** is a two-layer platform that answers the question *"how much is this actually costing us?"* and turns the answer into action. A non-invasive sensor package around the wheel (clamp-on current sensor, ultrasonic water-level sensor, weather station, and occupancy camera) quantifies the previously invisible waste and feeds an AI model that correlates energy and water loss with weather and human presence. The same IoT + ML platform is then scaled to monitor water consumption across five to seven key campus buildings, producing a unified **GJU Water Intelligence Dashboard** with anomaly detection.

At the end of three months, HydroLoop delivers: (1) the first quantified record of the wheel's true resource cost, (2) an evidence-based retrofit proposal for the campus administration, (3) a campus-wide water-intelligence network actively flagging leaks and misuse, and (4) an open, replicable hardware/software platform other universities across IEEE R8 can fork and deploy.

---

## 2. Problem Statement

### 2.1 The National Context

- **Jordan is the world's second most water-stressed country** (UN Water / World Resources Institute). Per-capita water availability sits near the absolute-scarcity threshold and is declining.
- Jordan imports a significant share of its electricity, with one of the highest energy-import dependencies in the region. Campus electricity consumption translates directly into national resource strain.
- Despite this, most Jordanian universities lack building-level water and energy monitoring; resources are billed in aggregate, so waste is invisible until a breakdown occurs.

### 2.2 The GJU-Specific Pain Point

In the center of GJU's campus operates a large, visible rotating water wheel:

- **Electric drive:** A large industrial motor powers the wheel during campus hours (~09:00 to 14:00) most weekdays.
- **Closed loop with periodic refresh:** Water is recirculated but drained and refilled with fresh potable water at intervals.
- **Evaporation losses:** The arid climate and continuous splashing cause substantial but unmeasured evaporative losses.
- **No measurement, no feedback:** There is no instrumentation on power draw, water level, refill volumes, or plaza occupancy. The motor runs regardless of whether anyone is present to enjoy the feature.
- **Physically off-limits:** Direct modification of the wheel or its plumbing is restricted, which further explains why the problem has gone un-quantified — retrofitting has seemed infeasible.

### 2.3 The Campus-Wide Gap

Beyond the wheel, GJU buildings also lack granular water telemetry. After-hours flows, fixture leaks, and abnormal consumption patterns are undetectable in monthly bulk utility bills. Every small leak or stuck valve is discovered late, after waste has occurred.

### 2.4 Why This Matters for the Competition

HydroLoop addresses the two core themes of the IEEE R8 Sustainable Universities Program simultaneously: **energy efficiency and renewable energy** (reducing motor and pump electricity) and **waste reduction** (cutting water loss and unnecessary refills). It does so by targeting an **iconic, visible, high-narrative campus asset** in the world's second most water-stressed country — a story judges can see, remember, and rally behind.

---

## 3. Proposed Solution

HydroLoop is delivered in two technical layers and one institutional deliverable.

### 3.1 Layer 1 — Flagship: The Smart Water Wheel Observatory

A **non-invasive sensor package** is installed around the wheel. Nothing physically modifies the wheel itself, which respects the existing access restriction and lowers the administrative barrier to approval.

| Sensor | Purpose | Non-Invasive? |
|---|---|---|
| Clamp-on CT current sensor / PZEM-004T | Measures motor electrical consumption (kWh, live power draw, runtime) | Yes — clamps on external supply line |
| Ultrasonic water-level sensor | Tracks water-level drop over time → evaporation and splash loss; detects refill events | Yes — mounted above basin, no water contact required |
| BME280 weather station | Air temperature, humidity, barometric pressure near the wheel | Yes — pole-mounted |
| ESP32-CAM plaza camera | Counts plaza occupancy during wheel runtime → computes "waste vs. value" hours | Yes — mounted on adjacent lamppost, privacy-preserving aggregate counts only |

Data flows through an ESP32 → MQTT → time-series database (InfluxDB) pipeline. A machine-learning layer (regression for evaporation modeling, anomaly detection for refill cycles, correlation between occupancy and runtime) produces the actionable insight:

> *"The wheel runs five hours per day. The plaza has fewer than five people in it for a majority of that runtime. We are spending kilowatt-hours and evaporating liters for an empty plaza."*

### 3.2 Layer 2 — Network: AquaSense Campus-Wide Water Intelligence

The same ESP32 + MQTT platform is replicated to five to seven high-value buildings (selected jointly with facilities — e.g., main academic, student dorms, engineering labs, cafeteria). Each site gets:

- A clamp-on or inline flow sensor at the main water inlet
- A baseline-learning ML model that flags leaks, after-hours flow, and abnormal consumption
- A unified building-level view in the central dashboard

This upgrades the flagship from a single-asset study into a **campus intelligence platform** — the most important move for impact, scalability, and judging.

### 3.3 Institutional Deliverable — Evidence-Based Retrofit Proposal

A formal document handed to GJU Facilities and Sustainability offices containing:

- The measured monthly electricity cost of the wheel
- The measured monthly water cost of the wheel
- A ranked list of retrofit options, each with cost/benefit modeled from actual data:
  1. Occupancy-triggered operation (run the wheel only when the plaza is in use)
  2. Retractable evaporation cover
  3. Variable-frequency drive on the motor
  4. Greywater-based refill loop (wudu / sink water instead of potable)
- Projected annual water and kWh savings, with CO₂e equivalent

This is the deliverable that converts HydroLoop from "student project" into "institutional change agent" — and is itself a strong winning-proposal artifact.

### 3.4 Public-Facing Twist (Differentiator)

A **QR code at the base of the wheel** links to the live HydroLoop dashboard. Any student can scan and see the wheel's live electricity draw, liters lost to evaporation today, and running tally of savings since HydroLoop went live. The iconic decoration becomes an active campus sustainability conversation — a unique, memorable, highly judge-friendly artifact that no other IEEE R8 team will have.

---

## 4. Technical Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      GJU CAMPUS (Field Layer)                    │
│                                                                  │
│   ┌─────────────┐    ┌─────────────────┐    ┌───────────────┐    │
│   │ Water Wheel │    │ Building Water  │    │ Weather /     │    │
│   │ Sensor Pod  │    │ Flow Sensors    │    │ Plaza Camera  │    │
│   │ (ESP32)     │    │ ×6 (ESP32)      │    │ (ESP32-CAM)   │    │
│   └─────┬───────┘    └────────┬────────┘    └───────┬───────┘    │
└─────────┼─────────────────────┼─────────────────────┼────────────┘
          │  Wi-Fi / LoRa       │                     │
          ▼                     ▼                     ▼
   ┌─────────────────────────────────────────────────────────┐
   │          MQTT Broker (Mosquitto on cloud VPS)            │
   └──────────────────────────┬──────────────────────────────┘
                              │
                              ▼
   ┌─────────────────────────────────────────────────────────┐
   │      Time-Series DB (InfluxDB)  +  ML Services (Python)  │
   │   • Evaporation regression (weather → loss)              │
   │   • Occupancy correlation (camera → runtime value)        │
   │   • Building anomaly detection (Isolation Forest / LSTM)  │
   └──────────────────────────┬──────────────────────────────┘
                              │
                              ▼
   ┌─────────────────────────────────────────────────────────┐
   │   Grafana Dashboard + Public QR-linked Kiosk View        │
   └─────────────────────────────────────────────────────────┘
```

**Stack summary:**

- **Edge:** ESP32 (wheel pod + 6 building nodes), ESP32-CAM, PZEM-004T, ultrasonic (HC-SR04 / JSN-SR04T), BME280, clamp-on flow sensors.
- **Transport:** Wi-Fi primary, LoRa fallback for out-of-range buildings.
- **Backend:** Mosquitto MQTT broker, InfluxDB for time series, small Python service for ML inference and API, Grafana for dashboards.
- **Public kiosk:** Budget tablet mounted near the wheel (weatherproof case) running the dashboard in kiosk mode.

---

## 5. Implementation Plan (3 Months Post-Approval)

| Phase | Weeks | Key Activities | Deliverable |
|---|---|---|---|
| **0 — Stakeholder & Access** | 1 | Memorandum of Understanding with GJU Facilities & Sustainability; procurement initiated; risk-register opened | Signed MoU; PO list |
| **1 — Wheel Sensor Bring-Up** | 2–3 | Assemble wheel sensor pod in lab; test on mock setup; secure permission for lamppost and pole mounts; deploy sensors around (not on) the wheel | Wheel node live streaming to MQTT |
| **2 — AquaSense Node Fabrication** | 3–5 | Build six building nodes in parallel; calibrate flow sensors; weatherproof enclosures | Six AquaSense nodes bench-verified |
| **3 — Network Deployment** | 5–7 | Install building nodes in selected sites (coordinated with facilities); verify telemetry | All nodes streaming live |
| **4 — ML & Dashboard** | 6–10 | Train evaporation model on collected data; train per-building baselines; build Grafana dashboards; build public kiosk view | Live dashboard and ML services in production |
| **5 — Analysis & Retrofit Proposal** | 10–11 | Compile measurements; model retrofit scenarios; write institutional retrofit proposal | Retrofit report delivered to GJU admin |
| **6 — Launch Event & Demo** | 12 | Public kiosk launch near wheel with QR code; campus communications piece; final presentation preparation | Public-facing kiosk live; IEEE deliverables submitted |

**Parallelization note:** Hardware (team's strength) runs mostly in weeks 2–7, while data/ML work (project lead's strength) front-loads architecture and back-loads analytics. No single team member becomes a bottleneck.

---

## 6. Budget

Total requested: **≈ $1,400 USD** (well under the $2,000 cap, leaving margin for customs and shipping surprises common in Jordan).

| Category | Item | Qty | Unit ~USD | Subtotal |
|---|---|---:|---:|---:|
| **Wheel Flagship** | PZEM-004T current/voltage sensor kit | 1 | 40 | 40 |
|  | JSN-SR04T waterproof ultrasonic + mount | 1 | 30 | 30 |
|  | BME280 weather sensor + pole + wiring | 1 | 25 | 25 |
|  | ESP32-CAM + outdoor enclosure | 1 | 25 | 25 |
|  | Weatherproof enclosure, cabling, hardware | — | 100 | 100 |
| **AquaSense Network** | Flow sensor + ESP32 + enclosure | 6 | 80 | 480 |
|  | LoRa gateway / central WiFi AP | 1 | 80 | 80 |
| **Platform & Publication** | Cloud VPS + domain (3 months) | — | 80 | 80 |
|  | Public kiosk tablet + weatherproof mount | 1 | 200 | 200 |
|  | Launch signage, QR plaques, infographics | — | 80 | 80 |
| **Contingency** | Shipping, customs, replacement components | — | 260 | 260 |
| **Total** |  |  |  | **~1,400** |

---

## 7. Key Performance Indicators

All KPIs are measurable, evidence-based, and defensible before judges.

| KPI | Target at End of 3 Months |
|---|---:|
| Wheel motor kWh measured per day | Quantified for first time in GJU history |
| Wheel water loss (evaporation + refill) measured per month | Quantified for first time in GJU history |
| Potential electricity reduction identified (via retrofit proposal) | ≥ 30% |
| Potential water-refill reduction identified (via retrofit proposal) | ≥ 40% |
| Buildings under live water intelligence | ≥ 6 |
| Anomaly events auto-detected during pilot | ≥ 10 |
| Dashboard uptime | ≥ 95% |
| Public kiosk live at wheel plaza | Yes, with QR code |
| CO₂e avoided from projected electricity savings | Quantified monthly |
| Open-source release of hardware BOM + firmware + ML code | Yes, on GitHub |

---

## 8. Sustainability Impact

- **Environmental:** Quantified reduction of potable water waste in the second most water-stressed country on Earth, plus electricity savings that directly reduce imported-grid dependence and Scope 2 emissions.
- **Institutional:** A continuing monitoring platform that outlives the competition and keeps producing value for GJU's operations and sustainability reporting.
- **Behavioral:** The public QR-linked dashboard converts a passive decoration into an active educational instrument seen by every student, every day.

---

## 9. Scalability & Replicability

HydroLoop is deliberately designed to be **portable to any university in IEEE Region 8**.

- The wheel is *illustrative*, not essential. Any high-visibility, high-consumption "hero asset" (a fountain, a chiller plant, a boiler, a lab compressor) can play the same role.
- All hardware is commodity (ESP32 + commonly available sensors).
- All software is open-source (MQTT, InfluxDB, Grafana, Python).
- Final deliverables include a public GitHub repository with BOM, wiring diagrams, firmware, ML models, and dashboard configuration — other R8 universities can fork and deploy within weeks.

The competition outcome is therefore not a single installation; it is a **reference architecture for data-driven campus sustainability across the region**.

---

## 10. Team & Roles

*Team members to be confirmed before submission.* Proposed role structure:

| Role | Responsibility | Skill Fit |
|---|---|---|
| **Project Lead (ML / Data)** | Architecture, ML models, analytics, retrofit-proposal authorship, pitch | AI + data analytics (lead proposer) |
| **Hardware Lead** | Sensor node design, fabrication, weatherproofing, field deployment | Strong IoT hardware background |
| **Hardware Engineer(s)** | Parallel node assembly, on-campus installation, calibration | Strong IoT hardware background |
| **Integration / DevOps** | MQTT broker, InfluxDB, Grafana, kiosk deployment, uptime monitoring | Cross-functional |
| **Faculty Advisor** | Institutional liaison with Facilities and Sustainability offices | — |

---

## 11. Risk Assessment & Mitigation

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Administrative access to wheel area denied | Medium | High | MoU signed in Week 1; non-invasive design specifically chosen to minimize admin objection; fallback plan uses lamppost/pole mounts on public ground only |
| Hardware import delays / customs in Jordan | Medium | Medium | Contingency line in budget; parallel sourcing from regional and international suppliers; early procurement in Week 1 |
| Sensor miscalibration leading to inaccurate savings claims | Low | High | Cross-validation: evaporation measured two ways (ultrasonic + refill event counts); independent spot-check with manual flow measurement |
| Wi-Fi coverage gaps across buildings | Medium | Medium | LoRa fallback included in budget; flexible topology |
| ML model underperforms on limited training data | Low | Medium | Classical baselines (Isolation Forest, regression) chosen over deep learning — they work with weeks, not months, of data |
| Public kiosk vandalism / weathering | Low | Low | Weatherproof case; easily replaceable tablet; mount inside existing signage area |

---

## 12. Why HydroLoop Will Win

1. **Unique, specific, visible problem.** Most IEEE R8 proposals are generic. HydroLoop names a physical object at the center of a real campus.
2. **Irresistible narrative.** A water-wasting water wheel in the world's second most water-stressed country, on an engineering campus teaching sustainability. Judges will remember this proposal.
3. **Technically credible.** Two-layer architecture, commodity hardware, mature open-source software, realistic budget with margin.
4. **Scalable and replicable.** Reference architecture intentionally generalizable to any R8 university.
5. **Visible, measurable outcomes.** Public kiosk + open dashboard + retrofit report mean judges can verify impact in real time — and so can every student.
6. **Maximizes the team's strengths.** Hardware-strong teammates + data/ML lead map cleanly onto the two-layer architecture with no skill gaps.

---

## Appendix A — Open Items Before Submission

*To be completed by the team in the next 2–3 days.*

- [ ] Confirm final team member names and roles
- [ ] Secure faculty advisor signature / letter of support
- [ ] Optional: secure letter of intent from GJU Facilities or Sustainability office (strong credibility boost)
- [ ] Final proofread against the IEEE R8 Sustainable Universities submission checklist
- [ ] Confirm exact wheel motor nameplate rating if accessible (to refine budget for current sensor sizing)
- [ ] Confirm final list of six buildings for AquaSense with facilities input
