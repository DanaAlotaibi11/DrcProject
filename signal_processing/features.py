"""
features.py — Core signal feature extraction for the ThermaTank leak-detection system.

SCOPE
-----
This module contains ONLY the functions required by the task brief:
    - mean
    - maximum peak
    - RMS
    - standard deviation
    - frequency spectrum (FFT)
    - a wrapper that applies all of the above to the three sensor channels
      (two microphones + one vibration/piezo channel)

Optional, exploratory features (windowing, band energy, spectral descriptors)
live in `extras.py` so that this file stays limited to the deliverable.

UNITS AND CALIBRATION
---------------------
Every function works on RAW SAMPLE VALUES (e.g. ADC counts) by default.
Each amplitude-returning function takes a `scale` argument:

    physical_value = raw_value * scale

`scale` converts raw counts into physical units (g, m/s^2, Pa, volts...).
It is 1.0 until the sensor part is chosen and its sensitivity is known.

This works because mean, peak, RMS, standard deviation and FFT magnitude are
all linear/homogeneous in amplitude: scaling the input by k scales the output
by k. So calibration can be applied after the fact without changing any math.

SAMPLING RATE
-------------
`fs` (samples per second) is always passed in, never hardcoded.
Only the frequency-domain function needs it: an FFT returns bin indices, and
`fs` is what converts a bin index into an actual frequency in Hz.

ERROR HANDLING
--------------
All functions raise `ValueError` on invalid input (empty, non-numeric,
non-1-D, containing NaN/Inf) or on an invalid sampling rate. Failing loudly
is intentional: it catches wiring/acquisition bugs immediately rather than
letting them propagate silently into results.

Author: ThermaTank signal processing sub-team
"""

from __future__ import annotations

import numpy as np

__all__ = [
    "validate_signal",
    "validate_fs",
    "signal_mean",
    "max_peak",
    "rms",
    "std_dev",
    "frequency_spectrum",
    "extract_features",
    "CHANNEL_NAMES",
]

# Channel labels used by `extract_features`. Two acoustic, one vibration.
CHANNEL_NAMES = ("mic1", "mic2", "vibration")


# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------

def validate_signal(signal, name: str = "signal") -> np.ndarray:
    """
    Check that `signal` is a usable 1-D numeric array and return it as float64.

    Parameters
    ----------
    signal : array-like
        The raw samples from one sensor channel.
    name : str
        Label used in error messages, so the caller knows which channel failed.

    Returns
    -------
    numpy.ndarray
        1-D float64 copy of the input.

    Raises
    ------
    ValueError
        If the input is empty, not 1-D, not numeric, or contains NaN/Inf.
    """
    try:
        arr = np.asarray(signal, dtype=np.float64)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name}: could not be read as numeric data ({exc})") from exc

    if arr.ndim != 1:
        raise ValueError(
            f"{name}: expected a 1-D array (one channel), got shape {arr.shape}. "
            "Pass each channel separately."
        )
    if arr.size == 0:
        raise ValueError(f"{name}: is empty — no samples to process.")
    if not np.all(np.isfinite(arr)):
        n_bad = int(np.count_nonzero(~np.isfinite(arr)))
        raise ValueError(
            f"{name}: contains {n_bad} non-finite sample(s) (NaN or Inf). "
            "This usually means dropped samples during acquisition."
        )
    return arr


def validate_fs(fs) -> float:
    """
    Check that the sampling rate is a positive, finite number.

    Parameters
    ----------
    fs : float
        Sampling rate in samples per second (Hz).

    Returns
    -------
    float

    Raises
    ------
    ValueError
        If `fs` is missing, non-numeric, zero, negative or non-finite.
    """
    if fs is None:
        raise ValueError("fs: sampling rate is required for frequency-domain analysis.")
    try:
        fs_val = float(fs)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"fs: expected a number, got {fs!r}") from exc

    if not np.isfinite(fs_val) or fs_val <= 0:
        raise ValueError(f"fs: must be a positive finite number, got {fs_val}")
    return fs_val


def _validate_scale(scale) -> float:
    """Check the calibration multiplier is a finite number."""
    try:
        scale_val = float(scale)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"scale: expected a number, got {scale!r}") from exc
    if not np.isfinite(scale_val):
        raise ValueError(f"scale: must be finite, got {scale_val}")
    return scale_val


# ---------------------------------------------------------------------------
# Time-domain features  (required by the brief)
# ---------------------------------------------------------------------------

def signal_mean(signal, scale: float = 1.0) -> float:
    """
    Arithmetic mean of the samples — i.e. the DC offset of the channel.

    INTERPRETATION: for an AC sensor (piezo, microphone) the mean of a healthy
    signal is close to zero, or close to the ADC mid-point if the front end
    adds a DC bias. It is therefore a SENSOR-HEALTH / OFFSET CHECK, not a leak
    feature. A drifting mean suggests a bias problem, saturation, or a loose
    connection.

    Parameters
    ----------
    signal : array-like
        1-D raw samples.
    scale : float, default 1.0
        Calibration multiplier (raw units -> physical units).

    Returns
    -------
    float
        Mean amplitude, in raw units if `scale` is 1.0.
    """
    arr = validate_signal(signal)
    scale_val = _validate_scale(scale)
    return float(np.mean(arr) * scale_val)


def max_peak(signal, scale: float = 1.0, signed: bool = False) -> float:
    """
    Maximum peak amplitude of the signal.

    By default this is the maximum ABSOLUTE deviation, max(|x|), which is the
    usual meaning of "peak" for a bipolar AC signal: it captures the largest
    excursion in either direction.

    INTERPRETATION: sensitive to transients (an impact, someone bumping the
    tank) and to clipping. A peak sitting exactly at the ADC full-scale value
    means the signal is saturating and the gain is too high.

    Parameters
    ----------
    signal : array-like
        1-D raw samples.
    scale : float, default 1.0
        Calibration multiplier.
    signed : bool, default False
        If True, return the largest signed value max(x) instead of max(|x|).
        Useful only when the positive and negative directions mean different
        physical things.

    Returns
    -------
    float
    """
    arr = validate_signal(signal)
    scale_val = _validate_scale(scale)
    peak = np.max(arr) if signed else np.max(np.abs(arr))
    return float(peak * scale_val)


def rms(signal, scale: float = 1.0) -> float:
    """
    Root-mean-square amplitude: sqrt(mean(x^2)).

    INTERPRETATION: RMS is proportional to the square root of the signal's
    total energy, so it is the natural measure of "how much is going on" in
    the channel. It is a strong candidate leak feature, but on its own it
    responds to ANY loud event, not just leaks — which is why band-limited
    energy (see extras.band_energy) is expected to separate leak from
    background far better.

    NOTE: this is the raw RMS, computed about zero, NOT about the mean. If the
    channel carries a DC bias, that bias contributes to the result. Remove the
    offset first if you want the AC-only value (then RMS == standard deviation).

    Parameters
    ----------
    signal : array-like
        1-D raw samples.
    scale : float, default 1.0
        Calibration multiplier.

    Returns
    -------
    float
    """
    arr = validate_signal(signal)
    scale_val = _validate_scale(scale)
    return float(np.sqrt(np.mean(arr ** 2)) * scale_val)


def std_dev(signal, scale: float = 1.0, ddof: int = 0) -> float:
    """
    Standard deviation of the samples — the RMS of the signal about its mean.

    INTERPRETATION: measures the spread of the signal, i.e. its AC content
    with any DC offset removed.

    RELATIONSHIP TO RMS: for a zero-mean signal, std == rms. The two will be
    nearly identical in practice and are therefore largely redundant; the
    difference between them is exactly the DC offset. Both are included
    because the brief asks for both, and because comparing them is a cheap way
    to detect an unexpected bias.

    Parameters
    ----------
    signal : array-like
        1-D raw samples.
    scale : float, default 1.0
        Calibration multiplier.
    ddof : int, default 0
        Delta degrees of freedom. 0 = population std (the usual choice for a
        long signal record); 1 = sample std.

    Returns
    -------
    float
    """
    arr = validate_signal(signal)
    scale_val = _validate_scale(scale)
    if arr.size <= ddof:
        raise ValueError(
            f"signal: needs more than ddof={ddof} samples to compute a standard "
            f"deviation, got {arr.size}."
        )
    return float(np.std(arr, ddof=ddof) * scale_val)


# ---------------------------------------------------------------------------
# Frequency-domain feature  (required by the brief)
# ---------------------------------------------------------------------------

def frequency_spectrum(
    signal,
    fs,
    scale: float = 1.0,
    window: str = "hann",
    detrend: bool = True,
) -> dict:
    """
    Single-sided amplitude spectrum of a real-valued signal, via FFT.

    WHAT IT RETURNS: frequencies in Hz and the corresponding amplitudes, so the
    result can be plotted directly as amplitude vs frequency.

    IMPLEMENTATION NOTES (the details that are easy to get wrong):
      * `np.fft.rfft` is used because the input is real — it returns only the
        non-negative frequencies, which is all that is physically meaningful.
      * A Hann window is applied before the transform to reduce spectral
        leakage from the signal not being a whole number of cycles long. The
        amplitudes are then corrected by the window's coherent gain so that a
        pure sine of amplitude A still reads as A.
      * Amplitudes are normalised by the number of samples and the non-DC bins
        are doubled, so the result is a single-sided AMPLITUDE spectrum
        (not power, not an unnormalised FFT magnitude).
      * The mean is removed by default, so the large DC bin does not dominate
        the plot.

    FREQUENCY RESOLUTION: df = fs / N. Longer records give finer resolution.
    MAXIMUM FREQUENCY: fs / 2 (Nyquist). Anything above this in the real world
    must be removed by an ANALOG low-pass filter before the ADC — it cannot be
    fixed here.

    Parameters
    ----------
    signal : array-like
        1-D raw samples.
    fs : float
        Sampling rate in Hz. Required.
    scale : float, default 1.0
        Calibration multiplier applied to the amplitudes.
    window : {'hann', 'hamming', 'blackman', 'none'}, default 'hann'
        Window applied before the FFT.
    detrend : bool, default True
        Subtract the mean before transforming (removes the DC bin).

    Returns
    -------
    dict
        {
          'frequencies' : ndarray, Hz, ascending, length N//2 + 1
          'amplitudes'  : ndarray, same length, single-sided amplitude
          'fs'          : float, the sampling rate used
          'n_samples'   : int, number of samples transformed
          'resolution'  : float, frequency spacing between bins, Hz
          'nyquist'     : float, fs / 2
        }
    """
    arr = validate_signal(signal)
    fs_val = validate_fs(fs)
    scale_val = _validate_scale(scale)

    if arr.size < 2:
        raise ValueError(
            f"signal: needs at least 2 samples for an FFT, got {arr.size}."
        )

    work = arr - np.mean(arr) if detrend else arr.copy()

    # --- window selection -------------------------------------------------
    n = work.size
    windows = {
        "hann": np.hanning,
        "hamming": np.hamming,
        "blackman": np.blackman,
    }
    key = str(window).lower()
    if key in ("none", "rectangular", "boxcar"):
        win = np.ones(n)
    elif key in windows:
        win = windows[key](n)
    else:
        raise ValueError(
            f"window: unknown window {window!r}. "
            f"Expected one of {sorted(windows) + ['none']}."
        )

    # Coherent gain = mean of the window. Dividing by it restores the true
    # amplitude of a sinusoid after windowing.
    coherent_gain = float(np.mean(win))
    if coherent_gain == 0:
        raise ValueError("window: has zero coherent gain; cannot normalise.")

    # --- transform --------------------------------------------------------
    spectrum = np.fft.rfft(work * win)
    freqs = np.fft.rfftfreq(n, d=1.0 / fs_val)

    amplitudes = np.abs(spectrum) / (n * coherent_gain)
    # Double the non-DC bins: a real signal splits its energy between the
    # positive and negative frequencies, and rfft discards the negative half.
    if amplitudes.size > 1:
        last_is_nyquist = (n % 2 == 0)
        end = -1 if last_is_nyquist else None
        amplitudes[1:end] *= 2.0

    amplitudes *= scale_val

    return {
        "frequencies": freqs,
        "amplitudes": amplitudes,
        "fs": fs_val,
        "n_samples": int(n),
        "resolution": float(fs_val / n),
        "nyquist": float(fs_val / 2.0),
    }


# ---------------------------------------------------------------------------
# Multi-channel wrapper  (required by the brief)
# ---------------------------------------------------------------------------

def extract_features(
    mic1,
    mic2,
    vibration,
    fs,
    scales: dict | None = None,
    include_spectrum: bool = True,
    window: str = "hann",
) -> dict:
    """
    Run every core feature on all three channels and return them together.

    This is the main entry point. It does no math of its own — it just calls
    the single-channel functions above, so the two layers stay independent and
    each can be tested on its own.

    Parameters
    ----------
    mic1, mic2 : array-like
        1-D raw samples from the two microphone channels.
    vibration : array-like
        1-D raw samples from the piezo / vibration channel.
    fs : float
        Sampling rate in Hz, assumed identical for all three channels. If the
        channels end up being sampled at different rates, call the
        single-channel functions directly instead.
    scales : dict, optional
        Per-channel calibration multipliers, e.g.
        {'mic1': 1.0, 'mic2': 1.0, 'vibration': 1.0}.
        Missing channels default to 1.0. Values are TBD until the sensors are
        chosen and their sensitivities are known.
    include_spectrum : bool, default True
        Set False to skip the FFT when only the time-domain scalars are needed
        (much faster for long records).
    window : str, default 'hann'
        Window passed through to `frequency_spectrum`.

    Returns
    -------
    dict
        {
          'mic1': {'mean':..., 'max_peak':..., 'rms':..., 'std':...,
                   'spectrum': {...}},
          'mic2': {...},
          'vibration': {...},
          'fs': float,
          'n_samples': {'mic1': int, 'mic2': int, 'vibration': int},
        }

    Raises
    ------
    ValueError
        If any channel is invalid, or if `fs` is invalid. The error message
        names the offending channel.
    """
    fs_val = validate_fs(fs)
    scales = scales or {}

    channels = dict(zip(CHANNEL_NAMES, (mic1, mic2, vibration)))

    # Validate everything up front so a bad third channel is not discovered
    # only after the first two have been processed.
    validated = {
        name: validate_signal(data, name=name) for name, data in channels.items()
    }

    results: dict = {"fs": fs_val, "n_samples": {}}

    for name, arr in validated.items():
        scale = _validate_scale(scales.get(name, 1.0))
        channel_result = {
            "mean": signal_mean(arr, scale=scale),
            "max_peak": max_peak(arr, scale=scale),
            "rms": rms(arr, scale=scale),
            "std": std_dev(arr, scale=scale),
        }
        if include_spectrum:
            channel_result["spectrum"] = frequency_spectrum(
                arr, fs=fs_val, scale=scale, window=window
            )
        results[name] = channel_result
        results["n_samples"][name] = int(arr.size)

    return results
