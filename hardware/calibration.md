# Calibration

The J/S model in `host/analysis/per_plot.py` is only as good as the numbers fed
into it. This page explains how to measure each term and how to verify the rig
does not radiate.

```
J/S = (P_int - A_int) - (P_friendly - A_fixed)
```

| Term | Meaning | Source |
|------|---------|--------|
| `P_friendly` | UAV node output power at its antenna pad | `--friendly-dbm` |
| `A_fixed` | fixed attenuation in the friendly branch | `--fixed-db` |
| `P_int` | interferer output power at its antenna pad | `--interferer-dbm` |
| `A_int` | step attenuator setting for the run | run metadata (`--atten-db`) |

## 1. Measure the friendly link budget

1. Note the firmware TX power (`config.h: kTxPowerDbm`, default **+2 dBm**). This
   is `P_friendly` in first approximation; treat it as nominal until measured.
2. Sum the known fixed losses: fixed attenuator + pigtails + combiner insertion
   loss + connectors. `A_fixed` is the fixed attenuator only; keep extra bulk
   loss as a documented correction.
3. Sanity-check with the ground node's **RSSI** at the baseline (`A_int` max,
   interferer off): recorded RSSI should sit within a few dB of
   `P_friendly - (all path losses)`. A large gap means a wrong/loose cable or an
   unaccounted pad.

## 2. Measure the interferer level

1. Set the interferer to `cw`, `A_int` to a known value, and read the level on the
   RTL-SDR at the tap. Compare across attenuator steps; the deltas should match
   the step values within ~1 dB.
2. Convert the SDR reading to a nominal `P_int` using the tap/coupler loss and the
   SDR's own calibration (or use a spectrum analyser if available). Record the
   chain explicitly.
3. If you cannot calibrate absolute power, run a **relative** sweep and report J/S
   as *changes from a reference point* rather than absolute dB — state this in
   the report.

## 3. Verify the harness path loss per attenuator setting

For each `A_int` step:

1. Interferer `off`; log a short baseline run and record mean RSSI.
2. The step attenuator only affects the interferer path, so the friendly RSSI
   should be **flat** across steps. Any change means coupling/settling or a bad
   connector — fix before sweeping.
3. Optionally inject a known friendly-side signal and confirm the combiner/port
   losses so the J/S denominator is trustworthy.

## 4. Containment verification (do this every session)

1. Put the RTL-SDR on a **separate** small antenna, away from the rig.
2. With the interferer at `cw` and `A_int` at minimum (worst case), scan around
   866.5 MHz (± 1 MHz). You should see only a noise floor well below the
   conducted level.
3. If a real signal is present off-rig, **stop**: a shield/connector is open.
   Re-seat SMA joints and repeat.
4. Only after containment passes may J/S runs proceed
   (`docs/05-safety-legal.md`).

## 5. SDR setup notes

- RTL-SDR Blog V4 with `rtl_sdr` / GQRX / `gqrx`, centred ~866.5 MHz, gain manual
  (not AGC) so readings are comparable across runs.
- Note the front-end gain and the tap loss; keep them identical between sessions.
- Save a spectrum screenshot per calibration for the report appendix.

## 6. Feeding results into analysis

```
python3 host/analysis/per_plot.py --db host/logger/spectra.db \
    --out out/per_vs_js.png \
    --interferer-dbm <P_int> --friendly-dbm <P_friendly> --fixed-db <A_fixed>
```

`A_int` comes from each run's `--atten-db` metadata. If absolute calibration was
not possible, report J/S as relative and say so.

## 7. Record-keeping

- Keep a calibration log: date, attenuator parts used, measured losses, SDR gain.
- Re-calibrate whenever cabling, boards, or attenuators change.
- Store the numbers in the report; never cite nameplate values as measured ones.
