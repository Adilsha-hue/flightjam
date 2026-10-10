// SPDX-License-Identifier: MIT
//
// interferer - Tier-1 conducted interferer on a CC1101 (865-868 MHz).
//
// Generates either a continuous carrier (CW) or same-channel noise. Serial
// commands (one per line, 115200 baud):
//
//   cw            - unmodulated carrier
//   noise         - repeated random payloads at the configured channel
//   off           - radio to standby
//   freq <MHz>    - retune (stay inside 865-868 MHz)
//   power <dBm>   - set output power
//
// Everything runs into the conducted harness (combiner + attenuators). Never
// attach an antenna to this node.
//
#include <Arduino.h>
#include <RadioLib.h>
#include <SPI.h>

#include "spectra/config.h"

using namespace spectra;

CC1101 radio = new Module(PIN_CC_CS, PIN_CC_GDO0, PIN_CC_RST, RADIOLIB_NC);

enum class Mode { Off, Cw, Noise };
static Mode g_mode = Mode::Off;
static float g_freq = kFreqMHz;

void applyMode() {
  switch (g_mode) {
    case Mode::Off:
      radio.standby();
      Serial.println("mode=off");
      break;
    case Mode::Cw:
      // Unmodulated carrier. RadioLib exposes transmitDirect() on modules that
      // support raw TX; verify availability for your CC1101 build.
      radio.transmitDirect();
      Serial.println("mode=cw");
      break;
    case Mode::Noise:
      Serial.println("mode=noise");
      break;
  }
}

void setup() {
  Serial.begin(115200);
  delay(300);

  SPI.begin(PIN_CC_SCK, PIN_CC_MISO, PIN_CC_MOSI, PIN_CC_CS);
  // freq, bitrate(kbps), freqDev(kHz), rxBw(kHz), power(dBm), preamble(bits)
  const int state = radio.begin(g_freq, 4.8, 5.0, 135.0, 10, 16);
  if (state != RADIOLIB_ERR_NONE) {
    Serial.printf("cc1101 begin failed: %d\n", state);
    while (true) delay(1000);
  }
  Serial.println("interferer ready");
  applyMode();
}

void handleCommand(String line) {
  line.trim();
  if (line == "cw") {
    g_mode = Mode::Cw;
  } else if (line == "noise") {
    g_mode = Mode::Noise;
  } else if (line == "off") {
    g_mode = Mode::Off;
  } else if (line.startsWith("freq ")) {
    const float f = line.substring(5).toFloat();
    if (f >= 865.0f && f <= 868.0f) {
      g_freq = f;
      radio.setFrequency(g_freq);
    } else {
      Serial.println("freq out of range (865-868 MHz)");
    }
  } else if (line.startsWith("power ")) {
    radio.setOutputPower(line.substring(6).toFloat());
  } else if (line.length() > 0) {
    Serial.println("unknown command");
    return;
  }
  applyMode();
}

void loop() {
  if (Serial.available()) {
    handleCommand(Serial.readStringUntil('\n'));
  }

  if (g_mode == Mode::Noise) {
    uint8_t noise[32];
    for (size_t i = 0; i < sizeof(noise); ++i) noise[i] = (uint8_t)random(256);
    radio.transmit(noise, sizeof(noise));
  }
}
