#!/usr/bin/env python3
"""Build docs/SPECTRA-SHIELD-V1-proposal.pdf from the proposal content.

Requires only fpdf2 (installed) and DejaVu fonts (system). Run:
    python3 docs/build_pdf.py
"""
from __future__ import annotations

import os
from fpdf import FPDF

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "SPECTRA-SHIELD-V1-proposal.pdf")

FONT_DIR = "/usr/share/fonts/truetype/dejavu"
SANS = os.path.join(FONT_DIR, "DejaVuSans.ttf")
SANS_B = os.path.join(FONT_DIR, "DejaVuSans-Bold.ttf")
MONO = os.path.join(FONT_DIR, "DejaVuSansMono.ttf")

ACCENT = (15, 76, 129)
GREY = (90, 90, 90)


class PDF(FPDF):
    def header(self):
        if self.page_no() == 1:
            return
        self.set_font("DejaVu", "", 8)
        self.set_text_color(*GREY)
        self.cell(0, 6, "SPECTRA-SHIELD V1 - Improved Proposal", align="L")
        self.cell(0, 6, f"Page {self.page_no()}", align="R")
        self.ln(8)
        self.set_text_color(0, 0, 0)

    def footer(self):
        self.set_y(-12)
        self.set_font("DejaVu", "", 7)
        self.set_text_color(*GREY)
        self.cell(0, 6, "Conducted-only RF lab prototype - 865-868 MHz license-exempt (India)", align="C")
        self.set_text_color(0, 0, 0)


def h1(pdf, text):
    pdf.set_font("DejaVu", "B", 20)
    pdf.set_text_color(*ACCENT)
    pdf.multi_cell(0, 9, text, new_x="LMARGIN", new_y="NEXT")
    pdf.set_text_color(0, 0, 0)
    pdf.ln(2)


def h2(pdf, text):
    pdf.ln(2)
    pdf.set_font("DejaVu", "B", 13)
    pdf.set_text_color(*ACCENT)
    pdf.multi_cell(0, 7, text, new_x="LMARGIN", new_y="NEXT")
    pdf.set_text_color(0, 0, 0)
    pdf.ln(1)


def para(pdf, text):
    pdf.set_font("DejaVu", "", 10)
    pdf.multi_cell(0, 5.2, text, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(1.5)


def bullet(pdf, text):
    pdf.set_font("DejaVu", "", 10)
    x = pdf.l_margin
    pdf.set_x(x + 5)
    pdf.multi_cell(0, 5.2, "-  " + text, new_x="LMARGIN", new_y="NEXT")
    pdf.set_x(x)
    pdf.ln(0.5)


def kv_bullet(pdf, key, text):
    pdf.set_font("DejaVu", "", 10)
    pdf.set_x(pdf.l_margin + 5)
    pdf.set_font("DejaVu", "B", 10)
    pdf.write(5.2, key + ": ")
    pdf.set_font("DejaVu", "", 10)
    pdf.multi_cell(0, 5.2, text, new_x="LMARGIN", new_y="NEXT")
    pdf.set_x(pdf.l_margin)


def table(pdf, headers, rows, widths, total_row=False):
    pdf.set_font("DejaVu", "B", 9)
    pdf.set_fill_color(230, 236, 245)
    for head, w in zip(headers, widths):
        pdf.cell(w, 7, head, border=1, align="L", fill=True)
    pdf.ln()
    pdf.set_font("DejaVu", "", 9)
    for i, row in enumerate(rows):
        last = total_row and i == len(rows) - 1
        if last:
            pdf.set_font("DejaVu", "B", 9)
            pdf.set_fill_color(245, 245, 245)
        for cell, w, head in zip(row, widths, headers):
            align = "L" if head == "Item" or head == "Week" or head == "Work" else "R"
            pdf.cell(w, 6.4, cell, border=1, align=align, fill=last)
        pdf.ln()
    pdf.ln(2)


def build():
    pdf = PDF(format="A4")
    pdf.add_font("DejaVu", "", SANS)
    pdf.add_font("DejaVu", "B", SANS_B)
    pdf.add_font("DejaVuMono", "", MONO)
    pdf.set_auto_page_break(auto=True, margin=16)
    pdf.set_margins(16, 16, 16)
    pdf.add_page()

    # ---- Title block ----
    pdf.set_font("DejaVu", "B", 26)
    pdf.set_text_color(*ACCENT)
    pdf.multi_cell(0, 12, "SPECTRA-SHIELD V1", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("DejaVu", "", 13)
    pdf.set_text_color(0, 0, 0)
    pdf.multi_cell(0, 7, "Improved Proposal - Selective RF Interference Evaluation and a Protected, Authenticated UAV Telemetry Link", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)
    pdf.set_draw_color(*ACCENT)
    pdf.set_line_width(0.6)
    y = pdf.get_y()
    pdf.line(16, y, 194, y)
    pdf.ln(6)

    pdf.set_font("DejaVu", "", 10)
    for k, v in [
        ("Team", "4 engineers"),
        ("Duration", "6-8 weeks"),
        ("Budget", "INR 45,000-80,000 target; this plan uses ~INR 29,100"),
        ("Setting", "Indoor RF lab, conducted (cabled) prototype only"),
        ("Interference tier", "Tier 1 only"),
        ("Friendly link", "865-868 MHz LoRa (SX1262 / SX1276, CSS)"),
        ("Deliverables", "Improved proposal document + code scaffolding"),
    ]:
        kv_bullet(pdf, k, v)
    pdf.ln(2)

    # ---- 1. Locked design ----
    h2(pdf, "1. Locked design")
    bullet(pdf, "Friendly link: LoRa SX1262 on ESP32-S3 (Heltec WiFi LoRa 32 V4), CSS, 865-868 MHz India license-exempt (25 mW e.r.p., 1% duty).")
    bullet(pdf, "Interferer (Tier 1): CC1101 868 MHz module on an ESP32, emitting OOK/FSK CW plus same-channel noise on the LoRa channel.")
    bullet(pdf, "Harness: all-cabled / conducted - friendly TX -> fixed att -> 2-way combiner -> friendly RX, and interferer -> step att -> same combiner.")
    bullet(pdf, "Monitoring: RTL-SDR Blog V4 to independently confirm interferer frequency/level and containment (no open-air radiation).")
    bullet(pdf, "Tier 2 (HackRF One) and Tier 3 (ADALM-PLUTO) dropped from the default plan as too costly; kept as optional upgrade notes.")

    # ---- 2. BOM ----
    h2(pdf, "2. Bill of materials (verified India prices, 2026)")
    table(
        pdf,
        ["Item", "Qty", "Unit INR", "Total INR"],
        [
            ["Heltec WiFi LoRa 32 V4 (ESP32-S3 + SX1262)", "2", "3549", "7098"],
            ["CC1101 868 MHz module (interferer)", "2", "250", "500"],
            ["SMA step attenuator 0-10 dB (1 dB step)", "1", "2500", "2500"],
            ["Fixed SMA attenuators (6/10/20 dB set)", "~4", "1500", "6000"],
            ["2-way power combiner / divider", "1", "2000", "2000"],
            ["SMA cables / adapters / pigtails", "-", "-", "1500"],
            ["RTL-SDR Blog V4 (monitor / verify)", "1", "6028", "6028"],
            ["Breadboard / PSU / enclosure / mounts", "-", "-", "2000"],
            ["Consumables / misc", "-", "-", "1500"],
            ["TOTAL", "", "", "29100"],
        ],
        [88, 14, 24, 24],
        total_row=True,
    )
    para(pdf, "Budget remaining vs the INR 45,000 floor: ~INR 16,000 (spare radios, second interferer, or report printing). Vendors referenced: zbotic.in, Robu.in, compoindia, Synergy Telecom / Dipeshwari.")

    pdf.add_page()
    # ---- 3. Test methodology ----
    h2(pdf, "3. Test methodology (conducted)")
    bullet(pdf, "Calibrate the harness: measure path loss per attenuator setting using the RTL-SDR and SX1262 RSSI.")
    bullet(pdf, "Sweep J/S via the step attenuator in 1 dB steps; per point record PER, RSSI, SNR, p95 latency, jitter, and auth accept/reject.")
    bullet(pdf, "Headline metric: J/S at 10% PER, plus a full PER-vs-J/S curve.")
    bullet(pdf, "Demonstrate LoRa resilience against an un-coded baseline (optional: CC1101 link as the fragile comparison).")

    # ---- 4. Firmware + auth ----
    h2(pdf, "4. Firmware + authentication design")
    bullet(pdf, "Frame: hdr | dev_id | seq | timestamp | payload | CRC16 | HMAC-SHA256 (truncated 16 B). Verify CRC before HMAC.")
    bullet(pdf, "Replay defense: monotonic counter + timestamp window; optional ground-nonce challenge-response.")
    bullet(pdf, "Crypto: ESP32-S3 hardware AES (~7.3 MB/s) and SHA-256 (~26 MB/s); mbedTLS with CONFIG_MBEDTLS_HARDWARE_AES/SHA, or the ESP-IDF HMAC peripheral with an eFuse-burned key (one-shot, fine for small frames).")
    bullet(pdf, "Payload: CBOR/MsgPack to minimize airtime (duty-cycle compliance).")
    bullet(pdf, "Provisioning: per-device keys via build-time secrets, never hardcoded in source.")

    # ---- 5. Software ----
    h2(pdf, "5. Software")
    bullet(pdf, "Logging: SQLite + CSV.")
    bullet(pdf, "Dashboard: Streamlit (PER/J/S plot, RSSI/SNR, latency histogram, auth counters).")
    bullet(pdf, "Analysis: Python / Matplotlib for report figures.")

    # ---- 6. Repo layout ----
    h2(pdf, "6. Repository layout")
    pdf.set_font("DejaVuMono", "", 8.5)
    for line in [
        "docs/       01-proposal 02-architecture 03-test-methodology 04-bom 05-safety-legal",
        "firmware/   common/ (frame, auth, cbor)  uav_node/  ground_node/  interferer/",
        "host/       logger/ (sqlite, csv)  analysis/ (PER plots)  dashboard/ (streamlit)",
        "hardware/   conducted_setup  calibration",
        "README.md   platformio.ini   requirements.txt",
    ]:
        pdf.multi_cell(0, 4.6, line, new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("DejaVu", "", 10)
    pdf.ln(1)
    para(pdf, "Firmware target: PlatformIO + Arduino core + RadioLib (SX1262). ESP-IDF noted as an option for the hardware-HMAC path.")

    # ---- 7. Schedule ----
    h2(pdf, "7. Schedule (6-8 weeks, 4 engineers)")
    table(
        pdf,
        ["Week", "Work"],
        [
            ["W1", "Order BOM; bench + harness calibration"],
            ["W2", "Friendly link bring-up; frame format"],
            ["W3", "Auth: HMAC, counter/replay; provisioning + replay-attack demo"],
            ["W4", "Interferer (CC1101 CW / same-channel); full conducted chain"],
            ["W5", "J/S sweep runs; data capture"],
            ["W6", "Dashboard + analysis + figures"],
            ["W7", "Repeatability, edge cases, report draft"],
            ["W8", "Buffer, demo, presentation"],
        ],
        [20, 130],
    )
    para(pdf, "Team split: 2x firmware, 1x RF/test, 1x software/analysis.")

    # ---- 8. Safety & legal ----
    h2(pdf, "8. Safety & legal")
    bullet(pdf, "Conducted-only; verify no radiation with the RTL-SDR outside the rig.")
    bullet(pdf, "Operate only in 865-868 MHz and 2.4 GHz ISM license-exempt bands. Never GPS or cellular bands.")
    bullet(pdf, "Low EIRP behind attenuators; interference research limited to a closed, cabled setup.")
    bullet(pdf, "India WPC rule: 'Use of Low Power Equipment in the Frequency Band 865-868 MHz for Short Range Devices (Exemption from Licence) Rules, 2021', G.S.R. 853(E), 10 Dec 2021 (865-868 MHz, 25 mW e.r.p., 1% duty cycle).")

    # ---- 9. Risks ----
    h2(pdf, "9. Open risks")
    bullet(pdf, "CC1101 sometimes out of stock -> fallback: a second LoRa module as interferer.")
    bullet(pdf, "Fixed attenuators have MOQ 5-10 -> buy a small set from one vendor, or lean on the step attenuator + one 20 dB pad.")
    bullet(pdf, "ESP32-S3 hardware HMAC is one-shot (no streaming) -> fine for our small frames.")

    pdf.output(OUT)
    print("wrote", OUT)


if __name__ == "__main__":
    build()
