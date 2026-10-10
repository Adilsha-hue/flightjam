// SPDX-License-Identifier: MIT
//
// uav_node - friendly LoRa transmitter (SX1262, 865-868 MHz).
//
// Builds a signed telemetry frame and transmits it at a duty-cycle-compliant
// rate. Payload is a packed struct in this scaffold; replace with CBOR/MsgPack
// if you need cross-architecture portability.
//
#include <Arduino.h>
#include <RadioLib.h>
#include <SPI.h>

#include "spectra/config.h"
#include "spectra/frame.h"

using namespace spectra;

SX1262 radio = new Module(PIN_LORA_NSS, PIN_LORA_DIO1,
                          PIN_LORA_RST, PIN_LORA_BUSY);

static uint8_t  g_key[kPskLen];
static uint32_t g_seq = 0;

// Identical struct on both ends; same-arch, so native byte order is fine here.
struct __attribute__((packed)) Telemetry {
  float   lat;
  float   lon;
  float   alt_m;
  float   batt_v;
  uint8_t sats;
};

// Airtime pacing: keep the 865-868 MHz duty cycle under 1%.
void paceToDutyCycle(size_t airtime_ms, float max_duty) {
  const uint32_t min_period = (uint32_t)(airtime_ms / max_duty);
  static uint32_t last_tx = 0;
  const uint32_t now = millis();
  if (last_tx != 0 && now - last_tx < min_period) {
    delay(min_period - (now - last_tx));
  }
  last_tx = millis();
}

void setup() {
  Serial.begin(115200);
  delay(300);

  load_psk(g_key);

  SPI.begin(PIN_LORA_SCK, PIN_LORA_MISO, PIN_LORA_MOSI, PIN_LORA_NSS);
  const int state = radio.begin(kFreqMHz, kBandwidthKHz, kSpreadingFactor,
                                kCodingRate, kSyncWord, kTxPowerDbm);
  if (state != RADIOLIB_ERR_NONE) {
    Serial.printf("radio.begin failed: %d\n", state);
    while (true) delay(1000);
  }
  Serial.println("uav_node ready");
}

void loop() {
  Telemetry t;
  t.lat    = 28.6139f + (float)random(-50, 50) / 100000.0f;
  t.lon    = 77.2090f + (float)random(-50, 50) / 100000.0f;
  t.alt_m  = 120.0f + (float)random(0, 200);
  t.batt_v = 11.8f;
  t.sats   = 9;

  FrameHeader h;
  h.version     = kFrameVersion;
  h.dev_id      = 1;                 // UAV device id
  h.seq         = ++g_seq;
  h.timestamp   = millis() / 1000;   // seconds since boot (see ground node note)
  h.payload_len = sizeof(Telemetry);

  uint8_t frame[sizeof(Telemetry) + kOverhead];
  const size_t n = frame_encode(h, (const uint8_t*)&t, g_key, kPskLen,
                                frame, sizeof(frame));
  if (n == 0) {
    Serial.println("encode failed");
    delay(1000);
    return;
  }

  const int state = radio.transmit(frame, n);
  if (state != RADIOLIB_ERR_NONE) {
    Serial.printf("tx failed: %d\n", state);
  } else {
    Serial.printf("tx seq=%lu len=%u\n", (unsigned long)h.seq, (unsigned)n);
  }

  paceToDutyCycle(radio.getTimeOnAir(n) / 1000, 0.01f);
}
