# VibraFlow Machine Learning Algorithm Plan

## Objective

Develop a machine-learning pipeline that uses recordings from four INMP441
microphones and one Piezo vibration sensor to classify the tank condition as:

- `Normal`
- `Potential Leak`

The ML pipeline starts after the Data Logger successfully creates validated CSV
recordings.

## Expected Raw Data

Each experiment should contain these columns:

```text
sample_index
timestamp_ms
mic1
mic2
mic3
mic4
vibration
label
trial_id
```

Recommended acquisition settings:

```text
Microphones: 4 × INMP441
Target sample rate: 16000 Hz
Experiment duration: 60 seconds
```

---

## Phase 1 — Raw Data Validation

Before training, verify that:

- All required columns exist.
- No sensor column is completely empty.
- The values change and are not constantly zero.
- The signals are not continuously saturated.
- The recording duration is approximately 60 seconds.
- Missing, duplicated and rejected readings are documented.
- The actual acquisition rate is verified.

### Deliverable

```text
reports/data_quality_report.csv
```

Do not collect the complete dataset before validating the pilot recordings.

---

## Phase 2 — Signal Preprocessing

Process every recording independently:

1. Sort rows using `sample_index`.
2. Remove invalid and duplicated rows.
3. Detect missing samples.
4. Remove the DC offset from every channel.
5. Normalize microphone channels when appropriate.
6. Preserve the original `trial_id` and `label`.
7. Apply filters only after inspecting pilot spectra.

Do not merge different trials into one continuous signal.

### Deliverable

```text
dataset/processed/
```

---

## Phase 3 — Windowing

Divide every 60-second recording into two-second windows with 50% overlap:

```text
0–2 seconds
1–3 seconds
2–4 seconds
...
58–60 seconds
```

At 16 kHz, each two-second microphone window contains:

```text
16000 × 2 = 32000 samples
```

Every window must retain its original trial identity:

```text
trial_id = N01
window_id = N01_W001
label = normal
```

A 60-second recording produces approximately 59 overlapping windows.

---

## Phase 4 — Feature Extraction

### Features for Each Microphone

Extract from `mic1`, `mic2`, `mic3` and `mic4`:

- Mean
- RMS
- Standard deviation
- Maximum peak
- Crest factor
- Zero-crossing rate
- Dominant frequency
- Spectral centroid
- Frequency-band energy

### Piezo Features

Extract:

- RMS
- Standard deviation
- Maximum peak
- Dominant frequency
- Frequency-band energy

### Multi-Sensor Features

Add:

- Strongest microphone
- Average microphone energy
- Difference between strongest and weakest microphone
- Ratios between microphone energies
- Correlation between microphones
- Correlation between microphone and Piezo activity

### Deliverable

```text
dataset/features/features.csv
```

Example columns:

```text
trial_id
window_id
mic1_rms
mic2_rms
mic3_rms
mic4_rms
piezo_rms
dominant_frequency
band_energy
label
```

---

## Phase 5 — Dataset Splitting

Windows from the same recording must not appear in both training and testing
sets.

Example:

```text
Training:
N01, N02, N03, N04
L01, L02, L03, L04

Testing:
N05, L05
```

Use grouped splitting:

```python
GroupShuffleSplit
```

or:

```python
GroupKFold
```

with:

```text
groups = trial_id
```

This prevents data leakage and provides a realistic evaluation on unseen
experiments.

---

## Phase 6 — Model Training

Train and compare:

1. Logistic Regression
2. Support Vector Machine
3. Random Forest

The proposed primary model is:

```python
from sklearn.ensemble import RandomForestClassifier

model = RandomForestClassifier(
    n_estimators=300,
    class_weight="balanced",
    random_state=42
)

model.fit(X_train, y_train)
```

Random Forest is recommended because it:

- Works well with small and medium structured datasets.
- Captures nonlinear relationships.
- Does not require a deep-learning dataset.
- Provides feature importance.
- Is straightforward to integrate into the dashboard.

---

## Phase 7 — Model Evaluation

Evaluate every model using:

- Recall
- Precision
- F1-score
- Confusion matrix
- ROC-AUC
- False-alarm rate

Recall is especially important because it measures how many real leaks are
detected.

Report performance by:

- Leak severity
- Water level
- Sensor position
- Recording session

Do not select the final model using accuracy alone.

---

## Phase 8 — Recording-Level Decision

The model predicts every two-second window:

```text
Normal probability = 0.15
Leak probability = 0.85
```

To reduce false alarms, combine consecutive predictions.

Initial proposed rule:

```text
If at least three consecutive windows predict Leak:
    Potential Leak
Otherwise:
    Normal
```

This rule is provisional. The probability threshold and number of consecutive
windows must be selected using validation data.

---

## Phase 9 — Model Export

Save the selected model:

```text
ml/models/random_forest.pkl
```

Save its configuration:

```text
ml/models/model_metadata.json
```

Metadata should contain:

- Model version
- Feature column order
- Sampling rate
- Window duration
- Window overlap
- Preprocessing settings
- Probability threshold
- Training date
- Training trial IDs
- Testing trial IDs

---

## Phase 10 — Dashboard Integration

The final operational pipeline is:

```text
Sensor readings
→ Two-second window
→ Preprocessing
→ Feature extraction
→ Random Forest
→ Leak probability
→ Consecutive-window decision
→ Supabase
→ Dashboard
```

The Dashboard can display:

- System status
- Leak probability
- Detection time
- Strongest microphone
- Recent sensor activity

---

## Pilot Before Full Dataset Collection

The six pilot recordings are a small equipment-validation session, not the
final training dataset. Record three normal conditions and three controlled
leaks. Every trial is a separate 60-second recording.

| Order | Trial ID | Logger Label | Physical Condition |
|---:|---|---|---|
| 1 | `P-N01` | `normal` | Valve fully closed; no leak |
| 2 | `P-H01` | `leak` | Strong controlled leak |
| 3 | `P-N02` | `normal` | Valve closed again |
| 4 | `P-H02` | `leak` | Repeat the exact strong-leak setting |
| 5 | `P-N03` | `normal` | Valve closed again |
| 6 | `P-M01` | `leak` | Moderate controlled leak |

The alternating order checks whether the system returns to the normal signal
after the valve is closed. Repeating the strong leak checks whether the setup
produces similar results under the same condition.

### Example Commands

```bash
python signal_processing/data_logger.py --port COM3 --label normal --trial P-N01 --duration 60
python signal_processing/data_logger.py --port COM3 --label leak --trial P-H01 --duration 60
python signal_processing/data_logger.py --port COM3 --label normal --trial P-N02 --duration 60
python signal_processing/data_logger.py --port COM3 --label leak --trial P-H02 --duration 60
python signal_processing/data_logger.py --port COM3 --label normal --trial P-N03 --duration 60
python signal_processing/data_logger.py --port COM3 --label leak --trial P-M01 --duration 60
```

Replace `COM3` with the actual ESP32 port.

### Procedure Between Trials

1. Wait until the terminal reports that the current trial was saved.
2. Close or adjust the valve for the next condition.
3. Refill the tank to the marked starting water level.
4. Wait for the water and sensor signals to stabilize.
5. Do not move the microphones or Piezo.
6. Start the next command.

Use a clearly marked valve position for the strong and moderate leak settings.
The two strong-leak trials must use the same valve position.

### Pilot Acceptance Checks

After the six recordings:

1. Confirm that all four microphone and Piezo channels contain valid data.
2. Compare the two strong-leak recordings to check repeatability.
3. Plot normal and leak time signals and spectra.
4. Calculate leak-to-normal spectral ratios.
5. Identify frequency bands that consistently increase during leakage.
6. Verify that strong leakage separates clearly from the normal condition.

If the strong leak cannot be distinguished from normal, stop. Fix the sensor
placement, synchronization, sampling or acquisition method before collecting
the full dataset. Six pilot recordings are enough to validate the measurement
pipeline, but they are not enough to claim final ML accuracy.

---

## Proposed ML Project Structure

```text
ml/
├── validate_data.py
├── preprocess.py
├── extract_features.py
├── build_dataset.py
├── train_model.py
├── evaluate_model.py
├── predict.py
├── README.md
└── models/
    ├── random_forest.pkl
    └── model_metadata.json
```

---

## Recommended Execution Order

1. Complete and verify the four-microphone Data Logger.
2. Collect six pilot recordings.
3. Generate a data-quality report.
4. Examine time-domain and frequency-domain plots.
5. Select useful frequency bands.
6. Collect the complete dataset.
7. Preprocess and divide recordings into windows.
8. Extract features.
9. Split the data by `trial_id`.
10. Train and compare the three models.
11. Evaluate on unseen recordings.
12. Save the best model and metadata.
13. Connect prediction results to Supabase and the Dashboard.

## Important Notes

- Do not mix recordings collected using different microphone models in the same
  final training dataset.
- Do not define final leak thresholds before analyzing real recordings.
- Do not randomly split windows without respecting `trial_id`.
- Keep sensor locations and starting water level documented for every trial.
- Ten recordings may validate the pipeline, but more varied independent
  recordings are required before claiming reliable real-world accuracy.
