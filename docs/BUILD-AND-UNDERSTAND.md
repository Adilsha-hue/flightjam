# FlightJam: understand it and plan the build

Reviewed upstream commit 9618c17. This is a bench telemetry research prototype named SPECTRA-SHIELD, not a complete aircraft or a demonstrated anti-jamming system.

## In everyday language

Think of the sender as posting a postcard containing altitude and battery information. CRC detects accidental damage to the postcard. HMAC is a secret-key seal proving it came from someone with the key. Sequence and time checks reject old postcards. The seal cannot make a lost postcard arrive, and it does not hide the postcard's contents.

The sender currently invents latitude, longitude, altitude, battery and satellite values. There is no attached GPS, battery measurement, autopilot, flight controller, motor or flight-control command path. The ground board checks frames and sends serial status lines to a laptop. This is one-way telemetry; it is not a bidirectional control system.

## What exists and what was verified

| Area | Repository implementation | Verification / limitation |
|---|---|---|
| Sender | ESP32-S3/SX1262; packed 17-byte mock payload | Source inspected; no physical board tested |
| Receiver | CRC, truncated HMAC-SHA256, replay guard | Source inspected; firmware not compiled in this review |
| Shared frame | 12-byte header + payload + 2-byte CRC + 16-byte MAC | Python mirror passed seven existing codec/replay self-tests |
| Lab disturbance node | Separate ESP32/CC1101 scaffold | Not built or operated; keep disturbance scenarios in software for the teaching model |
| Logger | Serial RX lines to SQLite and optional CSV | Existing simulator writes this schema |
| Analysis/dashboard | PER and received-signal summaries | Estimates require trustworthy transmitted counts and calibrated measurements |
| RF simulation | Logistic packet-success model and browser demo | Illustrative assumptions, not measured SX1262 performance |
| New learning lab | Both ends plus CRC-only/protected comparison | Actual browser HMAC, synthetic channel events, no radio hardware |

## Run the models on Windows

From the repository directory:

```powershell
python -m http.server 8765 --bind 127.0.0.1
```

Open http://127.0.0.1:8765/sim/learning-lab.html. Send a clean message, then select each scenario. With altered data and a recalculated CRC, the CRC-only receiver accepts the change while the authenticated receiver rejects it. Replaying a previously accepted message is also rejected by the protected receiver. Lost messages reach neither receiver. Browser cryptography requires a secure context; localhost provides that.

The original numerical model is at /sim/index.html. Its disturbance sliders are software parameters, not hardware instructions. Frequency changes do not currently affect its success model, and CW/noise share the same probability law.

```powershell
python host/sim/spectra_sim.py --selftest
python host/sim/spectra_sim.py --db out/review-simulation.db --sweep --replay --emit-csv out/review-packets.csv
```

Create `out` first if absent. The simulator appends runs to an existing database. Choose a new filename for independent runs. For analysis, install requirements in a virtual environment and pass `--fixed-db 90` to match the simulator; the analysis default is zero and otherwise shifts the horizontal axis by 90 dB.

## Hardware bill of materials: functional telemetry demonstration

| Part | Qty | Assigned function | Purchase / integration constraint |
|---|---:|---|---|
| Matching Heltec WiFi LoRa 32 development boards | 2 | Sender and receiver | Exact revision and regional radio variant must match the selected firmware configuration |
| USB data cables matching board connectors | 2 | Board power, programming and serial | Charge-only cables will not work |
| Laptop with available USB ports | 1 | PlatformIO, Python, logger/dashboard | Existing computer is sufficient |
| Powered USB hub | Optional 1 | Additional USB ports | Needed only if laptop ports/power are insufficient |
| Insulating enclosures | 2 | Protect the boards | Size from actual board and connector measurements |
| Insulating standoffs, screws, feet | 2 sets | Mechanical mounting | Match real mounting-hole diameter and spacing |
| Multimeter | 1 shared | Verify supply rails and continuity | Lab tool, not a node component |
| Jumper wires / small prototype board | Optional set | Future sensors | Integrated radios do not need external SPI jumper wiring |
| 3.3 V-compatible temperature or motion sensor | Optional 1 | Replace mock measurements | Requires driver, payload and receiver decoding changes |
| GNSS receiver | Optional 1 | Actual position instead of mock coordinates | Not required for this bench demo; needs power/serial integration |
| Battery and compatible protected power system | Optional per portable node | Portable power | Begin with USB; choose against exact board specifications |

No motors, ESCs, propellers, flight controller or aircraft battery are needed. The Heltec boards already contain their LoRa radios. The README/BOM incorrectly describes Heltec V3 as SX1278 and not ESP32-S3: the manufacturer's V3 product page specifies ESP32-S3 and SX1262. V3/V4 still need revision-specific validation; don't substitute based on the repository's description.

Manufacturer sources: https://heltec.org/project/wifi-lora-32-v3/ and https://heltec.org/project/wifi-lora-32-v4/ . Datasheet: https://resource.heltec.cn/download/WiFi_LoRa_32_V4/datasheet/WiFi_LoRa_32_V4.2.0.pdf . Current purchase prices were not verified. The original BOM's INR 29,100 total is a historical repository estimate, not a quotation, and omits an explicit separate ESP32 controller for its CC1101 node.

The repository also proposes RF attenuators, a combiner, coax adapters, a monitor receiver and a shielded enclosure for a conducted laboratory interference experiment. That is a separate institution-supervised RF setup, not part of this beginner build. Its RF protection, termination, calibrated levels and containment must be designed and approved by the lab. This deliverable does not provide an operational jammer wiring or deployment design.

## Model / enclosure concept

Use two separate bench modules labelled TX and RX. Each holds one development board on insulating standoffs, has an accessible USB opening and leaves reset/boot buttons reachable. The laptop sits outside the enclosures. Label the sender's optional sensor expansion area and the receiver's USB log connection. Keep cables strain-relieved. Do not invent enclosure dimensions: board revision, connector access and mounting-hole measurements are prerequisites for a dimensioned CAD file. This is a concept model, not fabrication-ready CAD or a validated circuit schematic.

## Issues to resolve before claiming a working physical build

1. Pin definitions are explicitly placeholders. Check every SPI/control pin, board power enable, RF switch and oscillator initialization against the exact revision; the generic PlatformIO board profile is not proof of compatibility.
2. Receiver passes the entire 256-byte buffer to the decoder rather than the received packet length. Short receptions may expose uninitialized buffer data to parsing. Header `h` is uninitialized if decoding exits early, yet logging reads its fields. Use actual received length and initialized output fields.
3. Sender and receiver compare independent uptimes. Different boot times can reject valid packets. Define synchronization or a session-based freshness protocol.
4. Sender sequence resets on reboot; receiver replay state is volatile and not per device. Define restart/session handling and persist or renegotiate freshness appropriately.
5. Public development key provides no real authentication security. Validate supplied key length/hex and provision private keys; use a constant-time MAC comparison.
6. Duty-cycle pacing runs after transmission. Startup can send two frames too closely, and the schedule is difficult to reason about. Gate each transmission before sending and validate actual airtime. Regulatory compliance has not been established here.
7. CRC-failed/MAC-failed headers are not trustworthy packet counters. Inferring transmitted count from min/max received sequence misses leading/trailing losses and all-lost runs. Log actual TX counts with run/session boundaries, separately count replay attempts, and report uncertainty.
8. Python RF simulation produces synthetic status labels instead of running every simulated packet through its codec/guard. Random RF corruption should not be interpreted as an authentication attack. Its seven crypto checks are independent tests.
9. Python baseline labelled interference-off still models finite disturbance. CW/noise are not separate physical models. Browser replay creates a fresh timestamp instead of retaining the original packet, and its step panel marks later checks passed even when an earlier one failed. The learning lab uses the original delivered frame for replay.
10. There is no implemented unprotected firmware baseline, frequency hopping, error-recovery protocol, encryption or autonomous failsafe. These features cannot be claimed from current code.

## Build order and acceptance criteria

First demonstrate the software learning lab and explain each outcome. Next compile sender and receiver for the exact purchased boards, resolve board initialization and framing issues, and validate the codec using fixed vectors. Then test the two-node telemetry path in a suitable authorized lab configuration. Verify that each TX produces the expected serial record and that actual TX counts match the analysis denominator. Add real sensors only after mock telemetry is stable. Finish with measured results and a documented enclosure; do not equate synthetic curves with hardware evidence.
