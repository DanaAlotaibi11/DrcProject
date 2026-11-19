# VibraFlow Dataset

This directory stores labelled, raw sensor experiments collected from the
ESP32. Do not use final leak-detection thresholds until real experiments have
been reviewed.

## Serial formats

The ESP32 must print numeric CSV lines with no extra text.

Current temporary setup:

```text
mic1,vibration
1250,1840
```

Final MVP setup:

```text
mic1,mic2,vibration
1250,1260,1840
```

The laptop adds the elapsed timestamp, label and trial ID automatically.

## Collect a trial

From the repository root:

```bash
python signal_processing/data_logger.py --port COM3 --mode one-mic --label normal --trial N01 --duration 60
```

Leak example:

```bash
python signal_processing/data_logger.py --port COM3 --mode one-mic --label leak --trial L01 --duration 60
```

When the second microphone is connected, replace `one-mic` with `two-mic`.

## First pilot experiments

Collect at least:

- `N01` to `N05`: normal tank.
- `L01` to `L05`: controlled leak.
- Optional `B01` onward using label `noise`: unrelated knocks or room noise.

Each trial creates:

- `dataset/raw/<label>/<trial_id>.csv`: full time-series samples.
- `dataset/raw/<label>/<trial_id>.json`: trial metadata and data-quality counts.

## Before every recording

Keep the sensor locations, water level, recording duration and leak position
documented and as consistent as possible. Do not touch the tank during a trial.
Use a new trial ID every time; the recorder refuses to overwrite an experiment.

## CSV columns

| Column | Meaning |
|---|---|
| `timestamp_ms` | Time elapsed since the start of the trial |
| `mic1` | First microphone raw reading |
| `mic2` | Second microphone raw reading; empty in one-mic mode |
| `vibration` | Piezo raw reading |
| `label` | `normal`, `leak` or `noise` |
| `trial_id` | Unique experiment identifier |

Ten experiments are a pilot dataset for validating the pipeline. More varied
experiments will be needed before claiming reliable machine-learning accuracy.
