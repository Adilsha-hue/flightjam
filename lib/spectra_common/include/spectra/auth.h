#pragma once
//
// spectra/auth.h - replay protection and a small per-link security state.
//
// Replay defense has two layers:
//   1. Monotonic counter: accept only seq strictly greater than the last seen.
//   2. Timestamp window: reject frames older than kTimestampWindowSec or further
//      in the future than kClockSkewSec.
//
#include <stdint.h>

#include "spectra/config.h"

namespace spectra {

class ReplayGuard {
 public:
  void reset(uint32_t last_seq = 0) { last_seq_ = last_seq; have_last_ = false; }

  // now = receiver's current time (seconds). Returns true if the frame is fresh.
  bool accept(uint32_t seq, uint32_t ts, uint32_t now) {
    if (seq == 0) return false;
    if (have_last_ && seq <= last_seq_) return false;      // stale / replayed seq

    if (ts + kTimestampWindowSec < now) return false;      // too old
    if (ts > now + kClockSkewSec) return false;            // from the future

    last_seq_  = seq;
    have_last_ = true;
    return true;
  }

  uint32_t last_seq() const { return last_seq_; }

 private:
  uint32_t last_seq_  = 0;
  bool     have_last_ = false;
};

}  // namespace spectra
