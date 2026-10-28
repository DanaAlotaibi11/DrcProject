# signal_processing

Feature extraction for the ThermaTank leak-detection system.

This module turns raw sound and vibration samples into numerical features.
It is written to run **before any hardware exists**: nothing is hardcoded to a
particular sensor, sampling rate, or calibration constant, so the same code
will work unchanged once real sensor data arrives.

-----

## Files

|File              |Status         |Contents                                                                               |
|------------------|---------------|---------------------------------------------------------------------------------------|
|`features.py`     |**Deliverable**|The five required functions + the three-channel wrapper. Nothing else.                 |
|`extras.py`       |Optional       |Windowing, band energy, spectral descriptors. Beyond the brief; safe to change or drop.|
|`test_features.py`|Verification   |35 tests against synthetic signals with analytically known answers.                    |
|`__init__.py`     |—              |Package setup.                                                                         |

`extras.py` imports from `features.py`, never the other way round. The core
can be reviewed against the brief on its own, and the extras can be
experimented with without touching it.

**Requirements:** `numpy`. (`pytest` for the tests.) No SciPy needed.

-----

## Quick start

```python
import numpy as np
from signal_processing import features as F

fs = 48_000          # samples/second — PLACEHOLDER, see "Open questions"

# One channel at a time
F.rms(mic1_samples)
F.frequency_spectrum(mic1_samples, fs)

# All three channels at once
results = F.extract_features(mic1, mic2, vibration, fs=fs)
results["vibration"]["rms"]
results["mic1"]["spectrum"]["frequencies"]
```

Run the tests:

```bash
python -m pytest signal_processing/test_features.py -v
```

-----

## Core API (`features.py`)

|Function                                          |Input           |Output       |Needs `fs`?|
|--------------------------------------------------|----------------|-------------|-----------|
|`signal_mean(signal, scale=1.0)`                  |1-D array       |`float`      |No         |
|`max_peak(signal, scale=1.0, signed=False)`       |1-D array       |`float`      |No         |
|`rms(signal, scale=1.0)`                          |1-D array       |`float`      |No         |
|`std_dev(signal, scale=1.0, ddof=0)`              |1-D array       |`float`      |No         |
|`frequency_spectrum(signal, fs, ...)`             |1-D array + `fs`|`dict`       |**Yes**    |
|`extract_features(mic1, mic2, vibration, fs, ...)`|3 arrays + `fs` |nested `dict`|**Yes**    |

`frequency_spectrum` returns:

```python
{
  "frequencies": ndarray,   # Hz, ascending, length N//2 + 1
  "amplitudes":  ndarray,   # single-sided amplitude, same length
  "fs":          float,
  "n_samples":   int,
  "resolution":  float,     # bin spacing = fs / N
  "nyquist":     float,     # fs / 2
}
```

`extract_features` returns `{"mic1": {...}, "mic2": {...}, "vibration": {...}, "fs": ..., "n_samples": {...}}`, where each channel dict holds `mean`,
`max_peak`, `rms`, `std` and (optionally) `spectrum`.

-----

## Design decisions

### Sampling rate is always an argument

Only the frequency-domain function depends on it. An FFT returns *bin
indices*; `fs` is what converts bin `k` into a real frequency via
`f = k · fs / N`. The time-domain features (mean, peak, RMS, std) operate on
sample values alone and give the same answer regardless of rate.

Keeping `fs` as a parameter means the module needs no hardware decisions to be
finished, and no code changes when the rate is finally chosen.

### Calibration enters as a single multiplier

The ADC gives integers. Converting to physical units is a chain:

```
counts → volts → physical units (g, m/s², Pa)
```

Every feature here is **linear in amplitude**: scale the input by *k* and the
output scales by *k*. So the whole chain collapses into one multiplicative
constant, applied after the fact:

```python
F.rms(signal, scale=0.0244)   # example only — value TBD from datasheet
```

`scale` defaults to `1.0`, meaning results are in raw ADC counts. When the
sensor is chosen, its sensitivity goes into `scale` and every output becomes
physical **without editing this module**. `test_scale_is_a_linear_multiplier`
verifies this property holds.

### Invalid input raises `ValueError`

Empty arrays, 2-D arrays, non-numeric data, NaN/Inf samples, and non-positive
sampling rates all raise immediately, with a message naming the problem and
the channel. Failing loudly catches acquisition and wiring bugs at the point
they occur. The alternative (returning `NaN` and carrying on) hides bugs until
half the results are missing with no indication why.

### Mean, RMS and std overlap — on purpose

For a zero-mean AC signal, **RMS ≈ standard deviation**, and the mean ≈ 0.
All three are included because the brief asks for them, and because comparing
them is a cheap diagnostic:

- `mean` ≈ 0 (or ≈ ADC mid-scale) → front end healthy. A drifting mean means
  bias drift, saturation, or a loose connection. It is a **sensor-health
  check, not a leak feature**.
- `rms` ≠ `std` → there is a DC offset, and the difference is exactly that
  offset.

### Windowing before the FFT

A Hann window is applied by default to reduce spectral leakage, and the
amplitudes are corrected by the window’s coherent gain so a sine of amplitude
A still reads as A. The non-DC bins are doubled so the result is a true
single-sided amplitude spectrum, not a raw FFT magnitude.

-----

## What needs validation with real sensor data

The brief asks which functions require real data. The honest split:

### Already verified — pure maths, no data needed

`signal_mean`, `max_peak`, `rms`, `std_dev`, `frequency_spectrum` and the
framing logic are all deterministic. They are tested against synthetic signals
with known answers: a 1 kHz sine of amplitude 2.0 must give RMS = 1.414, peak
= 2.0, and exactly one spectral peak at 1 kHz. All 35 tests pass.

These functions will not change when data arrives.

### Requires real data

|Item                                                  |Why it cannot be settled now                                                                     |
|------------------------------------------------------|-------------------------------------------------------------------------------------------------|
|**Sampling rate**                                     |Set by the acquisition firmware; must be ≥ 2× the highest frequency of interest.                 |
|**`scale` calibration constants**                     |From the sensor datasheet + ADC reference; one per channel.                                      |
|**Useful frequency bands**                            |Must be *measured*, see plan below.                                                              |
|**Window length / overlap**                           |Trades frequency resolution against time resolution; depends on how fast a leak signature varies.|
|**Which features actually separate leak from no-leak**|Unknown until the distributions are compared.                                                    |
|**Detection thresholds**                              |Deliberately **not defined**, per the brief. No threshold appears anywhere in this code.         |

### Plan for choosing the frequency band

1. Sample at the highest rate the hardware allows.
1. Record three conditions: **background only**, **tank sealed**, **tank with
   a deliberate small leak**.
1. Compute the average spectrum of each (`frequency_spectrum`).
1. Plot the ratio `leak_spectrum / no_leak_spectrum`.

Wherever that ratio is largest is the band to use. `extras.band_energy` takes
its bands as an argument specifically so this sweep requires no code changes.
This ratio plot is also the figure that justifies the band choice in the
final report.

-----

## Optional extras (`extras.py`)

Not part of the brief. Built on top of the core functions, no duplicated math.
None of them define a leak threshold or make a leak/no-leak decision.

|Function                                           |Purpose                                                                                             |
|---------------------------------------------------|----------------------------------------------------------------------------------------------------|
|`remove_offset(signal)`                            |Subtract the mean (simplest high-pass). Opt-in, never automatic.                                    |
|`frame_signal(signal, fs, window_seconds, overlap)`|Split a recording into overlapping frames.                                                          |
|`features_over_time(...)`                          |Core features computed per frame → a feature **time series**.                                       |
|`band_energy(signal, fs, bands)`                   |Energy in caller-specified bands. Expected to be the main leak feature.                             |
|`band_ratio(signal, fs, high_band, low_band)`      |High/low energy ratio — “hiss vs rumble”, insensitive to overall gain.                              |
|`spectral_centroid(signal, fs)`                    |Amplitude-weighted mean frequency.                                                                  |
|`peak_frequency(signal, fs)`                       |Frequency of the strongest component — usually identifies *interference*, since a leak is broadband.|
|`spectral_summary(...)`                            |All spectral descriptors in one call.                                                               |

**Why windowing matters:** a single RMS value for a 10-minute recording hides
everything. Features per frame let the detection stage use *persistence* —
a leak is continuous, whereas someone bumping the tank is a transient. That
distinction is likely to matter more than any single feature value.

**Why band energy matters:** a tank environment is full of low-frequency
noise (pumps, footsteps, wind, traffic). Leak noise is broadband and reaches
higher frequencies. Measuring energy *inside a chosen band* is what separates
“a leak” from “something loud happened”.

-----

## Open hardware questions

These affect what the system can detect, but **not** this module’s code.

1. **Piezo front end.** Is there an op-amp stage between the piezo and the
   ADC? It needs to (a) buffer — present a high input impedance so the sensor
   is not loaded, (b) apply gain — the output is small relative to the ADC’s
   ~0.8 mV step, and (c) low-pass filter before sampling. A non-inverting
   Sallen-Key stage can do all three. If the part is a piezo *module* with an
   onboard amplifier, some of this may already be handled — the datasheet
   will say.
1. **Anti-aliasing cutoff.** Anything above `fs/2` folds down into the band
   and becomes indistinguishable from a real signal. **This cannot be fixed
   in software.** The cutoff must sit above the highest frequency of interest
   and below `fs/2`.
1. **Analog output characteristics.** Some piezo modules are knock detectors
   whose output is a threshold-crossing pulse rather than a continuous
   waveform. This module needs a **waveform** — a pulse output cannot be
   analysed spectrally.
1. **Target leak frequency range and tank material.** Sets both the cutoff and
   the sampling rate. Under investigation by the detection-methods sub-task.

-----

## Status

Core module complete and tested. Ready to receive real sensor readings:
pass the measured `fs`, and the calibration constants into `scale`.