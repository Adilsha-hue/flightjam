# SPECTRA-SHIELD V1

Selective RF interference evaluation and a protected, authenticated UAV telemetry
link. Conducted (cabled) indoor prototype only.

- Friendly link: LoRa SX1262 on ESP32-S3 (Heltec WiFi LoRa 32 V4), 865-868 MHz.
- Interferer (Tier 1): CC1101 868 MHz, CW / same-channel noise.
- Auth: CRC16 + truncated HMAC-SHA256 + monotonic-counter / timestamp replay guard.
- Host: Python logger (SQLite/CSV), analysis (PER vs J/S), Streamlit dashboard.

See `docs/SPECTRA-SHIELD-V1-proposal.pdf` (or `.md`) for the full proposal and BOM.

## Working software project demo

Run `./Start-Demo.ps1` in PowerShell, then open
http://127.0.0.1:8765/sim/learning-lab.html and click **Run project presentation**.
This demonstrates live sender/receiver telemetry, a virtual jammer with
continuous or burst disturbance, recovery, HMAC verification and replay rejection.
It includes a component model, delivery-failure graph, event log and CSV export
with a copyable fallback. All disturbance stays in software; the demo emits no RF.
See `docs/PROJECT-DEMO.md` for the presentation script and model limitations,
and `docs/BUILD-AND-UNDERSTAND.md` for component assignments and firmware gaps.

The hardware behavior model is at http://127.0.0.1:8765/sim/hardware-lab.html.
See `hardware/HARDWARE-DESIGN.md` for the researched assembly, optional input
connections and physical validation plan.

## Layout

```
docs/        proposal, architecture, test methodology, BOM, safety/legal
firmware?    -> see src/ + lib/ (PlatformIO project rooted here)
lib/         spectra_common: frame + auth shared by all nodes
src/         uav_node/, ground_node/, interferer/
host/        logger/, analysis/, dashboard/
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

## Safety

Conducted-only, shielded setup. 865-868 MHz / 2.4 GHz ISM license-exempt bands
only. Never GPS or cellular. See `docs/05-safety-legal.md`.


### Unified responsive workspace

Run `./Start-Demo.ps1` and open http://127.0.0.1:8765/sim/index.html. Shared navigation brings together hardware assembly, wiring faults, flight world, code walkthrough, parts and firmware, learning, and the preserved original simulator. Section URLs use hashes, and loaded labs retain state when switching tabs. Mobile navigation scrolls horizontally; tables scroll inside their own regions. These are software simulations; hardware validation is still required.
