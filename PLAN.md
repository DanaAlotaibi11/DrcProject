# VibraFlow — 8-Week Plan

## Week 1: Environment Setup

- Install Arduino IDE and Python.
- Prepare the repository structure and assign roles.
- Create a dashboard using mock data.

**Deliverable:** A working ESP32 that sends values through Serial and an initial dashboard.

## Week 2: Microphone Integration

- Connect and test the first INMP441 microphone.
- Add the second microphone.
- Confirm stable recording from both channels.

**Deliverable:** Reliable recordings from two microphones.

## Week 3: Vibration Sensor Integration

- Connect the Piezo sensor through its Analog Output.
- Mount the sensor on the tank wall.
- Read sound and vibration signals together.

**Deliverable:** A synchronized stream of three sensor signals.

## Week 4: Test Tank Setup

- Install the valve and tube.
- Fix the sensor positions.
- Define test cases and safety procedures.

**Deliverable:** A consistent and repeatable test environment.

## Week 5: Data Collection

- Record the normal condition.
- Record different controlled-leak conditions.
- Record unrelated noise and vibration.
- Label samples and document each experiment.

**Deliverable:** An organized experimental dataset.

## Week 6: Signal Analysis

- Clean and preprocess the signals.
- Extract sound and vibration features.
- Define and evaluate initial thresholds.

**Deliverable:** Initial classification between `Normal` and `Potential Leak`.

## Week 7: System Integration

- Connect the ESP32 to the Python program.
- Connect the analysis result to the dashboard.
- Display sensor readings, alerts, and experiment timestamps.

**Deliverable:** An integrated sensor-to-dashboard prototype.

## Week 8: Testing and Final Demo

- Test the system using new samples.
- Reduce false alarms.
- Document results and limitations.
- Prepare the final presentation and demonstration.

**Deliverable:** An MVP ready for evaluation.
