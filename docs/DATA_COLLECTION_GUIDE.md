# VibraFlow Data Collection Guide

This guide explains how to download the latest project changes, connect the
ESP32, and record labelled sensor data from two microphones and one Piezo
vibration sensor.

## 1. Download the latest changes

Open a terminal inside the `DrcProject` folder and run:

```bash
git pull origin main
```

Install the required Python libraries:

```bash
python -m pip install -r requirements.txt
```

## 2. Connect the hardware

Connect the following components to the ESP32:

- Microphone 1
- Microphone 2
- Piezo vibration sensor
- USB data cable between the ESP32 and the laptop

The ESP32 code must send one line containing three numeric readings in this
exact order:

```text
mic1,mic2,vibration
```

Example:

```text
1250,1260,1840
1270,1255,1835
1245,1268,1842
```

Do not print labels or explanatory text from the ESP32 during data collection.

## 3. Check the COM port

In Arduino IDE, open:

```text
Tools > Port
```

Note the ESP32 port, such as `COM3` or `COM4`.

You may briefly open Serial Monitor to verify that the three readings appear.
Close Serial Monitor before starting Python because only one program can use
the ESP32 port at a time.

## 4. Record a normal experiment

From the project root, run:

```bash
python signal_processing/data_logger.py --port COM3 --label normal --trial N01 --duration 60
```

Replace `COM3` if the ESP32 uses a different port.

This command records a normal tank condition for 60 seconds and identifies the
experiment as `N01`.

## 5. Record a controlled-leak experiment

```bash
python signal_processing/data_logger.py --port COM3 --label leak --trial L01 --duration 60
```

This records a controlled-leak condition for 60 seconds and identifies the
experiment as `L01`.

## What the Data Logger does

The Data Logger:

1. Opens the ESP32 Serial connection.
2. Receives Microphone 1, Microphone 2 and Piezo readings.
3. Adds an elapsed timestamp to every reading.
4. Adds the experiment label and trial ID.
5. Rejects incomplete or invalid Serial lines.
6. Prevents accidental overwriting of an existing trial.
7. Calculates the observed sampling rate.
8. Saves the raw time-series data and experiment information.

The Data Logger only collects and organizes data. It does not detect leaks or
train the machine-learning model.

## Output files

A normal experiment is saved as:

```text
dataset/raw/normal/N01.csv
dataset/raw/normal/N01.json
```

A leak experiment is saved as:

```text
dataset/raw/leak/L01.csv
dataset/raw/leak/L01.json
```

The CSV contains:

```text
timestamp_ms,mic1,mic2,vibration,label,trial_id
```

The JSON file contains:

- Recording duration
- COM port
- Baud rate
- Number of valid readings
- Number of rejected readings
- Observed sampling rate

## First pilot dataset

Collect the following experiments using the same sensor locations, water level,
recording duration and leak position:

- `N01` to `N05`: normal condition
- `L01` to `L05`: controlled-leak condition

Do not touch or move the tank and sensors while an experiment is being
recorded. Review `N01` before collecting the remaining experiments.
