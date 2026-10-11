// Separate V3 reference implementation. Original project firmware is preserved.
// Payload is MOCK telemetry until a GNSS parser is added.
#include <Arduino.h>
#include <SPI.h>
#include <RadioLib.h>
#include <Preferences.h>
#include <mbedtls/gcm.h>
#include "secrets.h"

SX1262 radio = new Module(8, 14, 12, 13);
Preferences state;
constexpr uint32_t DEVICE = 1;
constexpr size_t HEADER = 13, PAYLOAD = 12, TAG = 16, SIZE = HEADER + PAYLOAD + TAG;
uint32_t boot = 0, sequence = 0, highBoot = 0, highSequence = 0;
uint32_t nextTx = 0;
void put32(uint8_t* p, uint32_t v) { p[0]=v>>24; p[1]=v>>16; p[2]=v>>8; p[3]=v; }
uint32_t get32(const uint8_t* p) { return (uint32_t(p[0])<<24)|(uint32_t(p[1])<<16)|(uint32_t(p[2])<<8)|p[3]; }
void stop(const char* why) { Serial.println(why); while(true) delay(1000); }
bool crypt(bool encrypt, const uint8_t* header, const uint8_t* input, uint8_t* output, uint8_t* tag) {
  // Nonce: device id + persisted boot counter + sequence. Header is authenticated.
  uint8_t nonce[12]; memcpy(nonce, header+1, sizeof(nonce));
  mbedtls_gcm_context ctx; mbedtls_gcm_init(&ctx);
  int rc = mbedtls_gcm_setkey(&ctx, MBEDTLS_CIPHER_ID_AES, TELEMETRY_KEY, 256);
  if(rc == 0) {
    if(encrypt) rc = mbedtls_gcm_crypt_and_tag(&ctx, MBEDTLS_GCM_ENCRYPT, PAYLOAD,
      nonce, sizeof(nonce), header, HEADER, input, output, TAG, tag);
    else rc = mbedtls_gcm_auth_decrypt(&ctx, PAYLOAD, nonce, sizeof(nonce),
      header, HEADER, tag, TAG, input, output);
  }
  mbedtls_gcm_free(&ctx); return rc == 0;
}
void setup() {
  Serial.begin(115200); delay(500);
  if(!state.begin(TELEMETRY_TX ? "tx-session" : "rx-session", false)) stop("NVS open failed");
  if(TELEMETRY_TX) {
    boot=state.getUInt("boot",0);
    if(boot==UINT32_MAX) stop("Boot counter exhausted; provision new key");
    ++boot;
    if(state.putUInt("boot",boot)!=sizeof(boot)) stop("Boot counter persistence failed");
  } else {
    uint32_t watermark[2]={};
    const size_t stored=state.getBytesLength("watermark");
    if(stored && (stored!=sizeof(watermark) || state.getBytes("watermark",watermark,sizeof(watermark))!=sizeof(watermark))) stop("RX state invalid");
    highBoot=watermark[0]; highSequence=watermark[1];
  }
  SPI.begin(9,11,10,8);
  // V3 reference: 866.5 MHz, 125 kHz, SF9, CR4/5, +2 dBm, 1.8 V TCXO.
  const int rc=radio.begin(866.5,125.0,9,5,0x12,2,8,1.8);
  if(rc!=RADIOLIB_ERR_NONE) { Serial.printf("Radio init error %d\n",rc); stop("Verify exact V3 revision"); }
  Serial.println(TELEMETRY_TX ? "TX reference ready: MOCK data" : "RX reference ready");
}
void loop() {
  if(TELEMETRY_TX) {
    if(int32_t(millis()-nextTx)<0) { delay(10); return; }
    if(sequence==UINT32_MAX) stop("Sequence exhausted; restart to create next boot session");
    uint8_t frame[SIZE]={}, plain[PAYLOAD]={}; frame[0]=1;
    put32(frame+1,DEVICE); put32(frame+5,boot); put32(frame+9,++sequence);
    put32(plain,286139000); put32(plain+4,772090000); put32(plain+8,120000);
    if(!crypt(true,frame,plain,frame+HEADER,frame+HEADER+PAYLOAD)) stop("Encryption failed");
    const int rc=radio.transmit(frame,SIZE);
    Serial.printf("TX,%lu,%lu,%d\n",(unsigned long)boot,(unsigned long)sequence,rc);
    // At least 60 seconds; add a full 100x airtime idle interval after TX.
    const uint32_t airtimeMs=(radio.getTimeOnAir(SIZE)+999)/1000;
    nextTx=millis()+max(uint32_t(60000),airtimeMs*100);
  } else {
    uint8_t frame[255]={},plain[PAYLOAD]={};
    const int rc=radio.receive(frame,sizeof(frame));
    if(rc!=RADIOLIB_ERR_NONE) return;
    const size_t length=radio.getPacketLength();
    if(length!=SIZE || frame[0]!=1 || get32(frame+1)!=DEVICE) { Serial.println("RX,BAD_HEADER"); return; }
    if(!crypt(false,frame,frame+HEADER,plain,frame+HEADER+PAYLOAD)) { Serial.println("RX,BAD_TAG"); return; }
    const uint32_t b=get32(frame+5),s=get32(frame+9);
    if(b==0 || s==0 || b<highBoot || (b==highBoot && s<=highSequence)) { Serial.println("RX,REPLAY"); return; }
    // Store the high-water pair as one NVS blob, avoiding partially updated pairs.
    const uint32_t watermark[2]={b,s};
    if(state.putBytes("watermark",watermark,sizeof(watermark))!=sizeof(watermark)) stop("RX persistence failed");
    highBoot=b; highSequence=s;
    Serial.printf("RX,OK,%lu,%lu,lat_e7=%ld,lon_e7=%ld,alt_mm=%ld,rssi=%.1f\n",
      (unsigned long)b,(unsigned long)s,(long)(int32_t)get32(plain),
      (long)(int32_t)get32(plain+4),(long)(int32_t)get32(plain+8),radio.getRSSI());
  }
}
