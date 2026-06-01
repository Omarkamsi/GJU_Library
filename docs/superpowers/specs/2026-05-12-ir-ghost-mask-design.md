# IR Ghost Mask — System Design Spec
**Date:** 2026-05-12  
**Authors:** Mustafa + Partner  
**Status:** Draft — pending review

---

## 1. Project Overview

Active IR "Ghost" Mask: a physical adversarial device that evades facial recognition systems (FRS) by combining high-power infrared illumination with a printed adversarial patch. The device targets the full FRS pipeline — face detection first, then face identification — and evaluates transferability to black-box commercial APIs.

**Deliverables:**
1. Fully working MVP (benchtop rig + wearable glasses prototype)
2. Publishable research paper

**Timeline:**
- Month 1.5: Full implementation plan + documented research methodology submitted
- Month 3: MVP + paper final submission

---

## 2. Threat Model

| Property | Value |
|---|---|
| Attacker knowledge | White-box for development; black-box for transferability evaluation |
| Attack surface | Camera → Face Detector → Face Recognizer pipeline |
| Physical access | Worn by attacker (no access to target system internals) |
| Staged goal | Stage 1: detection evasion → Stage 2: identification evasion → Stage 3: commercial API |
| IRB status | Approved |

All experiments are conducted on consenting subjects (attacker themselves) in controlled environments. No surveillance or non-consenting subjects.

---

## 3. Attack Architecture — Option 2 (Hybrid)

```
┌─────────────────────────────────────────────────────┐
│                  ATTACK DEVICE                       │
│                                                      │
│  ┌──────────────┐    ┌──────────────────────────┐   │
│  │  ESP32       │    │  Glasses Frame           │   │
│  │  PWM 20kHz   │───▶│  850nm LED bank (4–8×)   │   │
│  │  Strobe ISR  │    │  940nm LED bank (4–8×)   │   │
│  │  Serial CLI  │    │  Adversarial patch print │   │
│  └──────────────┘    └──────────────────────────┘   │
│         │                        │                   │
│    MOSFET driver            IR flood + patch         │
└─────────────────────────────────────────────────────┘
                          │
                          ▼
              ┌───────────────────────┐
              │   Camera (CMOS)       │
              │   Webcam / iPhone /   │
              │   IP cam              │
              └───────────────────────┘
                          │
                          ▼
              ┌───────────────────────┐
              │   Face Detector       │
              │   YOLOv8-face         │
              │   MediaPipe           │
              │   MTCNN               │
              │   RetinaFace          │
              └───────────────────────┘
                          │
                          ▼
              ┌───────────────────────┐
              │   Face Recognizer     │
              │   FaceNet             │
              │   ArcFace             │
              │   InsightFace         │
              └───────────────────────┘
                          │
                          ▼
              ┌───────────────────────┐
              │   Black-box API       │
              │   AWS Rekognition /   │
              │   Azure Face /        │
              │   Face++              │
              └───────────────────────┘
```

### Two independent attack vectors

**Vector A — IR Saturation/Strobe (Hardware)**
- Floods camera CMOS with 850nm or 940nm IR
- Saturates pixels in the eye–nose–mouth triangle
- Erases facial landmarks needed by detectors
- Strobe mode targets rolling-shutter interference

**Vector B — Adversarial Patch (Digital→Physical)**
- Trained digitally against face recognizer embeddings (ArcFace / FaceNet)
- Printed at 8×8 cm and attached to glasses frame
- EOT (Expectation Over Transformation) applied for physical robustness
- Degrades cosine similarity in embedding space below identification threshold

**Combined effect:** IR destroys detection; patch degrades identification. Ablation study measures each vector's isolated and combined ASR.

---

## 4. Hardware Specification

### 4.1 Bill of Materials (target ≤ $50 hardware)

| Component | Spec | Qty | Est. Cost |
|---|---|---|---|
| ESP32 DevKit v1 | 240MHz, WiFi/BT, LEDC PWM | 1 | $6 |
| IR LEDs 850nm | High-power 3W, TO-220 or SMD | 8 | $8 |
| IR LEDs 940nm | High-power 3W, TO-220 or SMD | 8 | $8 |
| MOSFET | IRLZ44N or similar logic-level | 2 | $2 |
| Resistors / capacitors | Gate resistor 10Ω, decoupling 100µF | assorted | $2 |
| LiPo battery | 3.7V 1000mAh + TP4056 charger | 1 | $6 |
| 5V boost converter | MT3608 or similar | 1 | $2 |
| Glasses frame | Safety glasses / 3D printed | 1 | $5 |
| Protoboard / PCB | Perforated board or custom | 1 | $3 |
| IP camera (Phase 3) | Wyze Cam or generic ONVIF, IR night-vision | 1 | $25 |
| **Total** | | | **~$67** |

Remaining budget (~$80): Colab Pro already covered; reserve for commercial API credits (~$20–30) and printing adversarial patches.

### 4.2 ESP32 Firmware — Key Parameters

```
LED_GPIO_850     = 18    // Bank A
LED_GPIO_940     = 19    // Bank B
LEDC_BASE_FREQ   = 20000 // Hz carrier (above human hearing)
LEDC_RESOLUTION  = 8     // bits → 0–255 duty range
DEFAULT_DUTY     = 200   // ~78% on
STROBE_FREQ_HZ   = 60    // default; sweep 30/60/90/120 Hz
```

**Serial CLI commands:**
```
on             → continuous IR at current duty
off            → all LEDs off
duty N         → set PWM duty (0–255)
wave [850|940] → select wavelength bank
strobe HZ      → enable strobe at HZ frequency
sduty %        → strobe duty cycle (% of strobe period in HIGH state)
status         → print current config
```

**Sweep protocol for experiments:**
- Wavelength: 850nm → 940nm → both
- Duty: 64 / 128 / 200 / 255
- Strobe Hz: off / 30 / 60 / 90 / 120
- Camera: webcam → iPhone → IP cam

---

## 5. Software Architecture

### 5.1 Repository Structure

```
ir-ghost-mask/
├── firmware/
│   └── ir_ghost.ino           # ESP32 Arduino firmware
├── validation/
│   ├── ir_ghost_validator.py  # Real-time ASR measurement
│   ├── plot_asr.py            # CSV → ASR graphs
│   └── runs/                  # Per-experiment CSV logs
├── adversarial/
│   ├── patch_train.py         # Adversarial patch training (Colab)
│   ├── patch_eval.py          # Physical patch evaluation
│   ├── eot_transform.py       # EOT augmentation pipeline
│   └── patches/               # Saved patch images (PNG)
├── models/
│   └── download_models.sh     # Pull YOLOv8-face, InsightFace weights
├── paper/
│   └── figures/               # Generated plots for paper
└── docs/
    └── bom.md                 # Bill of materials
```

### 5.2 Validation Pipeline (`ir_ghost_validator.py`)

- **Input:** Webcam/camera stream + experiment label
- **Detectors:** YOLOv8-face (primary) + MediaPipe Face Detection (secondary)
- **Output:** Per-frame CSV with `[frame, t_sec, label, yolo_conf, yolo_count, mp_conf, mp_count]`
- **HUD:** Live confidence overlay on video feed
- **CLI:** `--cam INT --label STR --model PATH --out DIR`

**ASR calculation:**
```
ASR = frames where max_conf < threshold / total frames
threshold_detection = 0.5 (YOLO default)
threshold_id = cosine_sim < 0.3 (ArcFace default)
```

### 5.3 Adversarial Patch Training (`patch_train.py`)

**Framework:** PyTorch on Colab Pro (A100/L4)

**Algorithm:**
1. Initialize patch P (random noise, ~10×10 cm when printed)
2. For each batch:
   - Render P onto face images at random positions/scales/angles (EOT)
   - Apply physical transforms: brightness ±30%, contrast ±20%, JPEG compression, perspective warp
   - Forward pass through ArcFace/FaceNet
   - Loss = maximize embedding distance from enrolled identity + minimize detection confidence
   - Backward pass → update P via Adam (lr=0.01)
3. Repeat for N=500 epochs
4. Save patch as high-DPI PNG for printing

**EOT transforms applied:**
- Random rotation ±15°
- Random scale 0.8–1.2×
- Brightness/contrast jitter
- Gaussian noise σ=0.05
- JPEG compression quality 60–95
- Perspective warp ±10°

**Target models for training:** ArcFace (ResNet-50, MS1MV3) + FaceNet (Inception-ResNet-v2)

**Transfer targets for evaluation:** InsightFace, commercial API (black-box)

### 5.4 Identification Evasion Evaluation (`patch_eval.py`)

- Enroll identity: 10 clean photos of subject → extract embeddings → store mean template
- Attack condition: live frame with patch → extract embedding → compute cosine similarity
- Log: similarity score, decision (match/no-match), attack label

---

## 6. Experimental Design

### 6.1 Phases

**Phase 1 — Detection Evasion (Hardware IR)**
- Independent variables: wavelength (850nm / 940nm / both simultaneously), duty (64/128/200/255), strobe Hz (off/30/60/90/120), camera (webcam/iPhone/IP)
- Dependent variable: ASR per detector per condition
- Baseline: LEDs off, subject faces camera normally
- Duration: ~2 weeks of data collection

**Phase 2 — Identification Evasion (Adversarial Patch)**
- Train patch white-box on ArcFace + FaceNet
- Evaluate on: ArcFace, FaceNet, InsightFace (white-box transfer)
- Physical print and re-evaluate (physical gap study)
- Combine with IR (Phase 1 best config) → measure compound ASR

**Phase 3 — Black-box Commercial API**
- Target: **AWS Rekognition** (CompareFaces + DetectFaces APIs)
- Enroll subject via API (5–10 reference photos)
- Attack: submit IR+patch frames via API → measure ASR
- Budget: ~100–200 API calls per condition (~$15–25 total)

### 6.2 Cameras Under Test

| Camera | IR-cut filter | Expected difficulty | Role |
|---|---|---|---|
| Laptop webcam | Weak/none | Easy | Primary data collection |
| iPhone | Strong | Hard | Upper-bound difficulty |
| IP cam (night-vision) | None (IR-pass) | Easiest | Surveillance scenario |

### 6.3 Metrics

| Metric | Definition |
|---|---|
| ASR_det | % frames where face detector confidence < 0.5 |
| ASR_id | % frames where cosine similarity < 0.3 (no identity match) |
| ASR_combined | % frames evading both detection AND identification |
| Δ_embedding | Mean cosine distance shift vs. baseline |
| Physical_gap | ASR_digital − ASR_physical (patch degradation from printing) |

---

## 7. Division of Labor

| Task | Owner |
|---|---|
| ESP32 firmware (PWM, strobe, serial CLI) | Partner |
| LED array circuit (MOSFET driver, BOM procurement) | Partner |
| PCB/protoboard assembly | Partner |
| Glasses frame fabrication | Partner |
| Validation pipeline (`ir_ghost_validator.py`) | Mustafa |
| Adversarial patch training + EOT (`patch_train.py`) | Mustafa |
| Patch evaluation + embedding analysis | Mustafa |
| Commercial API evaluation | Mustafa |
| Data collection (joint) | Both |
| ASR analysis + figures | Mustafa |
| Paper writing (joint) | Both |

---

## 8. Paper Structure

1. **Abstract** — IR+patch hybrid attack, ASR across 7 open-source models + 1 commercial API
2. **Introduction** — FRS threat landscape, physical adversarial attacks, contributions
3. **Related Work** — IR attacks (Wenger et al.), adversarial patches (Brown et al.), EOT (Athalye et al.)
4. **Threat Model** — attacker assumptions, staged attack definition
5. **Attack Design**
   - 5.1 IR Saturation/Strobe (hardware vector)
   - 5.2 Adversarial Patch with EOT (digital→physical vector)
   - 5.3 Combined attack
6. **Experimental Setup** — hardware BOM, models, cameras, metrics
7. **Results**
   - 7.1 Detection evasion (wavelength × duty × strobe ablation)
   - 7.2 Identification evasion (white-box, transfer, physical gap)
   - 7.3 Commercial API (black-box)
   - 7.4 Compound attack ASR
8. **Discussion** — failure modes (iPhone IR-cut), defenses, limitations
9. **Conclusion + Future Work** — rolling shutter sync, adaptive IR, learned frequency sweep
10. **Ethics Statement** — IRB approval reference, no non-consenting subjects

**Target venues:** IEEE S&P, USENIX Security, NDSS, ACM CCS (top tier) — or CVPR/ECCV adversarial ML track as backup.

---

## 9. Milestones

| Milestone | Target Date | Owner |
|---|---|---|
| Hardware prototype v1 (ESP32 + LEDs, bench test) | Week 2 | Partner |
| Validation pipeline running, baseline CSV logged | Week 2 | Mustafa |
| Phase 1 data collection complete (all conditions) | Week 4 | Both |
| Adversarial patch trained (digital ASR ≥ 80%) | Week 5 | Mustafa |
| Patch printed + physical evaluation | Week 6 | Both |
| **Milestone: Full plan + research docs submitted** | **Week 6 (Month 1.5)** | Both |
| Wearable glasses prototype | Week 8 | Partner |
| Phase 3 commercial API evaluation | Week 9 | Mustafa |
| IP camera add (surveillance scenario) | Week 10 | Both |
| Paper draft complete | Week 11 | Both |
| **Final submission: MVP + paper** | **Week 12 (Month 3)** | Both |

---

## 10. Risk Register

| Risk | Likelihood | Mitigation |
|---|---|---|
| iPhone IR-cut blocks all IR effect | High | Document honestly as attack limitation; webcam + IP cam still show ASR |
| Printed patch loses effectiveness vs digital | Medium | EOT training specifically reduces physical gap; re-train if >30% drop |
| Commercial API rate limits / cost overrun | Low | Batch requests; cap at 200 calls; use free tier where available |
| ESP32 timer interrupt timing drift | Low | Validate strobe frequency with oscilloscope or logic analyzer |
| Partner hardware delay | Medium | Mustafa can simulate IR with IR remote + webcam for early software testing |

---

## 11. Open Questions

- [x] Commercial API: **AWS Rekognition** (most detailed confidence scores, per-image pricing)
- [x] Patch size: **8×8 cm** on glasses frame
- [x] Wavelength sweep includes **850nm + 940nm simultaneously** as a fourth condition
- [ ] Video submission alongside paper? (Strong for demo, some venues accept supplementary)
