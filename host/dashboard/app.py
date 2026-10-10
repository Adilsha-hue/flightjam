#!/usr/bin/env python3
"""SPECTRA-SHIELD Streamlit dashboard.

Live/at-rest view of the logger database: run summary, PER vs J/S, RSSI/SNR,
and authentication counters (bad CRC/MAC, replays).

Run:
    streamlit run host/dashboard/app.py
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

import pandas as pd
import streamlit as st

DEFAULT_DB = Path(__file__).resolve().parents[1] / "logger" / "spectra.db"
BAD_STATUSES = ("BAD_CRC", "BAD_MAC", "BAD_VERSION", "TOO_SHORT")

st.set_page_config(page_title="SPECTRA-SHIELD", layout="wide")
st.title("SPECTRA-SHIELD dashboard")
st.caption("Conducted 865-868 MHz link under selective interference")


@st.cache_data(ttl=5)
def load(db_path: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    conn = sqlite3.connect(db_path)
    try:
        runs = pd.read_sql_query("SELECT * FROM runs ORDER BY id", conn)
        packets = pd.read_sql_query("SELECT * FROM packets", conn)
    finally:
        conn.close()
    return runs, packets


db_path = st.sidebar.text_input("Database", str(DEFAULT_DB))
if not Path(db_path).exists():
    st.warning(f"No database at {db_path}. Run `python3 host/logger/logger.py --init`.")
    st.stop()

runs, packets = load(db_path)
if runs.empty:
    st.info("Database is empty. Log a run first.")
    st.stop()

label_to_id = {f"#{r.id}  {r.label}": int(r.id) for r in runs.itertuples()}
choice = st.sidebar.selectbox("Run", list(label_to_id))
run_id = label_to_id[choice]
run = runs[runs["id"] == run_id].iloc[0]
pkts = packets[packets["run_id"] == run_id]

seq = pkts[pkts["status"].isin(("OK", "REPLAY", "BAD_CRC", "BAD_MAC",
                                "BAD_VERSION"))]
expected = int(seq["seq"].max() - seq["seq"].min() + 1) if not seq.empty else len(pkts)
ok = int((pkts["status"] == "OK")["seq"].nunique())
bad = int(pkts["status"].isin(BAD_STATUSES).sum())
replay = int((pkts["status"] == "REPLAY").sum())
per = 0.0 if expected == 0 else max(0.0, 1 - ok / expected)

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Expected", expected)
c2.metric("Received OK", ok)
c3.metric("PER", f"{per * 100:.1f}%")
c4.metric("Bad (CRC/MAC/ver/len)", bad)
c5.metric("Replays blocked", replay)

meta = []
for k in ("attenuator_db", "interferer_mode", "freq_mhz", "started_at"):
    if k in run and pd.notna(run[k]):
        meta.append(f"**{k}**: {run[k]}")
st.markdown(" · ".join(meta) if meta else "_no run metadata_")

left, right = st.columns(2)

with left:
    st.subheader("RSSI (dBm)")
    if not pkts.empty:
        st.line_chart(pkts[["device_ms", "rssi"]].set_index("device_ms"))
    else:
        st.write("no packets")

with right:
    st.subheader("SNR (dB)")
    if not pkts.empty:
        st.line_chart(pkts[["device_ms", "snr"]].set_index("device_ms"))
    else:
        st.write("no packets")

st.subheader("Status breakdown")
st.bar_chart(pkts["status"].value_counts())

st.subheader("All runs: PER by run")
rows = []
for r in runs.itertuples():
    p = packets[packets["run_id"] == r.id]
    sp = p[p["status"].isin(("OK", "REPLAY", "BAD_CRC", "BAD_MAC",
                             "BAD_VERSION"))]
    exp = int(sp["seq"].max() - sp["seq"].min() + 1) if not sp.empty else len(p)
    o = int((p["status"] == "OK")["seq"].nunique())
    rows.append({
        "run": r.id,
        "label": r.label,
        "atten_db": getattr(r, "attenuator_db", None),
        "mode": getattr(r, "interferer_mode", None),
        "expected": exp,
        "ok": o,
        "PER_%": 0.0 if exp == 0 else round(100 * max(0.0, 1 - o / exp), 2),
    })
st.dataframe(pd.DataFrame(rows), use_container_width=True)

with st.expander("Raw packets (latest 200)"):
    st.dataframe(pkts.tail(200), use_container_width=True)
