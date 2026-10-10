#!/usr/bin/env python3
"""SPECTRA-SHIELD bench simulator (software twin of the conducted rig).

This is NOT a replacement for the hardware bench. It is a simplified
link-budget + logistic-PER model of the friendly LoRa link, a same-channel
interferer and the CMSA frame verification chain (CRC -> HMAC -> replay guard).
It writes to the SAME SQLite schema as host/logger/logger.py, so the real
logger, per_plot.py and the dashboard run on simulated data unchanged.

Model (all powers dBm, conducted):
    S      = P_TX - A_FIXED            friendly signal at the receiver
    J      = P_INT - A_INT             interferer at the receiver
    J/S    = J - S                     jammer-to-signal ratio
    SINR   = 10*log10( 10^(S/10) / (10^(N/10) + 10^(J/10)) )
    RSSI   = 10*log10( 10^(S/10) + 10^(J/10) + 10^(N/10) )
    P(ok)  = 1 / (1 + exp(SLOPE*(THRESH - SINR)))   logistic decode prob.

If SINR is comfortably above the SF9 threshold, PER ~ 0; as the interferer
rises the signal-to-interference ratio falls and PER climbs toward 1.

Usage:
    python3 spectra_sim.py --db ../logger/spectra.db --sweep
    python3 spectra_sim.py --db ../logger/spectra.db --emit-csv sim.csv
    python3 spectra_sim.py --selftest
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import hmac
import math
import random
import sys
from pathlib import Path

# Reuse the logger's schema + helpers so the pipeline is exercised end to end.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "logger"))
import logger  # noqa: E402

# --- physical model constants (mirror lib/spectra_common/include/spectra/config.h)
P_TX_DBM = 2.0          # kTxPowerDbm
P_INT_DBM = 10.0        # interferer output power at the combiner
A_FIXED_DB = 90.0       # friendly-path fixed attenuation (bench baseline)
N_DBM = -120.0          # noise floor, ~ -120 dBm in 125 kHz
SNR_THRESH_DB = -6.0    # SF9 demodulation threshold
SNR_SLOPE = 0.70
PAYLOAD_LEN = 17        # packed Telemetry struct: 4 floats + 1 byte

# Frame layout constants (mirror frame.h)
K_HEADER_LEN = 12
K_CRC_LEN = 2
K_MAC_LEN = 16
K_OVERHEAD = K_HEADER_LEN + K_CRC_LEN + K_MAC_LEN


def dev_psk() -> bytes:
    """Same DEV placeholder key as config.h load_psk() fallback."""
    return bytes((0xA5 ^ i) & 0xFF for i in range(32))


def crc16_ccitt(data: bytes) -> int:
    """CRC-16/CCITT-FALSE, bit-for-bit identical to frame.cpp."""
    crc = 0xFFFF
    for byte in data:
        crc ^= (byte << 8) & 0xFFFF
        for _ in range(8):
            if crc & 0x8000:
                crc = ((crc << 1) ^ 0x1021) & 0xFFFF
            else:
                crc = (crc << 1) & 0xFFFF
    return crc


def frame_encode(dev_id: int, seq: int, ts: int, payload: bytes, key: bytes) -> bytes:
    """version|dev|seq(4)|ts(4)|plen(2)|payload|crc(2)|mac(16), big-endian header."""
    header = bytes([1, dev_id]) + seq.to_bytes(4, "big") + ts.to_bytes(4, "big") \
        + len(payload).to_bytes(2, "big")
    body = header + payload
    crc = crc16_ccitt(body).to_bytes(2, "big")
    mac = hmac.new(key, body + crc, hashlib.sha256).digest()[:K_MAC_LEN]
    return body + crc + mac


def frame_decode(frame: bytes, key: bytes) -> tuple[str, int, int, int]:
    """Mirror frame.cpp verification order; returns (status, seq, ts, plen)."""
    if len(frame) < K_OVERHEAD:
        return "TOO_SHORT", 0, 0, 0
    version = frame[0]
    dev_id = frame[1]
    seq = int.from_bytes(frame[2:6], "big")
    ts = int.from_bytes(frame[6:10], "big")
    plen = int.from_bytes(frame[10:12], "big")
    if version != 1:
        return "BAD_VERSION", seq, ts, plen
    total = K_OVERHEAD + plen
    if len(frame) < total:
        return "TOO_SHORT", seq, ts, plen
    expected_crc = int.from_bytes(frame[K_HEADER_LEN + plen:K_HEADER_LEN + plen + 2], "big")
    actual_crc = crc16_ccitt(frame[:K_HEADER_LEN + plen])
    if expected_crc != actual_crc:
        return "BAD_CRC", seq, ts, plen
    mac = hmac.new(key, frame[:K_HEADER_LEN + plen + K_CRC_LEN], hashlib.sha256).digest()
    if not hmac.compare_digest(mac[:K_MAC_LEN], frame[K_HEADER_LEN + plen + K_CRC_LEN:total]):
        return "BAD_MAC", seq, ts, plen
    return "OK", seq, ts, plen


class ReplayGuard:
    """Mirror auth.h: monotonic seq + timestamp window."""

    def __init__(self) -> None:
        self.last_seq = 0
        self.have_last = False

    def accept(self, seq: int, ts: int, now: int,
               window: int = 300, skew: int = 30) -> bool:
        if seq == 0:
            return False
        if self.have_last and seq <= self.last_seq:
            return False
        if ts + window < now:
            return False
        if ts > now + skew:
            return False
        self.last_seq = seq
        self.have_last = True
        return True


def _js_to_powers(js_db: float) -> tuple[float, float]:
    s_dbm = P_TX_DBM - A_FIXED_DB
    j_dbm = s_dbm + js_db
    return s_dbm, j_dbm


def snr_for(js_db: float) -> float:
    s_dbm, j_dbm = _js_to_powers(js_db)
    sinr_lin = 10 ** (s_dbm / 10) / (10 ** (N_DBM / 10) + 10 ** (j_dbm / 10))
    return 10 * math.log10(sinr_lin)


def rssi_for(js_db: float, rng: random.Random) -> float:
    s_dbm, j_dbm = _js_to_powers(js_db)
    lin = 10 ** (s_dbm / 10) + 10 ** (j_dbm / 10) + 10 ** (N_DBM / 10)
    return 10 * math.log10(lin) + rng.gauss(0, 0.4)


def p_ok(js_db: float) -> float:
    snr = snr_for(js_db)
    return 1.0 / (1.0 + math.exp(SNR_SLOPE * (SNR_THRESH_DB - snr)))


def attenuator_for_js(js_db: float) -> float:
    """Interferer-path attenuator that realises a target J/S on the bench."""
    s_dbm = P_TX_DBM - A_FIXED_DB
    return P_INT_DBM - s_dbm - js_db


def simulate_packets(js_db: float, n_tx: int, rng: random.Random,
                     replay_every: int = 0) -> list[dict]:
    """One run: return received-packet rows (lost frames produce no row)."""
    key = dev_psk()
    ok_prob = p_ok(js_db)
    rows: list[dict] = []
    t_ms = 0
    seen_ok: list[tuple[int, int]] = []
    for seq in range(1, n_tx + 1):
        t_ms += rng.randint(950, 1050)
        snr = snr_for(js_db) + rng.gauss(0, 0.3)
        rssi = rssi_for(js_db, rng)
        r = rng.random()
        if r < ok_prob:
            rows.append({"device_ms": t_ms, "seq": seq, "status": "OK",
                         "rssi": round(rssi, 1), "snr": round(snr, 1),
                         "payload_len": PAYLOAD_LEN})
            seen_ok.append((seq, t_ms))
        else:
            u = rng.random()
            if u < 0.60:
                continue  # frame lost: nothing logged, seq gap -> counts as error
            if u < 0.90:
                status = "BAD_CRC"
            elif u < 0.98:
                status = "BAD_MAC"
            else:
                status = "TOO_SHORT"
            rows.append({"device_ms": t_ms, "seq": seq, "status": status,
                         "rssi": round(rssi, 1), "snr": round(snr, 1),
                         "payload_len": PAYLOAD_LEN if status != "TOO_SHORT" else 0})
        if replay_every and seq % replay_every == 0 and seen_ok:
            rseq, _ = seen_ok[-1]
            rows.append({"device_ms": t_ms + 5, "seq": rseq, "status": "REPLAY",
                         "rssi": round(rssi, 1), "snr": round(snr, 1),
                         "payload_len": PAYLOAD_LEN})
    return rows


def insert_run(conn, label: str, atten_db: float | None, mode: str | None,
               freq: float | None, rows: list[dict]) -> int:
    run_id = logger.start_run(conn, label, atten_db, mode, freq)
    conn.executemany(
        "INSERT INTO packets(run_id, device_ms, seq, status, rssi, snr, payload_len)"
        " VALUES (?,?,?,?,?,?,?)",
        [(run_id, r["device_ms"], r["seq"], r["status"], r["rssi"], r["snr"],
          r["payload_len"]) for r in rows],
    )
    conn.commit()
    return run_id


def build_scenario(conn, packets: int, rng: random.Random,
                   with_sweep: bool, with_replay: bool) -> None:
    # 1) Baseline: interferer off, best-case J/S.
    base_js = -12.0
    insert_run(conn, "baseline (interferer off)",
               round(attenuator_for_js(base_js), 1), "off", 866.5,
               simulate_packets(base_js, packets, rng))

    # 2) J/S sweep with the interferer keyed.
    if with_sweep:
        for i, js in enumerate([-8, -4, 0, 2, 4, 6, 8, 10, 12, 16, 20, 24]):
            mode = "cw" if i % 2 == 0 else "noise"
            insert_run(conn, f"sweep J/S={js:+d} dB ({mode})",
                       round(attenuator_for_js(js), 1), mode, 866.5,
                       simulate_packets(js, packets, rng))

    # 3) Replay-attack run: valid frames, duplicated seqs -> guard rejects.
    if with_replay:
        insert_run(conn, "replay attack (duplicated seq)",
                   round(attenuator_for_js(6.0), 1), "cw", 866.5,
                   simulate_packets(6.0, packets, rng, replay_every=4))


def emit_csv(rows_by_run: list[tuple[str, list[dict]]], path: Path) -> None:
    """Emit ground-node style CSV lines and validate them through logger.parse_line."""
    accepted = 0
    with open(path, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["run", "device_ms", "seq", "status", "rssi", "snr",
                    "payload_len"])
        for label, rows in rows_by_run:
            for r in rows:
                line = (f"RX,{r['device_ms']},{r['seq']},{r['status']},"
                        f"{r['rssi']},{r['snr']},{r['payload_len']}")
                parsed = logger.parse_line(line)  # prove the logger parser accepts it
                if parsed is not None:
                    accepted += 1
                w.writerow([label, r["device_ms"], r["seq"], r["status"],
                            r["rssi"], r["snr"], r["payload_len"]])
    print(f"wrote {path} ({accepted} lines accepted by logger.parse_line)")


def selftest() -> int:
    """Round-trip the frame codec and the replay guard; print PASS/FAIL."""
    ok = True
    key = dev_psk()
    frame = frame_encode(1, 42, 1000, b"hello-telemetry", key)
    st, seq, ts, plen = frame_decode(frame, key)
    checks = [("encode/decode OK", st == "OK" and seq == 42 and ts == 1000
               and plen == len("hello-telemetry"))]
    checks.append(("tampered CRC -> BAD_CRC",
                   frame_decode(frame[:13] + bytes([frame[13] ^ 0xFF])
                                + frame[14:], key)[0] == "BAD_CRC"))
    bad_mac = frame[:-1] + bytes([frame[-1] ^ 0xFF])
    checks.append(("tampered MAC -> BAD_MAC",
                   frame_decode(bad_mac, key)[0] == "BAD_MAC"))
    checks.append(("short frame -> TOO_SHORT",
                   frame_decode(frame[:8], key)[0] == "TOO_SHORT"))
    g = ReplayGuard()
    checks.append(("guard accepts seq 1", g.accept(1, 100, 100) is True))
    checks.append(("guard rejects replay of seq 1", g.accept(1, 100, 101) is False))
    checks.append(("guard rejects stale timestamp", g.accept(2, 100, 1000) is False))
    print("--- frame codec + replay guard self-test ---")
    for name, passed in checks:
        print(f"  [{'PASS' if passed else 'FAIL'}] {name}")
        ok = ok and passed
    print("--- physical model sanity ---")
    for js in (-8, 6, 12, 24):
        print(f"  J/S={js:+3d} dB  SINR={snr_for(js):+6.1f} dB  "
              f"PER~{(1 - p_ok(js)) * 100:5.1f}%  "
              f"atten={attenuator_for_js(js):6.1f} dB")
    return 0 if ok else 1


def main() -> int:
    ap = argparse.ArgumentParser(description="SPECTRA-SHIELD bench simulator")
    ap.add_argument("--db", type=Path, default=logger.DEFAULT_DB)
    ap.add_argument("--packets", type=int, default=250, help="tx per run")
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--sweep", action="store_true", help="add the J/S sweep runs")
    ap.add_argument("--replay", action="store_true", help="add a replay-attack run")
    ap.add_argument("--emit-csv", type=Path, default=None)
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()

    if args.selftest:
        return selftest()

    rng = random.Random(args.seed)
    conn = logger.connect(args.db)
    try:
        conn.executescript(logger.SCHEMA)
        build_scenario(conn, args.packets, rng, args.sweep, args.replay)
        n_runs = conn.execute("SELECT COUNT(*) FROM runs").fetchone()[0]
        n_pkts = conn.execute("SELECT COUNT(*) FROM packets").fetchone()[0]
    finally:
        conn.close()
    print(f"simulated {n_runs} runs / {n_pkts} packet rows -> {args.db}")

    if args.emit_csv:
        rng2 = random.Random(args.seed)
        sample = [("baseline", simulate_packets(-12, 40, rng2)),
                  ("J/S=+6", simulate_packets(6, 40, rng2)),
                  ("replay", simulate_packets(6, 40, rng2, replay_every=4))]
        emit_csv(sample, args.emit_csv)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
