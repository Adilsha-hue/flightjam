# Conducted setup

The physical rig for SPECTRA-SHIELD V1. Everything is cabled on coax through
attenuators; the interferer never sees an antenna. See `docs/05-safety-legal.md`
for the rules this rig exists to satisfy.

## 1. Block diagram

```
   uav_node (SX1262)                       ground_node (SX1262)
        |                                        ^
        |                                             |
   [fixed attenuator A_fixed]                  [input]
        |                                             |
        +--------------[ 2-way combiner ]--------------+
                        /             \
                       /               \
        [step/variable att A_int]      [tap -> RTL-SDR Blog V4]
                  |
        interferer (CC1101)
```

- The **combiner** is the meeting point: friendly signal in one port, interferer
  in the other, sum out to the ground receiver.
- The **step attenuator `A_int`** in the interferer branch is the experimental
  variable that sets **J/S**.
- The **fixed attenuator `A_fixed`** in the friendly branch protects the receiver
  and pins the baseline link budget.
- The **RTL-SDR tap** watches the combined signal (and, separately, the air) to
  verify frequency, level, and containment.

## 2. Cabling order (assemble in this order)

1. **Ground node RX port** ← combiner sum port. Do not power anything yet.
2. **UAV node TX port** → `A_fixed` → combiner port 1.
3. **Interferer output** → `A_int` → combiner port 2.
4. **RTL-SDR** → tap coupler / spare port (or a separate probe), 50 Ω terminated
   where unused.
5. **Terminate** any open port with a 50 Ω load; floating ports change loss.
6. Power the two ESP32-S3 nodes; confirm the friendly link with the interferer
   **off** and `A_int` at maximum.

## 3. Harness checklist (before every session)

- [ ] All SMA connections finger-tight + 1/8 turn; no stress on the boards.
- [ ] `A_int` at max, interferer `off`, baseline link OK.
- [ ] 50 Ω loads on unused combiner/coupler ports.
- [ ] RTL-SDR sees the friendly carrier at the expected frequency/level.
- [ ] RTL-SDR sees **nothing** significant at 866.5 MHz away from the rig
      (containment check — see `docs/05-safety-legal.md` §1.2).
- [ ] Attenuator settings recorded and match the run label.

## 4. Connector / impedance notes

- Everything is **50 Ω**. Use SMA throughout; adapt SMA↔SMA, SMA↔U.FL/pigtail as
  needed for the Heltec/CC1101 antenna pads.
- Keep pigtails short and matched; note any that are swapped between sessions.
- The friendly nodes' on-board antenna pads may need a U.FL pigtail to SMA — this
  is the one place loss is easy to get wrong, so include it in calibration.

## 5. Roles on the bench

| Role | Owns |
|---|---|
| RF / test engineer | rig assembly, attenuator settings, RTL-SDR verification |
| Firmware (×2) | flashing nodes, interferer commands, serial capture |
| Software | logger run labels/metadata, analysis, figures |

Two people present whenever the interferer is enabled: one at the controls, one
watching the RTL-SDR.

## 6. Teardown

- Interferer `off` and `A_int` to max **before** unplugging anything.
- Bag and label attenuators by value; loss is only meaningful with a known part.
- Log any cabling change so calibration stays valid (else re-calibrate).
