"""
extras.py — OPTIONAL exploratory features. NOT part of the task brief.

WHY THIS IS A SEPARATE FILE
---------------------------
`features.py` contains exactly what the brief asks for and nothing else.
This file contains functions that are expected to be useful once real sensor
data exists, but that go beyond the deliverable. Keeping them apart means:

  * `features.py` can be reviewed against the brief line by line;
  * these can be tried, changed or thrown away without touching the core;
  * nothing here is imported by `features.py`, only the other way round.

Everything here is built ON TOP of the core functions — no duplicated math.

IMPORTANT: nothing in this file defines a leak threshold or makes a
leak/no-leak decision. Those numbers must come from real recordings
(see README, "Validation plan"). The functions here are parameterised so
that bands and window lengths can be swept once data exists, instead of
being guessed now and hardcoded.

Usage:
    from signal_processing import features, extras
"""

from __future__ import annotations

import numpy as np

from .features import (
    validate_signal,
    validate_fs,
    signal_mean,
    max_peak,
    rms,
    std_dev,
    frequency_spectrum,
)

__all__ = [
    "remove_offset",
    "frame_signal",
    "features_over_time",
    "band_energy",
    "band_ratio",
    "spectral_centroid",
    "peak_frequency",
    "spectral_summary",
]


# ---------------------------------------------------------------------------
# 1. Preprocessing
# ---------------------------------------------------------------------------

def remove_offset(signal) -> np.ndarray:
    """
    Subtract the mean — the simplest possible high-pass.

    Removes the DC bias that the front end adds to centre an AC signal in the
    ADC's range. Everything downstream is then about the AC content only.

    Note: this is deliberately NOT applied automatically inside the core
    functions. Filtering should be explicit and opt-in so that it is always
    clear what has been done to a signal.

    Returns
    -------
    numpy.ndarray
    """
    arr = validate_signal(signal)
    return arr - np.mean(arr)


# ---------------------------------------------------------------------------
# 2. Windowing — features over time
# ---------------------------------------------------------------------------

def frame_signal(
    signal,
    fs,
    window_seconds: float = 0.1,
    overlap: float = 0.5,
) -> np.ndarray:
    """
    Split a continuous recording into overlapping frames.

    WHY: a real recording is minutes long, and a single RMS value for the whole
    thing hides everything interesting. Computing features per frame gives a
    feature TIME SERIES, which is what makes it possible to distinguish a leak
    (continuous, persistent) from a transient (someone bumping the tank).

    Parameters
    ----------
    signal : array-like
        1-D raw samples.
    fs : float
        Sampling rate in Hz.
    window_seconds : float, default 0.1
        Frame length in seconds. Longer frames give finer frequency resolution
        (df = 1 / window_seconds) but coarser time resolution. TBD from data.
    overlap : float, default 0.5
        Fractional overlap between consecutive frames, 0 <= overlap < 1.

    Returns
    -------
    numpy.ndarray
        2-D array of shape (n_frames, frame_length). Any samples left over at
        the end that do not fill a whole frame are discarded.

    Raises
    ------
    ValueError
        If the parameters are invalid or the signal is shorter than one frame.
    """
    arr = validate_signal(signal)
    fs_val = validate_fs(fs)

    if not np.isfinite(window_seconds) or window_seconds <= 0:
        raise ValueError(f"window_seconds: must be positive, got {window_seconds}")
    if not (0 <= overlap < 1):
        raise ValueError(f"overlap: must be in [0, 1), got {overlap}")

    frame_len = int(round(window_seconds * fs_val))
    if frame_len < 2:
        raise ValueError(
            f"window_seconds={window_seconds} at fs={fs_val} gives {frame_len} "
            "samples per frame — too short to analyse."
        )
    if frame_len > arr.size:
        raise ValueError(
            f"signal is {arr.size} samples ({arr.size / fs_val:.3f} s) but one "
            f"frame needs {frame_len} samples ({window_seconds} s)."
        )

    step = max(1, int(round(frame_len * (1.0 - overlap))))
    n_frames = 1 + (arr.size - frame_len) // step

    # Strided view avoids copying the data for every overlapping frame.
    frames = np.lib.stride_tricks.sliding_window_view(arr, frame_len)[::step]
    return np.ascontiguousarray(frames[:n_frames])


def features_over_time(
    signal,
    fs,
    window_seconds: float = 0.1,
    overlap: float = 0.5,
    scale: float = 1.0,
    bands: list | None = None,
) -> dict:
    """
    Run the core time-domain features on every frame of a recording.

    Returns a feature time series: one value per frame, plus the timestamp of
    each frame's centre. This is the form the detection stage will consume.

    Parameters
    ----------
    signal : array-like
        1-D raw samples.
    fs : float
        Sampling rate in Hz.
    window_seconds, overlap : float
        Framing parameters, see `frame_signal`.
    scale : float, default 1.0
        Calibration multiplier.
    bands : list of (low, high) tuples, optional
        If given, band energy is also computed per frame for each band.

    Returns
    -------
    dict
        {
          'time'     : ndarray, seconds, centre of each frame
          'mean'     : ndarray
          'max_peak' : ndarray
          'rms'      : ndarray
          'std'      : ndarray
          'bands'    : {(low, high): ndarray, ...}   # only if `bands` given
          'frame_length_samples' : int
          'n_frames' : int
        }
    """
    fs_val = validate_fs(fs)
    frames = frame_signal(signal, fs_val, window_seconds, overlap)
    frame_len = frames.shape[1]
    step = max(1, int(round(frame_len * (1.0 - overlap))))

    out = {
        "time": (np.arange(frames.shape[0]) * step + frame_len / 2.0) / fs_val,
        "mean": np.array([signal_mean(f, scale) for f in frames]),
        "max_peak": np.array([max_peak(f, scale) for f in frames]),
        "rms": np.array([rms(f, scale) for f in frames]),
        "std": np.array([std_dev(f, scale) for f in frames]),
        "frame_length_samples": frame_len,
        "n_frames": int(frames.shape[0]),
    }

    if bands:
        out["bands"] = {
            tuple(b): np.array(
                [band_energy(f, fs_val, [tuple(b)], scale=scale)[tuple(b)] for f in frames]
            )
            for b in bands
        }

    return out


# ---------------------------------------------------------------------------
# 3. Band-limited energy  — the expected main leak feature
# ---------------------------------------------------------------------------

def band_energy(
    signal,
    fs,
    bands: list,
    scale: float = 1.0,
    window: str = "hann",
) -> dict:
    """
    Energy within one or more frequency bands.

    WHY THIS MATTERS: a tank environment is full of low-frequency noise —
    pumps, footsteps, wind, traffic, structural knocks. Leak noise is
    broadband and reaches higher frequencies. Measuring energy inside a chosen
    band, rather than across the whole signal, is what separates "a leak" from
    "something loud happened".

    The bands are ARGUMENTS, not constants, precisely so that the right band
    can be found by sweeping once real leak/no-leak recordings exist.

    Parameters
    ----------
    signal : array-like
        1-D raw samples.
    fs : float
        Sampling rate in Hz.
    bands : list of (low_hz, high_hz) tuples
        Frequency bands to measure. Each must satisfy 0 <= low < high <= fs/2.
    scale : float, default 1.0
        Calibration multiplier.
    window : str, default 'hann'
        Window passed to the FFT.

    Returns
    -------
    dict
        {(low, high): energy, ...} where energy is the sum of squared
        amplitudes in that band. Keys preserve the order given.

    Raises
    ------
    ValueError
        If a band is malformed or extends beyond the Nyquist frequency.
    """
    fs_val = validate_fs(fs)
    spec = frequency_spectrum(signal, fs_val, scale=scale, window=window)
    freqs = spec["frequencies"]
    amps = spec["amplitudes"]
    nyquist = spec["nyquist"]

    if not bands:
        raise ValueError("bands: at least one (low, high) tuple is required.")

    results: dict = {}
    for band in bands:
        try:
            low, high = float(band[0]), float(band[1])
        except (TypeError, IndexError, ValueError) as exc:
            raise ValueError(
                f"bands: each entry must be a (low_hz, high_hz) pair, got {band!r}"
            ) from exc

        if not (np.isfinite(low) and np.isfinite(high)):
            raise ValueError(f"bands: non-finite edges in {band!r}")
        if low < 0:
            raise ValueError(f"bands: low edge must be >= 0, got {low}")
        if high <= low:
            raise ValueError(f"bands: need high > low, got ({low}, {high})")
        if high > nyquist:
            raise ValueError(
                f"bands: ({low}, {high}) Hz exceeds the Nyquist frequency "
                f"({nyquist} Hz) for fs={fs_val}. Nothing above fs/2 can be "
                "measured — the sampling rate would need to be raised."
            )

        mask = (freqs >= low) & (freqs < high)
        if not np.any(mask):
            raise ValueError(
                f"bands: ({low}, {high}) Hz contains no FFT bins. Frequency "
                f"resolution is {spec['resolution']:.3f} Hz — use a wider band "
                "or a longer record."
            )
        results[(low, high)] = float(np.sum(amps[mask] ** 2))

    return results


def band_ratio(signal, fs, high_band, low_band, scale: float = 1.0) -> float:
    """
    Ratio of energy in a high band to energy in a low band.

    WHY: captures "hiss versus rumble" in a single number, and is largely
    insensitive to overall loudness — if everything gets louder, the ratio
    stays put. That makes it more robust than raw RMS to changes in sensor
    coupling or distance.

    Parameters
    ----------
    signal : array-like
    fs : float
    high_band, low_band : (low_hz, high_hz) tuples
    scale : float, default 1.0

    Returns
    -------
    float
        high-band energy / low-band energy. Returns np.inf if the low band
        holds zero energy.
    """
    energies = band_energy(signal, fs, [tuple(high_band), tuple(low_band)], scale=scale)
    numerator = energies[tuple(float(x) for x in high_band)]
    denominator = energies[tuple(float(x) for x in low_band)]
    if denominator == 0:
        return float("inf")
    return float(numerator / denominator)


# ---------------------------------------------------------------------------
# 4. Spectral shape descriptors
# ---------------------------------------------------------------------------

def spectral_centroid(signal, fs, scale: float = 1.0) -> float:
    """
    Amplitude-weighted mean frequency — the spectrum's "centre of mass", in Hz.

    INTERPRETATION: a rough measure of brightness. Broadband leak hiss pushes
    the centroid upward; low-frequency machinery rumble pulls it down.

    Returns
    -------
    float
        Centroid frequency in Hz, or np.nan if the spectrum is empty.
    """
    spec = frequency_spectrum(signal, fs, scale=scale)
    total = float(np.sum(spec["amplitudes"]))
    if total == 0:
        return float("nan")
    return float(np.sum(spec["frequencies"] * spec["amplitudes"]) / total)


def peak_frequency(signal, fs, scale: float = 1.0) -> float:
    """
    Frequency of the single largest component in the spectrum, in Hz.

    INTERPRETATION: useful for identifying tonal interference (mains hum,
    a pump's rotational frequency, the sensor's own resonance). A leak, being
    broadband, usually does NOT produce a sharp peak — so a strong isolated
    peak is more often a clue about noise than about a leak.

    Returns
    -------
    float
    """
    spec = frequency_spectrum(signal, fs, scale=scale)
    return float(spec["frequencies"][int(np.argmax(spec["amplitudes"]))])


def spectral_summary(signal, fs, scale: float = 1.0, bands: list | None = None) -> dict:
    """
    Convenience wrapper: all spectral descriptors in one call.

    Returns
    -------
    dict
        {'centroid': float, 'peak_frequency': float,
         'bands': {...}}   # 'bands' only if `bands` was given
    """
    out = {
        "centroid": spectral_centroid(signal, fs, scale=scale),
        "peak_frequency": peak_frequency(signal, fs, scale=scale),
    }
    if bands:
        out["bands"] = band_energy(signal, fs, bands, scale=scale)
    return out
