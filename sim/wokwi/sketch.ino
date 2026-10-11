// Wokwi ESP32-S3 protocol harness: in-memory transport, no SX1262 model.
// Public test key only. Never use this key in real equipment.
#include <Arduino.h>
#include <mbedtls/gcm.h>
const uint8_t TEST_KEY[32]={};
constexpr size_t HEADER=13,PAYLOAD=12,TAG=16,SIZE=41;
void put32(uint8_t* p,uint32_t v){p[0]=v>>24;p[1]=v>>16;p[2]=v>>8;p[3]=v;}
uint32_t get32(const uint8_t* p){return(uint32_t(p[0])<<24)|(uint32_t(p[1])<<16)|(uint32_t(p[2])<<8)|p[3];}
bool crypt(bool encrypt, const uint8_t* header, const uint8_t* input, uint8_t* output, uint8_t* tag) {
  // Nonce: device id + persisted boot counter + sequence. Header is authenticated.
  uint8_t nonce[12]; memcpy(nonce, header+1, sizeof(nonce));
  mbedtls_gcm_context ctx; mbedtls_gcm_init(&ctx);
  int rc = mbedtls_gcm_setkey(&ctx, MBEDTLS_CIPHER_ID_AES, TEST_KEY, 256);
  if(rc == 0) {
    if(encrypt) rc = mbedtls_gcm_crypt_and_tag(&ctx, MBEDTLS_GCM_ENCRYPT, PAYLOAD,
      nonce, sizeof(nonce), header, HEADER, input, output, TAG, tag);
    else rc = mbedtls_gcm_auth_decrypt(&ctx, PAYLOAD, nonce, sizeof(nonce),
      header, HEADER, tag, TAG, input, output);
  }
  mbedtls_gcm_free(&ctx); return rc == 0;
}

uint32_t highBoot=0,highSequence=0;
const char* receiveFrame(uint8_t* frame,size_t length,uint8_t* plain){
if(length!=SIZE||frame[0]!=1||get32(frame+1)!=1)return "BAD_HEADER";
if(!crypt(false,frame,frame+HEADER,plain,frame+HEADER+PAYLOAD))return "BAD_TAG";
uint32_t b=get32(frame+5),s=get32(frame+9);
if(!b||!s||b<highBoot||(b==highBoot&&s<=highSequence))return "REPLAY";
highBoot=b;highSequence=s;return "OK";
}
int failures=0,checks=0;
void check(const char* name,bool passed){checks++;if(!passed)failures++;Serial.printf("%s %s\n",passed?"PASS":"FAIL",name);}
void setup(){Serial.begin(115200);delay(1000);Serial.println("FLIGHTJAM ESP32-S3 PROTOCOL TEST");
uint8_t frame[SIZE]={},plain[PAYLOAD]={},decoded[PAYLOAD]={};frame[0]=1;
put32(frame+1,1);put32(frame+5,1);put32(frame+9,1);
put32(plain,286139000);put32(plain+4,772090000);put32(plain+8,120000);
check("encrypt",crypt(true,frame,plain,frame+HEADER,frame+HEADER+PAYLOAD));
check("valid receive",strcmp(receiveFrame(frame,SIZE,decoded),"OK")==0);
check("payload matches",memcmp(plain,decoded,PAYLOAD)==0);
check("replay rejected",strcmp(receiveFrame(frame,SIZE,decoded),"REPLAY")==0);
frame[SIZE-1]^=1;check("tampered tag rejected",strcmp(receiveFrame(frame,SIZE,decoded),"BAD_TAG")==0);frame[SIZE-1]^=1;
frame[HEADER]^=1;check("tampered ciphertext rejected",strcmp(receiveFrame(frame,SIZE,decoded),"BAD_TAG")==0);frame[HEADER]^=1;
check("short frame rejected",strcmp(receiveFrame(frame,SIZE-1,decoded),"BAD_HEADER")==0);
frame[0]=2;check("wrong version rejected",strcmp(receiveFrame(frame,SIZE,decoded),"BAD_HEADER")==0);frame[0]=1;
put32(frame+5,2);put32(frame+9,1);crypt(true,frame,plain,frame+HEADER,frame+HEADER+PAYLOAD);
check("new session accepted",strcmp(receiveFrame(frame,SIZE,decoded),"OK")==0);
Serial.printf("RESULT %d/%d PASSED\n",checks-failures,checks);Serial.println("Radio/GNSS/NVS persistence are NOT tested.");}
void loop(){delay(1000);}
