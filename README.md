# SPECTRA-SHIELD V1

Selective RF interference evaluation and a protected, authenticated UAV telemetry
link. Conducted (cabled) indoor prototype only.

- Friendly link: LoRa SX1262 on ESP32-S3 (Heltec WiFi LoRa 32 V4), 865-868 MHz.
- Interferer (Tier 1): CC1101 868 MHz, CW / same-channel noise.
- Auth: CRC16 + truncated HMAC-SHA256 + monotonic-counter / timestamp replay guard.
- Host: Python logger (SQLite/CSV), analysis (PER vs J/S), Streamlit dashboard.

See `docs/SPECTRA-SHIELD-V1-proposal.pdf` (or `.md`) for the full proposal and BOM.

## Layout

```
docs/        proposal, architecture, test methodology, BOM, safety/legal
firmware?    -> see src/ + lib/ (PlatformIO project rooted here)
lib/         spectra_common: frame + auth shared by all nodes
src/         uav_node/, ground_node/, interferer/
host/        logger/, analysis/, dashboard/, sim/ (Python pipeline simulator)
sim/         self-contained offline HTML bench simulator (open in a browser)
hardware/    conducted setup + calibration notes
```

## Build firmware (PlatformIO)

```
pio run -e uav_node        # build UAV node
pio run -e ground_node     # build ground node
pio run -e interferer      # build Tier-1 interferer
pio run -e uav_node -t upload
```

Each node is a separate PlatformIO environment selected by `build_src_filter`.

> The firmware is **scaffolding**: pin maps and RadioLib call parameters are
> plausible defaults and must be verified against your exact boards before use.

## Run the host tools

```
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt

python3 host/logger/logger.py --init           # create the SQLite DB
python3 host/analysis/per_plot.py --db host/logger/spectra.db --out out/per_vs_js.png
streamlit run host/dashboard/app.py
```

> On a PEP 668 "externally managed" system where `python3 -m venv` is unavailable,
> install dependencies with:
> `python3 -m pip install --user --break-system-packages -r requirements.txt`.

## How it works

**The authenticated frame.** Every transmission is one 47-byte frame:

```
ver(1) dev(1) seq(4) ts(4) plen(2) payload(17) crc(2) mac(16)   = 47 bytes
```

Reception verifies in order: length -> version -> CRC16/CCITT-FALSE -> HMAC-SHA256
(truncated to 16 B) -> replay guard (monotonic `seq` + a +-300 s timestamp window).
Each failure maps to a distinct status the logger records:
`OK / TOO_SHORT / BAD_VERSION / BAD_CRC / BAD_MAC / REPLAY`. Because the MAC covers
`header || payload || CRC`, a corrupted or forged frame fails even if its CRC
happens to match.

**The RF / J-S model** (conducted; all powers dBm):

```
S    = P_TX - A_FIXED                                    friendly signal (+2 - 90 = -88)
J    = S + J/S                                           interferer at the receiver
SINR = 10*log10( 10^(S/10) / (10^(N/10) + 10^(J/10)) )   N = -120 dBm noise
P(ok)= 1 / (1 + exp(0.70*(-6 - SINR)))                   decode prob vs SF9 threshold
```

Key the interferer up (or lower the interferer-path attenuator,
`A_INT = P_INT - S - J/S`) and SINR falls, so PER climbs from ~0 through ~50% near
SINR = -6 dB toward 100%:

| J/S (dB) | SINR (dB) | PER    |
| -------- | --------- | ------ |
| -8       | +8.0      | ~0%    |
| +6       | -6.0      | 50%    |
| +12      | -12.0     | ~98.5% |
| +24      | -24.0     | ~100%  |

**What's simulated.** Both simulators below share this exact frame codec, crypto
and constant set. The pipeline simulator rolls the physical outcome, then writes
real `packets` rows the host tools consume unchanged; the HTML bench simulator
does the same live, with real SHA-256/HMAC/CRC16.

## Simulator

Two simulators reproduce the firmware's frame codec, replay guard and RF/J-S model
without hardware.

- **Pipeline simulator** — writes real packets/db rows the host tools consume:

  ```
  python3 host/logger/logger.py --db out/sim.db --init
  python3 host/sim/spectra_sim.py --db out/sim.db --sweep --replay \
      --packets 250 --seed 7 --emit-csv out/sim_packets.csv
  python3 host/analysis/per_plot.py --db out/sim.db --out out/per_vs_js.png \
      --fixed-db 90 --friendly-dbm 2 --interferer-dbm 10 --target 0.10
  ```

  Run `python3 host/sim/spectra_sim.py --selftest` to check the codec/crypto vectors.

- **Browser bench simulator** — a single offline HTML file (no CDN), real
  SHA-256/HMAC/CRC16 and a live J/S sweep. Open directly or serve it:

  ```
  python3 -m http.server 8080 --directory sim
  # then browse http://127.0.0.1:8080/index.html
  ```

## Safety

Conducted-only, shielded setup. 865-868 MHz / 2.4 GHz ISM license-exempt bands
only. Never GPS or cellular. See `docs/05-safety-legal.md`.
