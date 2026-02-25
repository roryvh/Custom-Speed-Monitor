#include <Arduino.h>
#include <cmath>

// ===================== USER SETTINGS =====================
constexpr float kBeamSpacing_m = 0.03f;   // distance between adjacent beams
constexpr uint8_t N_BEAMS = 6;

// Change these to match your wiring
const uint8_t BEAM_PINS[N_BEAMS] = {0, 1, 2, 3, 4, 5};

// If sensor pulls LOW when broken → FALLING
// If sensor pulls HIGH when broken → RISING
constexpr int kInterruptEdge = FALLING;

// Ignore ultra-fast noise
constexpr uint32_t kMinPulseGap_us = 200;
// ========================================================

// ISR shared
volatile uint32_t g_hitTime_us[N_BEAMS] = {0};
volatile bool g_hitFlag[N_BEAMS] = {false};

// Session state
uint32_t sessionTime_us[N_BEAMS] = {0};
bool sessionHave[N_BEAMS] = {false};
bool sessionActive = false;

bool start = true;

// ---------- Helpers ----------
inline float speed_mps(uint32_t t0, uint32_t t1) {
  uint32_t dt = t1 - t0; // unsigned handles rollover
  if (dt == 0) return NAN;
  return kBeamSpacing_m / (dt / 1e6f);
}

inline void resetSession() {
  for (uint8_t i = 0; i < N_BEAMS; i++) {
    sessionTime_us[i] = 0;
    sessionHave[i] = false;
  }
  sessionActive = false;
}

// ---------- ISR core ----------
volatile uint32_t g_lastIsr_us[N_BEAMS] = {0};

inline void handleBeamISR(uint8_t i) {
  uint32_t now = micros();
  if (now - g_lastIsr_us[i] < kMinPulseGap_us) return;
  g_lastIsr_us[i] = now;

  g_hitTime_us[i] = now;
  g_hitFlag[i] = true;
}

// wrappers
void isr0(){ handleBeamISR(0); }
void isr1(){ handleBeamISR(1); }
void isr2(){ handleBeamISR(2); }
void isr3(){ handleBeamISR(3); }
void isr4(){ handleBeamISR(4); }
void isr5(){ handleBeamISR(5); }

// ---------- Setup ----------
void setup() {
  Serial.begin(115200);
  while (!Serial && millis() < 3000) {}

  for (uint8_t i = 0; i < N_BEAMS; i++) {
    pinMode(BEAM_PINS[i], INPUT_PULLUP);
  }

  attachInterrupt(digitalPinToInterrupt(BEAM_PINS[0]), isr0, kInterruptEdge);
  attachInterrupt(digitalPinToInterrupt(BEAM_PINS[1]), isr1, kInterruptEdge);
  attachInterrupt(digitalPinToInterrupt(BEAM_PINS[2]), isr2, kInterruptEdge);
  attachInterrupt(digitalPinToInterrupt(BEAM_PINS[3]), isr3, kInterruptEdge);
  attachInterrupt(digitalPinToInterrupt(BEAM_PINS[4]), isr4, kInterruptEdge);
  attachInterrupt(digitalPinToInterrupt(BEAM_PINS[5]), isr5, kInterruptEdge);
  resetSession();
}

// ---------- Main loop ----------
void loop() {
  uint32_t t[N_BEAMS];
  bool f[N_BEAMS];

  // Snapshot ISR data
  noInterrupts();
  for (uint8_t i = 0; i < N_BEAMS; i++) {
    t[i] = g_hitTime_us[i];
    f[i] = g_hitFlag[i];
    g_hitFlag[i] = false;
  }
  interrupts();

  // Process hits
  for (uint8_t i = 0; i < N_BEAMS; i++) {
    if (!f[i]) continue;

    // Start new shot on beam 0
    if (i == 0) {
      resetSession();
      sessionActive = true;
      sessionHave[0] = true;
      sessionTime_us[0] = t[0];
      continue;
    }

    if (!sessionActive) continue;

    // Enforce order
    if (sessionHave[i - 1] && !sessionHave[i]) {
      sessionHave[i] = true;
      sessionTime_us[i] = t[i];

      // Compute running average
      float sum = 0;
      uint8_t n = 0;

      for (uint8_t k = 0; k < i; k++) {
        float v = speed_mps(sessionTime_us[k],
                             sessionTime_us[k + 1]);
        if (isfinite(v)) {
          sum += v;
          n++;
        }
      }

      float avg = sum / n;
    }

    // End of monitor → final summary
    if (start) {
      Serial.println("v1, v2, v3, v4, v5");
      start = false;
    }

    if (i == N_BEAMS - 1) {
      float v = speed_mps(sessionTime_us[0],
                             sessionTime_us[1]);

      Serial.print(String(v));

      for (uint8_t k = 1; k < N_BEAMS - 1; k++) {
        float v = speed_mps(sessionTime_us[k],
                             sessionTime_us[k + 1]);

        Serial.print(", " + String(v));

      }
      Serial.println();
      resetSession();
    }
  }
}