# VibraFlow Data Collection Guide

## System

```text
4 × INMP441 microphones
1 × Piezo vibration sensor
ESP32
Target sample rate: 16000 Hz
One experiment: 60 seconds
```

## 1. Get the latest files

Inside the local `DrcProject` folder:

```bash
git pull origin main
python -m pip install -r requirements.txt
```

## 2. Configure ESP32

The repository contains:

```text
esp32/config.h
```

It defines:

```cpp
#define SAMPLE_RATE 16000
#define MICROPHONE_COUNT 4
#define RECORD_DURATION_SECONDS 60
```

The main Arduino I2S configuration must use:

```cpp
.sample_rate = SAMPLE_RATE
```

## 3. Verify the ESP32 output

For the current text logger, each Serial line must contain exactly:

```text
mic1,mic2,mic3,mic4,vibration
```

Example:

```text
1250,1260,1242,1271,1840
```

Close Arduino Serial Monitor before running Python.

## 4. Record one normal experiment

```bash
python signal_processing/data_logger.py --port COM3 --label normal --trial N01 --duration 60
```

## 5. Record one leak experiment

```bash
python signal_processing/data_logger.py --port COM3 --label leak --trial L01 --duration 60
```

The logger records continuously for 60 seconds and then stops. Change the tank
condition only after the terminal reports that the experiment was saved.

## 6. Output

Normal example:

```text
dataset/raw/normal/N01.csv
dataset/raw/normal/N01.json
```

The CSV contains:

```text
sample_index,timestamp_ms,mic1,mic2,mic3,mic4,vibration,label,trial_id
```

The JSON metadata contains the expected sample rate, observed Serial row rate,
duration and data-quality counts.

## 7. Verify before continuing

After `N01`, check:

- All four microphone columns contain changing values.
- The Piezo value changes when the tank surface vibrates.
- Rejected lines are low.
- The duration is approximately 60 seconds.
- The actual acquisition/transfer rate is suitable.

Do not collect the full dataset before verifying the first recording.

## Important

Milliseconds represent the elapsed time inside a 60-second experiment.
The intended microphone sampling rate is 16000 samples per second. Text CSV
over Serial may not transfer four raw channels at that rate; if the observed
rate is much lower, switch to binary transfer, local audio storage, or
on-device feature extraction before official ML data collection.
