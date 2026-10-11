# Two-board telemetry bench validation

Status: reference TX/RX firmware compiled; physical testing has not been performed. This validates normal encrypted telemetry only. The browser world is not physical evidence.

## Identify the hardware first

Record board name, printed revision, regional RF variant, antenna band and connector. Reference firmware targets Heltec WiFi LoRa 32 V3, 863–870 MHz variant at 866.5 MHz. Do not upload to V4 or a different band variant without revising and validating initialization. Confirm the operating configuration is permitted for your location before enabling transmission.

Use two USB data cables, compatible antennas or an engineered lab RF termination, and a multimeter. Keep nodes stationary on the bench. The integrated radio uses NSS8 / SCK9 / MOSI10 / MISO11 / RESET12 / BUSY13 / DIO1 14; do not add external wires between the integrated chips. Consult the exact revision schematic; the web board drawing is illustrative. Attach proper RF termination before powering TX. A logic analyzer can inspect accessible SPI signals; never probe an RF output with its digital inputs.

## Build and load deliberately

The generated private key is already local and ignored by Git. Do not regenerate it for ordinary restarts or expose it in reports. Never erase or roll back persistent storage under the same key: nonce reuse or replay-state loss requires rekeying both nodes. Do not publish compiled firmware containing a live key.

Identify one physical board at a time to assign COM ports. Replace the placeholders below; commands are examples, not executed uploads.

```powershell
.\.venv-build\Scripts\pio.exe device list
.\.venv-build\Scripts\pio.exe run -d reference-telemetry -e transmitter
.\.venv-build\Scripts\pio.exe run -d reference-telemetry -e receiver
.\.venv-build\Scripts\pio.exe run -d reference-telemetry -e receiver -t upload --upload-port COM_RX
.\.venv-build\Scripts\pio.exe run -d reference-telemetry -e transmitter -t upload --upload-port COM_TX
.\.venv-build\Scripts\python.exe host/bench_check.py --tx-port COM_TX --rx-port COM_RX --seconds 190
```

Close other serial monitors first. The capture tool avoids intentionally asserting DTR/RTS; opening USB serial can still affect some boards. Check startup logs. Stop and diagnose any `Radio init error`; do not assume TX success merely because firmware uploaded.

## Measurements and pass criteria

| Check | Expected evidence | Status |
|---|---|---|
| Supply / assembly | Measured rails match manufacturer specification; no shorts or resets | Pending |
| Radio startup | TX and RX ready messages, no initialization errors | Pending |
| Normal delivery | TX code 0 and matching RX OK boot/sequence; correct mock payload | Pending |
| TX restart | Boot increases; sequence restarts; new packets accepted | Pending |
| RX restart | Prior high-water state retained; new packets accepted | Pending |
| Duplicate / older authenticated frame | RX REPLAY, no accepted repeated frame | Pending; requires controlled fixture |
| Invalid authentication tag | RX BAD_TAG, no accepted payload | Pending; requires controlled fixture |
| Invalid length / device / version | RX BAD_HEADER, no accepted payload | Pending; requires controlled fixture |
| Loss / recovery | Receives stop when RX is powered off and resume after restoring RX | Pending |

The capture tool observes logs only. It does not generate corrupted or replayed radio packets, test crypto itself, or prove rejection from silence. A controlled isolated fixture is needed for those negative tests. Never remove the TX antenna while transmitting. Log both nodes during the same window, retain raw capture, and report sample count, duration and reset events. A 190-second run covers only a few packets at this slow rate; it is a smoke test, not a reliability claim. RSSI alone does not establish range, antenna quality or compliance.

## What remains after a successful bench test

Real GNSS driver and its verified power/UART wiring; independent backup hardware; enclosure/power design; integration testing. Flight control/failsafe is not implemented. Exact analog/RF verification needs physical instruments and measurements. Wokwi can exercise supported MCU peripherals; it lacks a listed built-in SX1262 model and cannot replace this bench.

Sources: [Heltec V3](https://heltec.org/project/wifi-lora-32-v3/), [Wokwi hardware](https://docs.wokwi.com/getting-started/supported-hardware), [PlatformIO monitor](https://docs.platformio.org/en/stable/core/userguide/device/cmd_monitor.html), [Saleae SPI](https://www.saleae.com/support/protocol-analyzers/analyzer-user-guides/using-spi).
