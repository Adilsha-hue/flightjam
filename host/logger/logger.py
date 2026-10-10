#!/usr/bin/env python3
"""SPECTRA-SHIELD host logger.

Reads CSV reception lines from the ground node over serial and stores them in
SQLite (and optionally a CSV mirror).

Ground node line format:
    RX,<millis>,<seq>,<status>,<rssi>,<snr>,<payload_len>

Usage:
    python3 logger.py --init
    python3 logger.py --port /dev/ttyUSB0 --run-label "js=6dB" --atten-db 6
"""
from __future__ import annotations

import argparse
import csv
import sqlite3
import sys
import time
from pathlib import Path

DEFAULT_DB = Path(__file__).parent / "spectra.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS runs (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    label       TEXT NOT NULL,
    attenuator_db REAL,
    interferer_mode TEXT,
    freq_mhz    REAL,
    started_at  TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS packets (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id      INTEGER NOT NULL REFERENCES runs(id),
    device_ms   INTEGER,
    seq         INTEGER,
    status      TEXT,
    rssi        REAL,
    snr         REAL,
    payload_len INTEGER,
    logged_at   TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_packets_run ON packets(run_id);
"""

VALID_STATUS = {"OK", "TOO_SHORT", "BAD_VERSION", "BAD_CRC", "BAD_MAC", "REPLAY"}


def connect(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: Path) -> None:
    with connect(db_path) as conn:
        conn.executescript(SCHEMA)
    print(f"initialized {db_path}")


def start_run(conn: sqlite3.Connection, label: str, atten_db: float | None,
              mode: str | None, freq_mhz: float | None) -> int:
    cur = conn.execute(
        "INSERT INTO runs(label, attenuator_db, interferer_mode, freq_mhz) "
        "VALUES (?,?,?,?)",
        (label, atten_db, mode, freq_mhz),
    )
    conn.commit()
    return int(cur.lastrowid)


def parse_line(line: str):
    """Return a dict for a valid RX line, else None. Counters lines with
    'ignored' so the caller can track malformed input."""
    line = line.strip()
    if not line.startswith("RX,"):
        return None
    parts = line.split(",")
    if len(parts) != 7:
        return None
    _, ms, seq, status, rssi, snr, plen = parts
    if status not in VALID_STATUS:
        return None
    try:
        return {
            "device_ms": int(float(ms)),
            "seq": int(float(seq)),
            "status": status,
            "rssi": float(rssi),
            "snr": float(snr),
            "payload_len": int(float(plen)),
        }
    except ValueError:
        return None


def log_serial(port: str, baud: int, db_path: Path, label: str,
               atten_db: float | None, mode: str | None,
               freq_mhz: float | None, csv_path: Path | None) -> None:
    import serial  # pyserial, imported lazily so --init needs no hardware

    conn = connect(db_path)
    run_id = start_run(conn, label, atten_db, mode, freq_mhz)
    print(f"run #{run_id} '{label}' -> {db_path}")

    csv_file = csv.writer(open(csv_path, "w", newline="")) if csv_path else None
    if csv_file:
        csv_file.writerow(["run_id", "device_ms", "seq", "status", "rssi",
                           "snr", "payload_len"])

    ignored = 0
    with serial.Serial(port, baud, timeout=1) as ser:
        while True:
            raw = ser.readline().decode("ascii", errors="replace")
            if not raw:
                continue
            rec = parse_line(raw)
            if rec is None:
                if raw.strip() and not raw.startswith(("uav", "ground", "ctl")):
                    ignored += 1
                    print(f"  [skip] {raw.strip()}", file=sys.stderr)
                continue
            conn.execute(
                "INSERT INTO packets(run_id, device_ms, seq, status, rssi, snr, "
                "payload_len) VALUES (?,?,?,?,?,?,?)",
                (run_id, rec["device_ms"], rec["seq"], rec["status"],
                 rec["rssi"], rec["snr"], rec["payload_len"]),
            )
            conn.commit()
            if csv_file:
                csv_file.writerow([run_id, rec["device_ms"], rec["seq"],
                                   rec["status"], rec["rssi"], rec["snr"],
                                   rec["payload_len"]])
            print(f"  {rec['status']:9s} seq={rec['seq']:<6d} "
                  f"rssi={rec['rssi']:6.1f} snr={rec['snr']:5.1f}")


def main() -> int:
    ap = argparse.ArgumentParser(description="SPECTRA-SHIELD logger")
    ap.add_argument("--db", type=Path, default=DEFAULT_DB)
    ap.add_argument("--init", action="store_true", help="create the database")
    ap.add_argument("--port", help="serial port, e.g. /dev/ttyUSB0")
    ap.add_argument("--baud", type=int, default=115200)
    ap.add_argument("--run-label", default=f"run-{int(time.time())}")
    ap.add_argument("--atten-db", type=float, default=None,
                    help="interferer path attenuator setting in dB")
    ap.add_argument("--mode", default=None, help="cw|noise|off")
    ap.add_argument("--freq-mhz", type=float, default=None)
    ap.add_argument("--csv", type=Path, default=None, help="CSV mirror path")
    args = ap.parse_args()

    if args.init:
        init_db(args.db)
        return 0

    if not args.port:
        ap.error("--port is required unless --init is used")
    log_serial(args.port, args.baud, args.db, args.run_label, args.atten_db,
               args.mode, args.freq_mhz, args.csv)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
