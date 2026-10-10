# 02 - Architecture

SPECTRA-SHIELD V1 evaluates a **protected, authenticated UAV telemetry link** on
the license-exempt 865–868 MHz band under **selective, conducted** interference,
and shows how a camera-drone-style telemetry link behaves when it is not
protected.

Everything is cabled into a shielded harness. Nothing radiates.

## Nodes

```
        +-----------------+        conducted RF        +-----------------+
        |    uav_node     |==========[ harness ]=======>|   ground_node   |
        | ESP32-S3 + SX1262|        attenuators          | ESP32-S3 + SX1262|
        +--------+--------+        + combiner           +--------+--------+
                 |                                                   |
                 | USB/serial (build, logs)                          | USB/serial
                 v                                                   v
        +---------------------------------------------------------------+
        |                         host (laptop)                         |
        |  logger.py (SQLite/CSV) -> analysis/per_plot.py -> dashboard  |
        +---------------------------------------------------------------+

        +-----------------+
        |   interferer    |===[ step/var attenuator ]===+
        | ESP32 + CC1101  |                             |
        +-----------------+                             |
                                          [ 2-way combiner ]---( RTL-SDR tap )
```

| Node | Board | Radio | Role |
|------|-------|-------|------|
| `uav_node` | ESP32-S3 (Heltec V4) | SX1262 | transmits signed telemetry |
| `ground_node` | ESP32-S3 (Heltec V4) | SX1262 | receives, verifies, logs to serial |
| `interferer` | ESP32 dev | CC1101 | CW / same-channel noise into the harness |
| monitor | — | RTL-SDR Blog V4 | verifies interferer frequency/level, containment |

## Friendly link

- LoRa CSS, 866.5 MHz, BW 125 kHz, SF9, CR 4/5, sync word `0x12`.
- Low TX power (default +2 dBm); all path loss is added in the harness.
- Airtime pacing keeps duty cycle under the 1% limit for 865–868 MHz.

## Frame format

All multi-byte header fields are **big-endian**.

```
+------+------+--------+--------+--------+------------------+--------+----------+
| ver  | dev  | seq(4) | ts(4)  | plen(2)| payload (plen)   | crc(2) | mac(16)  |
+------+------+--------+--------+--------+------------------+--------+----------+
```

- `ver` = frame version (currently 1); `dev` = device id.
- `seq` = monotonic counter; `ts` = sender uptime/UTC seconds.
- `crc` = CRC-16/CCITT-FALSE over `header || payload`.
- `mac` = first 16 bytes of `HMAC-SHA256(key, header || payload || crc)`.

Verify order on RX: length → version → **CRC** → **MAC** → replay guard.
The CRC is a cheap pre-filter; the MAC is the authenticity gate.

Implementation: `lib/spectra_common/include/spectra/frame.h` and `src/frame.cpp`
using mbedTLS. Overhead = 12 + 2 + 16 = 30 bytes.

## Authentication

- **HMAC-SHA256**, truncated to 16 bytes (~128-bit tag; fine for short frames).
- **Replay guard**: reject `seq <= last_seq` for the same device, and reject
  timestamps outside `±(kTimestampWindowSec + kClockSkewSec)`.
- **Key provisioning**: 32-byte PSK supplied at build time via
  `-DSPECTRA_PSK_HEX="<64 hex>"`; never committed. The scaffold falls back to a
  clearly-marked DEV placeholder so it builds without secrets.

Statuses emitted by the ground node:
`OK | TOO_SHORT | BAD_VERSION | BAD_CRC | BAD_MAC | REPLAY`.

## Interferer

- Tier 1 only: CC1101, 865–868 MHz, `cw` / `noise` / `off`, plus `freq` and
  `power` commands.
- Feeds the combiner through a step/variable attenuator. The attenuator setting
  is the experimental variable that sweeps **J/S**.

## Host pipeline

1. `host/logger/logger.py` — reads `RX,...` serial lines → SQLite (+ optional
   CSV). Each logging session is a **run** with its attenuator setting and mode.
2. `host/analysis/per_plot.py` — computes PER per run, maps attenuator → J/S,
   plots PER-vs-J/S and reports **J/S at 10% PER**.
3. `host/dashboard/app.py` — Streamlit view of runs, PER, RSSI/SNR, auth counters.

## Repository map

```
lib/spectra_common/   frame + auth + config shared by all firmware
src/uav_node/         friendly transmitter
src/ground_node/      friendly receiver + verifier
src/interferer/       Tier-1 CC1101 interferer
host/logger/          serial -> SQLite/CSV
host/analysis/        PER vs J/S figures
host/dashboard/       Streamlit dashboard
hardware/             conducted setup + calibration
docs/                 proposal (01), architecture (02), ... safety (05)
```

## Design rationale (why this shape)

- **Conducted harness** makes results repeatable and removes legal/EMC risk.
- **HMAC + counter** turns a jamming/forgery experiment into an authenticated-link
  experiment: the link can lose packets but cannot be spoofed or replayed silently.
- **CC1101 Tier 1** is enough to produce a clean PER-vs-J/S curve at a fraction
  of the cost of an SDR jammer; HackRF/PLUTO remain optional upgrades.
