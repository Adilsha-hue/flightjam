# 05 - Safety & legal

SPECTRA-SHIELD V1 is an **indoor, conducted (cabled) lab prototype**. It is
designed so that the interference work happens entirely inside a shielded
harness and nothing of consequence radiates. Read this before powering the
interferer.

## 1. Hard rules

1. **Conducted-only.** The interferer feeds the friendly receiver through
   attenuators and a combiner on coax. Never connect the interferer to an
   antenna, and never run it with the harness open.
2. **Verify containment.** Before every interferer session, sweep with the
   RTL-SDR around and away from the rig; there must be no meaningful signal at
   866.5 MHz beyond the harness. If there is, stop and fix the shield/cabling.
3. **Bands.** Operate only in **865–868 MHz** and **2.4 GHz ISM** (license-exempt
   in India). The interferer firmware clamps its frequency to 865–868 MHz.
4. **Never** transmit into **GPS / GNSS, cellular, aviation, or any licensed
   service band.** No exceptions.
5. **Low level.** Keep node TX power low (default +2 dBm) and always behind
   attenuators. Target EIRP at the "antenna" port is effectively zero because
   there is no antenna.
6. **No real aircraft.** This is a bench telemetry link between two boards. Do
   not involve, target, or attempt to detect or defeat any real UAS or its links.

## 2. India regulatory basis

- **Rule:** "Use of Low Power Equipment in the Frequency Band 865–868 MHz for
  Short Range Devices (Exemption from Licence) Rules, 2021".
- **Notification:** G.S.R. 853(E), dated 10 December 2021.
- **Terms:** 865–868 MHz, **25 mW e.r.p.**, **1% duty cycle**.
- Source: Wireless Planning & Coordination (WPC) Wing, Department of
  Telecommunications (thc.nic.in).

Our friendly link sits at 866.5 MHz and paces its airtime under the 1% duty
cycle. Because the experiment is conducted, our radiated level is far *below*
these limits, not at them.

## 3. Why this shape is safe

- **No antenna path** on the interferer → the "jammer" is a signal inside a wire,
  not in the air.
- **RTL-SDR monitor** is an independent witness that the energy stays on the
  bench.
- **Limited scope** (single channel, single band, low power) means even an
  accidental open port would be a low-power ISM emission, not a crisis.

## 4. If something goes wrong

- Interferer emitting unexpectedly: cut its power (USB/battery) first, then
  investigate. The `off` mode / `power` command is the software belt; the switch
  is the hardware braces.
- Suspected radiation leak: stop all runs, keep the rig as-is, sweep with the
  RTL-SDR, and re-seat every SMA connection before resuming.
- Any doubt about legality: stop and consult the lab supervisor / institution's
  spectrum policy before continuing.

## 5. Ethics / scope statement

This project evaluates the **resilience of a protected, authenticated telemetry
link** and the **cost of not protecting it**. It is not, and must not be turned
into, a tool for disrupting real drones, evading detection, or interfering with
anyone's service. The authentication layer is a first-class deliverable: the
point is that a jammed link can lose packets but cannot be silently spoofed or
replayed.
