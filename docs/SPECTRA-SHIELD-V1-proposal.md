# SPECTRA-SHIELD V1 — Improved Proposal

Selective RF interference evaluation and a protected, authenticated UAV telemetry link.

- **Team:** 4 engineers
- **Duration:** 6–8 weeks
- **Budget:** ₹45,000–₹80,000 (this plan uses ~₹29,100)
- **Setting:** indoor RF lab, conducted (cabled) prototype only
- **Interference tier:** Tier 1 only
- **Friendly link:** 865–868 MHz LoRa (SX1262 / SX1276, CSS)
- **Deliverables:** improved proposal document + code scaffolding

---

## 1. Locked design

- **Friendly link:** LoRa **SX1262** on ESP32-S3 (Heltec WiFi LoRa 32 V4), CSS modulation, 865–868 MHz India license-exempt (25 mW e.r.p., 1% duty cycle).
- **Interferer (Tier 1):** **CC1101** 868 MHz module driven by an ESP32, emitting OOK/FSK CW plus same-channel noise on the LoRa channel.
- **Harness:** all-cabled / conducted.
  - `friendly TX → fixed att → 2-way combiner → friendly RX`
  - `interferer → variable / step att → same combiner`
- **Monitoring:** RTL-SDR Blog V4 to independently confirm interferer frequency/level and containment (no open-air radiation).

Tier 2 (HackRF One) and Tier 3 (ADALM-PLUTO) are dropped from the default plan as too costly; kept only as optional upgrade notes.

---

## 2. Bill of materials (verified India prices, 2026)

| Item | Qty | Unit ₹ | Total ₹ |
|---|---|---|---|
| Heltec WiFi LoRa 32 V4 (ESP32-S3 + SX1262) | 2 | 3,549 | 7,098 |
| CC1101 868 MHz module (interferer) | 2 | 250 | 500 |
| SMA step attenuator 0–10 dB (1 dB step) | 1 | 2,500 | 2,500 |
| Fixed SMA attenuators (6/10/20 dB set) | ~4 | 1,500 | 6,000 |
| 2-way power combiner / divider | 1 | 2,000 | 2,000 |
| SMA cables / adapters / pigtails | — | — | 1,500 |
| RTL-SDR Blog V4 (monitor / verify) | 1 | 6,028 | 6,028 |
| Breadboard / PSU / enclosure / 3D-printed mounts | — | — | 2,000 |
| Consumables / misc | — | — | 1,500 |
| **TOTAL** | | | **~29,100** |

Budget remaining vs the ₹45,000 floor: **~₹16,000** (spare radios, second interferer, or report printing).

Vendors referenced: zbotic.in, Robu.in, compoindia, Synergy Telecom / Dipeshwari (RF passives).

---

## 3. Test methodology (conducted)

- Calibrate the harness: measure path loss per attenuator setting using the RTL-SDR and SX1262 RSSI.
- Sweep **J/S** via the step attenuator in 1 dB steps; per point record PER, RSSI, SNR, p95 latency, jitter, and auth accept/reject.
- Headline metric: **J/S at 10 % PER**, plus a full PER-vs-J/S curve.
- Demonstrate LoRa resilience against an un-coded baseline (optional: CC1101 link as the fragile comparison).

---

## 4. Firmware + authentication design

- **Frame:** `hdr | dev_id | seq | timestamp | payload | CRC16 | HMAC-SHA256 (truncated 16 B)`. Verify CRC before HMAC.
- **Replay defense:** monotonic counter + timestamp window; optional ground-nonce challenge–response.
- **Crypto:** ESP32-S3 hardware AES (~7.3 MB/s) and SHA-256 (~26 MB/s); mbedTLS with `CONFIG_MBEDTLS_HARDWARE_AES/SHA`, or the dedicated ESP-IDF HMAC peripheral with an eFuse-burned key (one-shot, fine for small frames).
- **Payload:** CBOR/MsgPack to minimize airtime (duty-cycle compliance).
- **Provisioning:** per-device keys via build-time secrets, never hardcoded in source.

---

## 5. Software

- **Logging:** SQLite + CSV.
- **Dashboard:** Streamlit (PER/J/S plot, RSSI/SNR, latency histogram, auth counters).
- **Analysis:** Python / Matplotlib for report figures.

---

## 6. Repository layout

```
docs/       01-proposal.md  02-architecture.md  03-test-methodology.md  04-bom.md  05-safety-legal.md
firmware/   common/ (frame, auth, cbor) · uav_node/ · ground_node/ · interferer/
host/       logger/ (sqlite, csv) · analysis/ (PER plots) · dashboard/ (streamlit)
hardware/   conducted_setup.md  calibration.md
README.md   platformio.ini   requirements.txt
```

Firmware target: **PlatformIO + Arduino core + RadioLib** (SX1262). ESP-IDF noted as an option for the hardware-HMAC path.

---

## 7. Schedule (6–8 weeks, 4 engineers)

| Week | Work |
|---|---|
| W1 | Order BOM; bench + harness calibration |
| W2 | Friendly link bring-up; frame format |
| W3 | Auth: HMAC, counter/replay; provisioning + replay-attack demo |
| W4 | Interferer (CC1101 CW / same-channel); full conducted chain |
| W5 | J/S sweep runs; data capture |
| W6 | Dashboard + analysis + figures |
| W7 | Repeatability, edge cases, report draft |
| W8 | Buffer, demo, presentation |

Team split: 2x firmware, 1x RF/test, 1x software/analysis.

---

## 8. Safety & legal

- Conducted-only; verify no radiation with the RTL-SDR outside the rig.
- Operate only in 865–868 MHz and 2.4 GHz ISM license-exempt bands.
- Never GPS or cellular bands.
- Low EIRP behind attenuators.
- Interference research limited to a closed, cabled setup.
- India WPC rule: "Use of Low Power Equipment in the Frequency Band 865–868 MHz for Short Range Devices (Exemption from Licence) Rules, 2021", G.S.R. 853(E), 10 Dec 2021 (865–868 MHz, 25 mW e.r.p., 1% duty cycle).

---

## 9. Open risks

- CC1101 sometimes out of stock → fallback: a second LoRa module as interferer.
- Fixed attenuators have MOQ 5–10 → buy a small set from one vendor, or lean on the step attenuator + one 20 dB pad.
- ESP32-S3 hardware HMAC is one-shot (no streaming) → fine for our small frames.
