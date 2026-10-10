#pragma once
//
// spectra/frame.h - on-air frame format, CRC16 and HMAC sign/verify.
//
// Wire layout (all multi-byte header fields big-endian):
//
//   +--------+--------+--------+--------+--------+--------+--------------+--------+--------+
//   | ver(1) | dev(1) | seq(4) | ts(4)  | plen(2)| payload (plen)        | crc(2) | mac(16)|
//   +--------+--------+--------+--------+--------+--------+--------------+--------+--------+
//
// The 16-byte MAC is the truncation of HMAC-SHA256 over (header || payload || crc).
//
#include <stdint.h>
#include <stddef.h>

namespace spectra {

constexpr uint8_t kFrameVersion = 1;
constexpr size_t  kHeaderLen    = 12;   // 1+1+4+4+2
constexpr size_t  kCrcLen       = 2;
constexpr size_t  kMacLen       = 16;   // truncated HMAC-SHA256
constexpr size_t  kOverhead     = kHeaderLen + kCrcLen + kMacLen;

struct __attribute__((packed)) FrameHeader {
  uint8_t  version;
  uint8_t  dev_id;
  uint32_t seq;          // monotonic counter
  uint32_t timestamp;    // seconds since boot (or UTC)
  uint16_t payload_len;
};

enum class FrameStatus {
  Ok = 0,
  TooShort,
  BadVersion,
  BadCrc,
  BadMac,
};

// CRC-16/CCITT-FALSE.
uint16_t crc16_ccitt(const uint8_t* data, size_t len);

// Encode + sign. Returns total bytes written, or 0 on error (buffer too small).
size_t frame_encode(const FrameHeader& h, const uint8_t* payload,
                    const uint8_t* key, size_t key_len,
                    uint8_t* out, size_t out_cap);

// Verify CRC then MAC, then unpack. `payload_out` points into `in`.
FrameStatus frame_decode(const uint8_t* in, size_t len,
                         const uint8_t* key, size_t key_len,
                         FrameHeader& h_out, const uint8_t*& payload_out);

}  // namespace spectra
