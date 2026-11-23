# ESP32 Acquisition Configuration

VibraFlow uses four INMP441 microphones at a target sample rate of 16 kHz.

Include the configuration file in the main Arduino sketch:

```cpp
#include "config.h"
```

Then use the constant inside the I2S configuration:

```cpp
.sample_rate = SAMPLE_RATE
```

The required settings are:

```cpp
#define SAMPLE_RATE 16000
#define MICROPHONE_COUNT 4
#define RECORD_DURATION_SECONDS 60
```

The Python Data Logger expects each text Serial line in this order:

```text
mic1,mic2,mic3,mic4,vibration
```

## Important throughput note

Setting `SAMPLE_RATE` to 16000 configures the intended acquisition rate, but
does not guarantee that text CSV over Serial can transfer four raw microphone
channels at that speed. Always check the observed rate written to the trial
JSON metadata. If it is much lower than 16 kHz, use binary transfer, local
audio storage, or on-device feature extraction before collecting the official
machine-learning dataset.
