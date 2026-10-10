#pragma once
//
// spectra/config.h - board pin maps, radio parameters and provisioning knobs.
//
// All values are scaffolding defaults. VERIFY the SPI pin map against your
// exact board revision before flashing.
//
#include <stdint.h>

namespace spectra {

// ---------------------------------------------------------------------------
// Radio parameters (friendly link)
// ---------------------------------------------------------------------------
constexpr float  kFreqMHz      = 866.5f;  // inside 865-868 MHz (India exempt)
constexpr float  kBandwidthKHz = 125.0f;
constexpr uint8_t kSpreadingFactor = 9;
constexpr uint8_t kCodingRate  = 5;       // 4/5
constexpr uint8_t kSyncWord    = 0x12;    // private
constexpr int8_t kTxPowerDbm   = 2;       // low: conducted behind attenuators

// ---------------------------------------------------------------------------
// Friendly node pins - Heltec WiFi LoRa 32 V4 (ESP32-S3 + SX1262)
// ---------------------------------------------------------------------------
constexpr int PIN_LORA_NSS  = 8;
constexpr int PIN_LORA_SCK  = 9;
constexpr int PIN_LORA_MOSI = 10;
constexpr int PIN_LORA_MISO = 11;
constexpr int PIN_LORA_RST  = 12;
constexpr int PIN_LORA_BUSY = 13;
constexpr int PIN_LORA_DIO1 = 14;

// ---------------------------------------------------------------------------
// Interferer pins - generic ESP32 + CC1101 breakout
// ---------------------------------------------------------------------------
constexpr int PIN_CC_CS    = 5;   // CSN
constexpr int PIN_CC_GDO0  = 4;   // GDO0 / DIO1
constexpr int PIN_CC_SCK   = 18;
constexpr int PIN_CC_MISO  = 19;
constexpr int PIN_CC_MOSI  = 23;
constexpr int PIN_CC_RST   = 27;  // optional

// ---------------------------------------------------------------------------
// Provisioning
// ---------------------------------------------------------------------------
// Per-device pre-shared key. Provide it at build time, never in source:
//   pio run -e uav_node -DSPECTRA_PSK_HEX=\"<64 hex chars>\"
// If unset, a clearly-marked DEV placeholder is used so the scaffold builds.
constexpr size_t kPskLen = 32;

inline void load_psk(uint8_t out[kPskLen]) {
#ifdef SPECTRA_PSK_HEX
  const char* hex = SPECTRA_PSK_HEX;
  auto nib = [](char c) -> uint8_t {
    if (c >= '0' && c <= '9') return c - '0';
    if (c >= 'a' && c <= 'f') return c - 'a' + 10;
    if (c >= 'A' && c <= 'F') return c - 'A' + 10;
    return 0;
  };
  for (size_t i = 0; i < kPskLen; ++i) {
    out[i] = (nib(hex[2 * i]) << 4) | nib(hex[2 * i + 1]);
  }
#else
#pragma message("WARNING: SPECTRA_PSK_HEX not set - using DEV placeholder key")
  for (size_t i = 0; i < kPskLen; ++i) out[i] = (uint8_t)(0xA5 ^ i);
#endif
}

// Anti-replay window for the timestamp check.
constexpr uint32_t kTimestampWindowSec = 300;
constexpr uint32_t kClockSkewSec       = 30;

}  // namespace spectra
