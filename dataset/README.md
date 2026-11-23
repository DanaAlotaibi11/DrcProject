# VibraFlow Dataset

This directory stores labelled experiments collected using four INMP441
microphones and one Piezo vibration sensor.

## Required acquisition settings

```text
Microphones: 4 × INMP441
Target sample rate: 16000 Hz
Experiment duration: 60 seconds
```

The ESP32 Serial text format expected by the Python logger is:

```text
mic1,mic2,mic3,mic4,vibration
```

The logger adds the sample index, elapsed time, label and trial ID.

## Record a trial

Normal condition:

```bash
python signal_processing/data_logger.py --port COM3 --label normal --trial N01 --duration 60
```

Controlled-leak condition:

```bash
python signal_processing/data_logger.py --port COM3 --label leak --trial L01 --duration 60
```

Replace `COM3` with the actual ESP32 port.

## Output files

Each experiment creates:

```text
dataset/raw/<label>/<trial_id>.csv
dataset/raw/<label>/<trial_id>.json
```

CSV columns:

```text
sample_index,timestamp_ms,mic1,mic2,mic3,mic4,vibration,label,trial_id
```

The JSON file records the expected 16 kHz rate, observed Serial row rate,
duration, valid rows and rejected rows.

## First pilot

Collect alternating baseline and leak trials:

- `P-N01`: normal
- `P-H01`: strong leak
- `P-N02`: normal
- `P-H02`: strong leak repeated
- `P-N03`: normal
- `P-M01`: moderate leak

Keep microphone positions, Piezo position and starting water level fixed. Review
the six pilot recordings before collecting the official dataset.

## Throughput warning

Four raw 16 kHz microphone channels are usually too large for line-by-line text
CSV over a slow Serial connection. The logger reports the observed row rate.
Do not claim full-rate audio unless the JSON metadata confirms the acquisition
and transfer method preserved the intended rate. Binary transfer, local audio
storage or on-device feature extraction may be required.
