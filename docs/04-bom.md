# 04 - Bill of materials

Machine-readable source of truth: [`bom.csv`](bom.csv). This page mirrors it and
adds sourcing notes. All prices are verified India street prices (2026) in INR.

## Line items

| # | Item | Qty | Unit ₹ | Total ₹ | Category |
|---|------|----:|------:|--------:|----------|
| 1 | Heltec WiFi LoRa 32 V4 (ESP32-S3 + SX1262) | 2 | 3,549 | 7,098 | friendly link |
| 2 | CC1101 868 MHz module (interferer) | 2 | 250 | 500 | interferer |
| 3 | SMA step attenuator 0–10 dB (1 dB step) | 1 | 2,500 | 2,500 | RF passives |
| 4 | Fixed SMA attenuators (6/10/20 dB set) | ~4 | 1,500 | 6,000 | RF passives |
| 5 | 2-way power combiner / divider | 1 | 2,000 | 2,000 | RF passives |
| 6 | SMA cables / adapters / pigtails | — | — | 1,500 | RF passives |
| 7 | RTL-SDR Blog V4 (monitor / verify) | 1 | 6,028 | 6,028 | monitoring |
| 8 | Breadboard / PSU / enclosure / 3D-printed mounts | — | — | 2,000 | mech / misc |
| 9 | Consumables / misc | — | — | 1,500 | mech / misc |
| | **TOTAL** | | | **29,100** | |

Budget floor ₹45,000 → **~₹16,000 headroom** for spares, a second interferer, or
report printing.

## Sourcing notes / vendors

- **Heltec WiFi LoRa 32 V4** — vihaaniotgateway.in (₹3,549). The older V3
  (SX1278) is cheaper (~₹2,099) but currently out of stock and not equivalent
  (no SX1262, no ESP32-S3).
- **CC1101 868 MHz** — zbotic.in / Robu.in / compoindia, ₹217–410, stock varies.
- **RF passives** (step + fixed attenuators, combiner, cables) — Synergy Telecom /
  Dipeshwari / rfconnector.in. Fixed attenuators often have **MOQ 5–10**; either
  buy a small set from one vendor or lean on the step attenuator plus a single
  20 dB pad.
- **RTL-SDR Blog V4** — amazon.in ₹6,028. The V4 is being succeeded by the V4L;
  either is fine (Rx-only monitor).

## Substitutions / contingencies

| Want | Instead | Why |
|---|---|---|
| CC1101 out of stock | second LoRa module in CW-adjacent mode | still produces the sweep; less ideal co-channel |
| Fixed-attenuator MOQ | step attenuator + 1× 20 dB pad | covers the same range |
| RTL-SDR unavailable | borrow/scope + spectrum analyser | any Rx that shows freq/level works |

## Excluded on purpose

- **HackRF One** (~₹23k–27k) and **ADALM-PLUTO** — Tier 2/3 SDR jammers, dropped
  from the default plan as too costly; kept only as optional upgrades.
- **Raspberry Pi** host (~₹9k) — dropped; the team's laptops run GNU Radio and
  the Python/Streamlit host tools.
