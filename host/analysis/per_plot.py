#!/usr/bin/env python3
"""SPECTRA-SHIELD PER-vs-J/S analysis.

Reads the logger SQLite database, groups packets by run, computes the packet
error rate (PER) for each run, maps each run to a J/S ratio using the run's
interferer-path attenuator setting, and plots PER vs J/S.

J/S model (all in dB):
    J/S = (P_int - A_int) - (P_friendly - A_fixed)

where P_int / P_friendly are the node output powers and A_int is the run's
interferer-path attenuator (runs.attenuator_db). A_fixed is the friendly link's
fixed attenuator (the harness baseline, default 0). Diagnose the real values in
hardware/calibration.md and pass them here.

Usage:
    python3 per_plot.py --db spectra.db --out per_vs_js.png
    python3 per_plot.py --db spectra.db \
        --interferer-dbm 10 --friendly-dbm 2 --fixed-db 10
"""
from __future__ import annotations

import argparse
import sqlite3
from dataclasses import dataclass
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # headless
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

# Statuses that carry a trustworthy frame header (so seq is meaningful).
HDR_STATUSES = ("OK", "REPLAY", "BAD_CRC", "BAD_MAC", "BAD_VERSION")
BAD_STATUSES = ("BAD_CRC", "BAD_MAC", "BAD_VERSION", "TOO_SHORT")


@dataclass
class RunResult:
    run_id: int
    label: str
    mode: str | None
    atten_db: float | None
    j_over_s: float | None
    expected: int
    received: int
    ok: int
    bad: int
    replay: int
    per: float
    mean_rssi: float | None
    mean_snr: float | None


def load(db_path: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    conn = sqlite3.connect(db_path)
    try:
        runs = pd.read_sql_query("SELECT * FROM runs ORDER BY id", conn)
        packets = pd.read_sql_query("SELECT * FROM packets", conn)
    finally:
        conn.close()
    return runs, packets


def analyze_run(run: pd.Series, pkts: pd.DataFrame, p_int: float,
                p_friendly: float, a_fixed: float) -> RunResult | None:
    atten = run["attenuator_db"]
    js = None
    if atten is not None and not pd.isna(atten):
        js = (p_int - float(atten)) - (p_friendly - a_fixed)

    if pkts.empty:
        return None

    # Expected transmissions: span of sequence numbers in this run.
    seq_pkts = pkts[pkts["status"].isin(HDR_STATUSES)]
    if seq_pkts.empty:
        expected = len(pkts)
        ok = 0
    else:
        lo, hi = int(seq_pkts["seq"].min()), int(seq_pkts["seq"].max())
        expected = max(1, hi - lo + 1)
        ok = int(pkts[pkts["status"] == "OK"]["seq"].nunique())

    received = int(len(pkts))
    bad = int(pkts["status"].isin(BAD_STATUSES).sum())
    replay = int((pkts["status"] == "REPLAY").sum())
    per = 1.0 - (ok / expected) if expected else 0.0
    per = min(max(per, 0.0), 1.0)

    return RunResult(
        run_id=int(run["id"]),
        label=str(run["label"]),
        mode=run["interferer_mode"],
        atten_db=None if atten is None or pd.isna(atten) else float(atten),
        j_over_s=js,
        expected=expected,
        received=received,
        ok=ok,
        bad=bad,
        replay=replay,
        per=per,
        mean_rssi=float(pkts["rssi"].mean()) if "rssi" in pkts else None,
        mean_snr=float(pkts["snr"].mean()) if "snr" in pkts else None,
    )


def js_at_target(results: list[RunResult], target: float = 0.10) -> float | None:
    """Linear-interpolated J/S (dB) at a target PER, over the monotonic sweep."""
    pts = sorted([r for r in results if r.j_over_s is not None],
                 key=lambda r: r.j_over_s)
    for a, b in zip(pts, pts[1:]):
        if (a.per - target) * (b.per - target) <= 0 and a.per != b.per:
            t = (target - a.per) / (b.per - a.per)
            return a.j_over_s + t * (b.j_over_s - a.j_over_s)
    # Tail behaviour: already above target at the lowest J/S tested.
    if pts and pts[0].per >= target:
        return pts[0].j_over_s
    return None


def main() -> int:
    ap = argparse.ArgumentParser(description="PER vs J/S analysis")
    ap.add_argument("--db", type=Path, required=True)
    ap.add_argument("--out", type=Path, default=Path("per_vs_js.png"))
    ap.add_argument("--interferer-dbm", type=float, default=10.0,
                    help="interferer output power at the combiner (dBm)")
    ap.add_argument("--friendly-dbm", type=float, default=2.0,
                    help="friendly node output power (dBm)")
    ap.add_argument("--fixed-db", type=float, default=0.0,
                    help="fixed attenuator in the friendly path (dB)")
    ap.add_argument("--target", type=float, default=0.10,
                    help="PER target for the headline J/S number")
    ap.add_argument("--csv", type=Path, default=None,
                    help="write the per-run table to this CSV")
    args = ap.parse_args()

    if not args.db.exists():
        ap.error(f"database not found: {args.db} (run logger.py --init first)")

    runs, packets = load(args.db)
    if runs.empty:
        ap.error("no runs in database")

    results: list[RunResult] = []
    for _, run in runs.iterrows():
        pkts = packets[packets["run_id"] == run["id"]]
        r = analyze_run(run, pkts, args.interferer_dbm, args.friendly_dbm,
                        args.fixed_db)
        if r is not None:
            results.append(r)

    if not results:
        ap.error("no packet data to analyze")

    df = pd.DataFrame([vars(r) for r in results])
    if args.csv:
        df.to_csv(args.csv, index=False)
        print(f"wrote {args.csv}")

    print(df[["run_id", "label", "atten_db", "j_over_s", "expected", "ok",
              "per"]].to_string(index=False))

    j10 = js_at_target(results, args.target)
    if j10 is not None:
        print(f"\nJ/S at {args.target:.0%} PER: {j10:+.1f} dB")
    else:
        print(f"\nJ/S at {args.target:.0%} PER: not reached in this sweep")

    # --- plot ---
    sweep = [r for r in results if r.j_over_s is not None]
    fig, (ax_per, ax_rf) = plt.subplots(
        2, 1, figsize=(8, 8), sharex=True,
        gridspec_kw={"height_ratios": [2, 1]})

    if sweep:
        xs = [r.j_over_s for r in sweep]
        ys = [r.per * 100 for r in sweep]
        ax_per.plot(xs, ys, "o-", color="#c0392b", label="PER")
        if j10 is not None:
            ax_per.axhline(args.target * 100, color="gray", ls="--", lw=1)
            ax_per.axvline(j10, color="steelblue", ls=":", lw=1)
            ax_per.annotate(f"J/S@10% = {j10:+.1f} dB",
                            xy=(j10, args.target * 100),
                            xytext=(5, 15), textcoords="offset points",
                            color="steelblue")
        ax_per.set_ylabel("Packet error rate (%)")
        ax_per.set_title("SPECTRA-SHIELD: PER vs jammer-to-signal ratio")
        ax_per.grid(True, alpha=0.3)
        ax_per.legend(loc="lower right")

        rssi = [r.mean_rssi for r in sweep if r.mean_rssi is not None]
        if rssi:
            ax_rf.plot(xs, [r.mean_rssi for r in sweep], "s-",
                       color="#2c3e50", label="mean RSSI (dBm)")
        snr = [r.mean_snr for r in sweep if r.mean_snr is not None]
        if snr:
            ax_rf.plot(xs, [r.mean_snr for r in sweep], "^-",
                       color="#27ae60", label="mean SNR (dB)")
        ax_rf.set_xlabel("J/S (dB)")
        ax_rf.set_ylabel("RSSI / SNR")
        ax_rf.grid(True, alpha=0.3)
        ax_rf.legend(loc="upper right")
    else:
        ax_per.text(0.5, 0.5, "no J/S metadata (set --atten-db when logging)",
                    ha="center", va="center", transform=ax_per.transAxes)

    fig.tight_layout()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.out, dpi=150)
    print(f"wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
