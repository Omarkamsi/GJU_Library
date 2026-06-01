# Node B — Building Flow Meter

Counts YF-S201 Hall-effect pulses, publishes L/min + cumulative liters every 10s.

## Wiring
| ESP32 | Sensor   |
|-------|----------|
| GPIO4 | YF-S201 yellow (signal, pulled up) |
| 5V    | YF-S201 red   |
| GND   | YF-S201 black |

## Calibration
`PULSES_PER_LITER = 450` is the datasheet typical for YF-S201. Verify against
a known-volume bucket and adjust per unit.
