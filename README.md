# VibraFlow

**Low-Cost Water Tank Leak Detection Using Sound and Vibration**

VibraFlow is a low-cost prototype designed to detect potential water tank leaks by analyzing sound and vibration signals and displaying the results on a simple dashboard.

## Problem

Small water tank leaks can be difficult to detect visually. If left unnoticed, they may lead to water loss and further damage. Therefore, a low-cost early-warning system is needed to monitor unusual changes and alert the user when an inspection may be required.

## Proposed Solution

The system uses:

- Two `INMP441` microphones to capture sound from different points.
- A `Piezo` vibration sensor to measure vibrations on the tank wall.
- An `ESP32` board to collect the sensor readings and send them to a computer.
- Python software to process and analyze the signals.
- A dashboard to display readings and alerts.

The system combines sound and vibration readings and displays one of the following conditions:

- `Normal` — No unusual indicators are detected.
- `Potential Leak` — Unusual indicators are detected and further inspection is recommended.

## MVP Objectives

- Read the sensor signals reliably.
- Record data from normal and controlled-leak conditions.
- Compare sound and vibration features between both conditions.
- Develop an initial detection method using thresholds.
- Display sensor readings, system status, and alerts on a dashboard.

> VibraFlow is an early-warning prototype. It does not identify the exact location of a leak and does not replace a professional inspection.

## Required Components

- ESP32 Development Board
- 2 × INMP441 Microphones
- Piezo Vibration Sensor Module with Analog Output (AO)
- Breadboard
- Jumper Wires
- USB Cable
- Test Tank, Valve, and Tube
- Laptop

**Maximum MVP budget: 400 SAR.**

## Technologies

- ESP32 / Arduino IDE
- Python
- Digital Signal Processing
- Serial Communication
- Dashboard Development

## Project Structure

```text
VibraFlow/
├── esp32/             # ESP32 code and sensor readings
├── signal_processing/ # Sound and vibration signal processing
├── dashboard/         # Readings, system status, and alerts interface
├── dataset/           # Experimental data and documentation
├── tests/             # System and software tests
└── docs/              # Wiring diagrams and project documentationالتوصيلات والتوثيق
```

## حالة المشروع

المشروع حاليًا في مرحلة تجهيز واختبار الـMVP خلال ثمانية أسابيع. راجع ملف [PLAN.md](PLAN.md) للاطلاع على الخطة، وملف [TASKS.md](TASKS.md) لمهام الفريق.
