#include "spectra/frame.h"

#include <string.h>

#include <mbedtls/md.h>

namespace spectra {
namespace {

inline void put_u16_be(uint8_t* p, uint16_t v) {
  p[0] = (uint8_t)(v >> 8);
  p[1] = (uint8_t)(v);
}
inline void put_u32_be(uint8_t* p, uint32_t v) {
  p[0] = (uint8_t)(v >> 24);
  p[1] = (uint8_t)(v >> 16);
  p[2] = (uint8_t)(v >> 8);
  p[3] = (uint8_t)(v);
}
inline uint16_t get_u16_be(const uint8_t* p) {
  return (uint16_t)((p[0] << 8) | p[1]);
}
inline uint32_t get_u32_be(const uint8_t* p) {
  return ((uint32_t)p[0] << 24) | ((uint32_t)p[1] << 16) |
         ((uint32_t)p[2] << 8) | (uint32_t)p[3];
}

// HMAC-SHA256 (mbedTLS). `out` must have room for 32 bytes.
bool hmac_sha256(const uint8_t* key, size_t key_len,
                 const uint8_t* msg, size_t msg_len, uint8_t out[32]) {
  const mbedtls_md_info_t* info = mbedtls_md_info_from_type(MBEDTLS_MD_SHA256);
  if (info == nullptr) return false;
  return mbedtls_md_hmac(info, key, key_len, msg, msg_len, out) == 0;
}

inline void serialize_header(const FrameHeader& h, uint8_t* p) {
  p[0] = h.version;
  p[1] = h.dev_id;
  put_u32_be(p + 2, h.seq);
  put_u32_be(p + 6, h.timestamp);
  put_u16_be(p + 10, h.payload_len);
}

}  // namespace

uint16_t crc16_ccitt(const uint8_t* data, size_t len) {
  uint16_t crc = 0xFFFF;
  for (size_t i = 0; i < len; ++i) {
    crc ^= (uint16_t)data[i] << 8;
    for (int b = 0; b < 8; ++b) {
      crc = (crc & 0x8000) ? (uint16_t)((crc << 1) ^ 0x1021) : (uint16_t)(crc << 1);
    }
  }
  return crc;
}

size_t frame_encode(const FrameHeader& h, const uint8_t* payload,
                    const uint8_t* key, size_t key_len,
                    uint8_t* out, size_t out_cap) {
  const size_t total = kOverhead + h.payload_len;
  if (out_cap < total) return 0;

  serialize_header(h, out);
  if (h.payload_len > 0 && payload != nullptr) {
    memcpy(out + kHeaderLen, payload, h.payload_len);
  }

  // CRC covers header || payload.
  const uint16_t crc = crc16_ccitt(out, kHeaderLen + h.payload_len);
  put_u16_be(out + kHeaderLen + h.payload_len, crc);

  // MAC covers header || payload || crc.
  uint8_t mac[32];
  if (!hmac_sha256(key, key_len, out, kHeaderLen + h.payload_len + kCrcLen, mac)) {
    return 0;
  }
  memcpy(out + kHeaderLen + h.payload_len + kCrcLen, mac, kMacLen);
  return total;
}

FrameStatus frame_decode(const uint8_t* in, size_t len,
                         const uint8_t* key, size_t key_len,
                         FrameHeader& h_out, const uint8_t*& payload_out) {
  if (len < kOverhead) return FrameStatus::TooShort;

  h_out.version = in[0];
  h_out.dev_id  = in[1];
  h_out.seq     = get_u32_be(in + 2);
  h_out.timestamp = get_u32_be(in + 6);
  h_out.payload_len = get_u16_be(in + 10);

  if (h_out.version != kFrameVersion) return FrameStatus::BadVersion;

  const size_t total = kOverhead + h_out.payload_len;
  if (len < total) return FrameStatus::TooShort;

  // 1) CRC first (cheap), 2) MAC (expensive).
  const uint16_t expected_crc = get_u16_be(in + kHeaderLen + h_out.payload_len);
  const uint16_t actual_crc   = crc16_ccitt(in, kHeaderLen + h_out.payload_len);
  if (expected_crc != actual_crc) return FrameStatus::BadCrc;

  uint8_t mac[32];
  if (!hmac_sha256(key, key_len, in, kHeaderLen + h_out.payload_len + kCrcLen, mac)) {
    return FrameStatus::BadMac;
  }
  if (memcmp(mac, in + kHeaderLen + h_out.payload_len + kCrcLen, kMacLen) != 0) {
    return FrameStatus::BadMac;
  }

  payload_out = in + kHeaderLen;
  return FrameStatus::Ok;
}

}  // namespace spectra
