"""
signal_processing — feature extraction for the ThermaTank leak-detection system.

Two modules:
    features.py  — the required deliverable (mean, max peak, RMS, std, FFT,
                   plus the three-channel wrapper). Stable; review this one
                   against the task brief.
    extras.py    — optional exploratory features (windowing, band energy,
                   spectral descriptors). Not part of the brief; safe to
                   change or drop without affecting `features`.

`extras` imports from `features`, never the reverse.
"""

from . import features  # noqa: F401
from . import extras  # noqa: F401

__version__ = "0.1.0"
