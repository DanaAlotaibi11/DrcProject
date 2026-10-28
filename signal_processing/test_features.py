"""
test_features.py — verification against synthetic signals with known answers.

WHY SYNTHETIC SIGNALS: every function in `features.py` is pure maths, so its
correctness can be proven right now, before any sensor exists. A 1 kHz sine of
amplitude A has an RMS of exactly A/sqrt(2) and exactly one spectral peak at
1 kHz — so the tests assert those known values rather than just checking that
the code runs.

What CANNOT be tested this way is listed in the README under "Validation plan":
sampling rate, calibration, useful frequency bands, window length, thresholds.

Run with:  python -m pytest signal_processing/test_features.py -v
       or:  python signal_processing/test_features.py
"""

import numpy as np
import pytest

from signal_processing import features as F
from signal_processing import extras as E


# ---------------------------------------------------------------------------
# Test fixtures: signals whose feature values are known analytically
# ---------------------------------------------------------------------------

FS = 48_000.0          # placeholder sampling rate — TBD from hardware
DURATION = 1.0
AMPLITUDE = 2.0
FREQ = 1_000.0


def make_sine(freq=FREQ, amp=AMPLITUDE, fs=FS, duration=DURATION, offset=0.0):
    """A pure sine wave: RMS = amp/sqrt(2), peak = amp, mean = offset."""
    t = np.arange(int(fs * duration)) / fs
    return amp * np.sin(2 * np.pi * freq * t) + offset


# ---------------------------------------------------------------------------
# Time-domain features
# ---------------------------------------------------------------------------

def test_mean_of_zero_mean_sine_is_zero():
    assert F.signal_mean(make_sine()) == pytest.approx(0.0, abs=1e-9)


def test_mean_recovers_dc_offset():
    assert F.signal_mean(make_sine(offset=512.0)) == pytest.approx(512.0, abs=1e-9)


def test_max_peak_equals_amplitude():
    assert F.max_peak(make_sine()) == pytest.approx(AMPLITUDE, rel=1e-4)


def test_max_peak_uses_absolute_value():
    # A mostly-negative signal still has a positive peak magnitude.
    assert F.max_peak(np.array([-5.0, 1.0, 2.0])) == pytest.approx(5.0)
    assert F.max_peak(np.array([-5.0, 1.0, 2.0]), signed=True) == pytest.approx(2.0)


def test_rms_of_sine_is_amplitude_over_root_two():
    assert F.rms(make_sine()) == pytest.approx(AMPLITUDE / np.sqrt(2), rel=1e-4)


def test_rms_equals_std_for_zero_mean_signal():
    sig = make_sine()
    assert F.rms(sig) == pytest.approx(F.std_dev(sig), rel=1e-6)


def test_rms_and_std_diverge_with_dc_offset():
    # std ignores the offset; rms does not. This is the documented difference.
    sig = make_sine(offset=10.0)
    assert F.std_dev(sig) == pytest.approx(AMPLITUDE / np.sqrt(2), rel=1e-4)
    assert F.rms(sig) > F.std_dev(sig)


def test_scale_is_a_linear_multiplier():
    # The whole calibration design rests on this: scaling input == scaling output.
    sig = make_sine()
    assert F.rms(sig, scale=3.0) == pytest.approx(F.rms(sig * 3.0), rel=1e-9)
    assert F.max_peak(sig, scale=3.0) == pytest.approx(F.max_peak(sig * 3.0), rel=1e-9)


# ---------------------------------------------------------------------------
# Frequency domain
# ---------------------------------------------------------------------------

def test_spectrum_peak_lands_at_the_right_frequency():
    spec = F.frequency_spectrum(make_sine(), FS)
    peak_bin = int(np.argmax(spec["amplitudes"]))
    assert spec["frequencies"][peak_bin] == pytest.approx(FREQ, abs=spec["resolution"])


def test_spectrum_amplitude_matches_the_sine_amplitude():
    # Hann window + coherent-gain correction should recover the true amplitude.
    spec = F.frequency_spectrum(make_sine(), FS)
    assert np.max(spec["amplitudes"]) == pytest.approx(AMPLITUDE, rel=0.02)


def test_spectrum_metadata():
    spec = F.frequency_spectrum(make_sine(), FS)
    assert spec["nyquist"] == pytest.approx(FS / 2)
    assert spec["resolution"] == pytest.approx(FS / spec["n_samples"])
    assert spec["frequencies"][-1] <= FS / 2 + 1e-9


def test_two_tones_give_two_peaks():
    t = np.arange(int(FS)) / FS
    sig = np.sin(2 * np.pi * 1000 * t) + 0.5 * np.sin(2 * np.pi * 5000 * t)
    spec = F.frequency_spectrum(sig, FS)
    # Amplitude at 5 kHz should be about half that at 1 kHz.
    a1 = spec["amplitudes"][np.argmin(np.abs(spec["frequencies"] - 1000))]
    a5 = spec["amplitudes"][np.argmin(np.abs(spec["frequencies"] - 5000))]
    assert a5 / a1 == pytest.approx(0.5, rel=0.05)


# ---------------------------------------------------------------------------
# Invalid input — every one of these must raise ValueError
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("bad", [
    [],                                  # empty
    np.array([]),                        # empty array
    np.array([[1.0, 2.0], [3.0, 4.0]]),  # 2-D
    np.array([1.0, np.nan, 3.0]),        # NaN
    np.array([1.0, np.inf, 3.0]),        # Inf
    ["a", "b", "c"],                     # non-numeric
])
def test_invalid_signals_raise(bad):
    for func in (F.signal_mean, F.max_peak, F.rms, F.std_dev):
        with pytest.raises(ValueError):
            func(bad)


@pytest.mark.parametrize("bad_fs", [0, -1, None, "fast", np.nan, np.inf])
def test_invalid_fs_raises(bad_fs):
    with pytest.raises(ValueError):
        F.frequency_spectrum(make_sine(), bad_fs)


def test_error_message_names_the_channel():
    with pytest.raises(ValueError, match="vibration"):
        F.extract_features(make_sine(), make_sine(), [], fs=FS)


# ---------------------------------------------------------------------------
# Three-channel wrapper
# ---------------------------------------------------------------------------

def test_extract_features_returns_all_channels():
    res = F.extract_features(make_sine(), make_sine(), make_sine(), fs=FS)
    for ch in F.CHANNEL_NAMES:
        assert set(res[ch]) == {"mean", "max_peak", "rms", "std", "spectrum"}
    assert res["fs"] == FS


def test_extract_features_applies_per_channel_scales():
    sig = make_sine()
    res = F.extract_features(sig, sig, sig, fs=FS, scales={"vibration": 10.0})
    assert res["vibration"]["rms"] == pytest.approx(res["mic1"]["rms"] * 10, rel=1e-9)


def test_extract_features_can_skip_the_spectrum():
    res = F.extract_features(make_sine(), make_sine(), make_sine(),
                             fs=FS, include_spectrum=False)
    assert "spectrum" not in res["mic1"]


# ---------------------------------------------------------------------------
# Extras
# ---------------------------------------------------------------------------

def test_framing_shape_and_count():
    frames = E.frame_signal(make_sine(), FS, window_seconds=0.1, overlap=0.5)
    assert frames.shape[1] == int(0.1 * FS)
    assert frames.shape[0] == 19          # 1 s, 0.1 s frames, 50 % overlap


def test_features_over_time_is_steady_for_a_steady_signal():
    out = E.features_over_time(make_sine(), FS, window_seconds=0.05)
    assert out["rms"].std() < 0.01 * out["rms"].mean()
    assert len(out["time"]) == out["n_frames"]


def test_band_energy_finds_the_tone_in_the_right_band():
    sig = make_sine(freq=3000)
    energies = E.band_energy(sig, FS, [(2000, 4000), (8000, 10000)])
    assert energies[(2000.0, 4000.0)] > 100 * energies[(8000.0, 10000.0)]


def test_band_above_nyquist_raises():
    with pytest.raises(ValueError, match="Nyquist"):
        E.band_energy(make_sine(), FS, [(1000, 30_000)])


def test_band_ratio_is_insensitive_to_overall_gain():
    t = np.arange(int(FS)) / FS
    sig = np.sin(2 * np.pi * 500 * t) + np.sin(2 * np.pi * 6000 * t)
    r1 = E.band_ratio(sig, FS, (4000, 8000), (100, 1000))
    r2 = E.band_ratio(sig * 7.0, FS, (4000, 8000), (100, 1000))
    assert r1 == pytest.approx(r2, rel=1e-6)


def test_peak_frequency_and_centroid():
    sig = make_sine(freq=2000)
    assert E.peak_frequency(sig, FS) == pytest.approx(2000, abs=5)
    assert E.spectral_centroid(sig, FS) == pytest.approx(2000, rel=0.1)


def test_remove_offset():
    sig = make_sine(offset=100.0)
    assert F.signal_mean(E.remove_offset(sig)) == pytest.approx(0.0, abs=1e-9)


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
