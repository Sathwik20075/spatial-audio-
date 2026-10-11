"""Head-related impulse responses (HRIRs).

Built-in HRIRs come from a simple spherical-head model:
  * Woodworth formula for interaural time difference (ITD)
  * Frequency-dependent head shadow for interaural level difference (ILD)

This needs no datasets, but it has no elevation or front/back cues, so
localisation is approximate. For better results, replace `synthetic_hrir`
with a loader for measured HRIR sets (SOFA files such as SADIE II or MIT KEMAR).
"""
import numpy as np
from scipy.signal import lfilter

HEAD_RADIUS_M = 0.0875
SPEED_OF_SOUND = 343.0
MAX_ILD_DB = 8.0


def _fractional_delay(delay_samples, length, half_width=16):
    """Windowed-sinc impulse that delays a signal by `delay_samples`."""
    n = np.arange(length) - delay_samples
    window = np.where(np.abs(n) < half_width,
                      0.5 + 0.5 * np.cos(np.pi * n / half_width), 0.0)
    return np.sinc(n) * window


def itd_seconds(azimuth_rad):
    """Woodworth interaural time difference (magnitude)."""
    theta = np.clip(np.abs(azimuth_rad), 0.0, np.pi / 2)
    return HEAD_RADIUS_M / SPEED_OF_SOUND * (theta + np.sin(theta))


def synthetic_hrir(azimuth_deg, fs=48000, length=128):
    """Return a (2, length) array [left_ear, right_ear] for a source at
    `azimuth_deg` (0 = front, positive = right, +/-90 = sides)."""
    az = np.deg2rad(azimuth_deg)
    side = abs(np.sin(az))
    delay = itd_seconds(az) * fs

    near = np.zeros(length)
    near[0] = 1.0

    # The far ear is delayed, quieter and duller (head shadow).
    cutoff = 20000.0 - 18500.0 * side
    a = np.exp(-2 * np.pi * cutoff / fs)
    gain = 10 ** (-MAX_ILD_DB * side / 20)
    far = gain * lfilter([1 - a], [1, -a], _fractional_delay(delay, length))

    if azimuth_deg >= 0:          # source on the right: right ear is near
        return np.stack([far, near])
    return np.stack([near, far])
