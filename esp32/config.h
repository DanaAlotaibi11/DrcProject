#pragma once

// VibraFlow INMP441 acquisition settings.
#define SAMPLE_RATE 16000
#define MICROPHONE_COUNT 4
#define RECORD_DURATION_SECONDS 60

// The I2S setup in the ESP32 sketch must use:
//     .sample_rate = SAMPLE_RATE
//
// A 60-second experiment should contain approximately:
//     SAMPLE_RATE * RECORD_DURATION_SECONDS
//     = 960000 samples per microphone.
