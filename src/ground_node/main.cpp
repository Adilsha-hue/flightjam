// SPDX-License-Identifier: MIT
//
// ground_node - friendly LoRa receiver (SX1262, 865-868 MHz).
//
// Receives frames, verifies CRC + HMAC + replay guard, and emits one CSV line
// per reception on the serial port for the host logger to collect:
//
//   RX,<millis>,<seq>,<status>,<rssi>,<snr>,<payload_hex>
//
// status is one of: OK TOO_SHORT BAD_VERSION BAD_CRC BAD_MAC REPLAY
//
#include <Arduino.h>
#include <RadioLib.h>
#include <SPI.h>

#include "spectra/auth.h"
#include "spectra/config.h"
#include "spectra/frame.h"

using namespace spectra;

SX1262 radio = new Module(PIN_LORA_NSS, PIN_LORA_DIO1,
                          PIN_LORA_RST, PIN_LORA_BUSY);

static uint8_t    g_key[kPskLen];
static ReplayGuard g_guard;
static uint32_t   g_rx = 0;
static uint32_t   g_bad = 0;

const char* statusName(FrameStatus s) {
  switch (s) {
    case FrameStatus::Ok:         return "OK";
    case FrameStatus::TooShort:   return "TOO_SHORT";
    case FrameStatus::BadVersion: return "BAD_VERSION";
    case FrameStatus::BadCrc:     return "BAD_CRC";
    case FrameStatus::BadMac:     return "BAD_MAC";
  }
  return "?";
}

void setup() {
  Serial.begin(115200);
  delay(300);

  load_psk(g_key);
  g_guard.reset();

  SPI.begin(PIN_LORA_SCK, PIN_LORA_MISO, PIN_LORA_MOSI, PIN_LORA_NSS);
  const int state = radio.begin(kFreqMHz, kBandwidthKHz, kSpreadingFactor,
                                kCodingRate, kSyncWord, kTxPowerDbm);
  if (state != RADIOLIB_ERR_NONE) {
    Serial.printf("radio.begin failed: %d\n", state);
    while (true) delay(1000);
  }
  Serial.println("ground_node ready");
}

void loop() {
  uint8_t buf[256];
  const int state = radio.receive(buf, sizeof(buf));
  if (state != RADIOLIB_ERR_NONE) return;

  const float rssi = radio.getRSSI();
  const float snr  = radio.getSNR();

  FrameHeader h;
  const uint8_t* payload = nullptr;
  FrameStatus st = frame_decode(buf, sizeof(buf), g_key, kPskLen, h, payload);

  // Replay guard applies only to otherwise-valid frames.
  if (st == FrameStatus::Ok) {
    const uint32_t now = millis() / 1000;
    if (!g_guard.accept(h.seq, h.timestamp, now)) {
      Serial.printf("RX,%lu,%lu,REPLAY,%.1f,%.1f,%u\n",
                    (unsigned long)millis(), (unsigned long)h.seq, rssi, snr,
                    (unsigned)h.payload_len);
      g_bad++;
      return;
    }
  }

  g_rx++;
  if (st != FrameStatus::Ok) g_bad++;

  Serial.printf("RX,%lu,%lu,%s,%.1f,%.1f,%u\n",
                (unsigned long)millis(), (unsigned long)h.seq, statusName(st),
                rssi, snr, (unsigned)h.payload_len);

  // NOTE: end-to-end latency needs a shared time base. Frames carry device
  // uptime seconds; for latency measurement, use a ground-sent beacon or a
  // GPS/PPS time source and correlate.
}
