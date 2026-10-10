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
