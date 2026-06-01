# Node B — Building Flow Meter Spec

## BOM
- 1× ESP32 DevKit-C
- 1× YF-S201 ½″ Hall-effect flow sensor (or G1″ depending on pipe)
- 1× IP54 enclosure + glands
- 1× 5V/1A USB PSU

## Wiring
| ESP32 pin | Sensor    |
|-----------|-----------|
| GPIO4     | YF-S201 yellow (signal) |
| 5V        | YF-S201 red |
| GND       | YF-S201 black |

## Firmware
`firmware/node_b_flow/` — calibrate `PULSES_PER_LITER` (default 450) per unit
against a known-volume bucket.

## Bench-test acceptance
Pour 1 L of water through the sensor, confirm `total_l` increased by ~1.0 ± 0.05.
