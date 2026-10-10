# 03 - Test methodology

How SPECTRA-SHIELD V1 turns a conducted interference experiment into a repeatable
**PER-vs-J/S** curve and a single headline number. Everything here is cabled;
see `hardware/conducted_setup.md` for the physical rig.

## 1. Definitions

- **PER** — fraction of *expected* transmissions the ground node did not accept as
  `OK`. Expected is the span of sequence numbers seen in a run
  (`max(seq) - min(seq) + 1` over header-bearing statuses); lost frames never
  arrive, so the span is the correct denominator. See
  `host/analysis/per_plot.py`.
- **J/S** — jammer-to-signal ratio at the ground receiver input, in dB:

  ```
  J/S = (P_int - A_int) - (P_friendly - A_fixed)
  ```

  `P_int` interferer output power, `A_int` the run's interferer-path step
  attenuator, `P_friendly` the UAV node output power, `A_fixed` the friendly
  path's fixed attenuation. Diagnose each term in `hardware/calibration.md`.
- **Auth status** — one of `OK | TOO_SHORT | BAD_VERSION | BAD_CRC | BAD_MAC | REPLAY`.
  `BAD_*` and `REPLAY` are frames that arrived but were correctly rejected.

## 2. Independent variables

| Variable | How it is swept | Typical range |
|---|---|---|
| J/S | interferer-path step attenuator, 1 dB steps | −5 … +20 dB |
| Interferer mode | `interferer` serial command (`cw`/`noise`/`off`) | 2–3 modes |
| Interferer frequency | `freq` command, clamped 865–868 MHz | on-channel + ±BW |

The primary sweep is **J/S**; mode and frequency are secondary contrasts.

## 3. Dependent variables (per run)

- PER and the accepted/lost counts.
- Mean and p95 **RSSI**, mean **SNR** (from the ground node).
- **Latency** (sender timestamp vs receive time) and **jitter**, p95.
- **Auth counters**: `BAD_CRC`, `BAD_MAC`, `REPLAY`, `TOO_SHORT`.

All rows land in SQLite (`runs`, `packets`) via `host/logger/logger.py`.

## 4. Procedure

1. **Calibrate** the harness (path loss per attenuator setting) —
   `hardware/calibration.md`. Do this once, and re-check if cabling changes.
2. **Init** the database: `python3 host/logger/logger.py --init`.
3. **Set the interferer** to `off`; log a baseline run (PER should be ~0).
4. **Sweep J/S**: for each step setting, set the interferer to `cw` (or `noise`),
   then log one run with the matching metadata:
   ```
   python3 host/logger/logger.py --port /dev/ttyUSB0 \
       --run-label "cw att=6dB" --atten-db 6 --mode cw --freq-mhz 866.5
   ```
   Hold every run to the same duration / packet count so PER is comparable.
5. **Repeat** each point ≥3 times to expose run-to-run variance; keep the run
   label encoding the point so it is auditable.
6. **Analyse**:
   ```
   python3 host/analysis/per_plot.py --db host/logger/spectra.db \
       --out out/per_vs_js.png --interferer-dbm 10 --friendly-dbm 2 --fixed-db 10
   ```
   This prints the per-run table, the **J/S at 10% PER**, and writes the figure.
7. **Optional contrast** — repeat a subset against an un-coded CC1101 link as a
   fragile baseline, to show LoRa CSS + coding resilience.

## 5. Controls & hygiene

- **Baseline** run with the interferer off, every session.
- **Containment** check with the RTL-SDR before any interferer run
  (see safety doc): no meaningful signal reachable off-rig.
- **Fixed geometry**: same cables, same attenuators, same boards, same firmware
  build; record a hash/build id if firmware changes.
- **Run length** fixed (e.g. 200 packets or 120 s) and identical across points.
- **One variable at a time**: change only the attenuator between points.

## 6. Acceptance criteria (what a good result looks like)

- Baseline PER ≤ 1%.
- A monotonic PER rise with J/S, with a well-defined **J/S at 10% PER**.
- At high J/S, rejected frames appear as `BAD_CRC` (CRC catches garbled frames)
  and `BAD_MAC` (corrupted-but-CRC-passing frames fail the tag), proving the
  auth layer, not just the CRC, is doing work.
- A **replay demo** (re-transmit a captured valid frame) is judged `REPLAY`, i.e.
  the counter/timestamp guard wins.

## 7. Threats to validity

- **Cable drift / connector wear** changes loss between sessions → recalibrate.
- **Board-to-board RSSI variance** → characterise both receivers or fix one pair.
- **Duty-cycle pacing** must be respected or runs are not representative of a
  compliant link.
- **J/S model is nominal**: it assumes the calibrated `P*`/`A*` terms; state the
  measured values in the report, not the nameplate ones.
