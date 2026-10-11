"""High-level processor: picks the right chain for the output device."""
import numpy as np

from .render import BinauralRenderer, CrosstalkCanceller

MODES = ("headphones", "speakers", "bypass")


def _layout(n_channels, spread_deg):
    """Virtual speaker azimuths and LFE index for a given input channel count."""
    if n_channels == 1:
        return {0: 0.0}, None
    if n_channels < 6:
        return {0: -spread_deg, 1: spread_deg}, None
    # 5.1 in SMPTE order: FL, FR, FC, LFE, BL, BR
    return {0: -spread_deg, 1: spread_deg, 2: 0.0, 4: -110.0, 5: 110.0}, 3


def _to_stereo(x):
    if x.shape[1] == 1:
        return np.repeat(x, 2, axis=1)
    return x[:, :2]


def resolve_mode(output_kind):
    """Map a detected device kind to a processing mode."""
    if output_kind == "speakers":
        return "speakers"
    return "headphones"   # headphones and unknown devices


class SpatialProcessor:
    """Stateful, block-based processor.

    headphones : sources -> binaural -> ears (headphone output)
    speakers   : sources -> binaural -> crosstalk cancellation -> speakers
                 (stereo input skips the binaural stage and goes straight to CTC)
    bypass     : pass the first two channels through unchanged
    """

    def __init__(self, mode, in_channels, fs=48000, spread_deg=30.0):
        if mode not in MODES:
            raise ValueError(f"mode must be one of {MODES}")
        self.mode = mode
        self.in_channels = in_channels
        self.fs = fs
        self.latency_samples = 0
        self._binaural = None
        self._ctc = None

        azimuths, lfe = _layout(in_channels, spread_deg)
        if mode == "headphones":
            self._binaural = BinauralRenderer(azimuths, fs, lfe_channel=lfe)
        elif mode == "speakers":
            self._ctc = CrosstalkCanceller(fs, speaker_angle=spread_deg)
            self.latency_samples = self._ctc.latency_samples
            if in_channels > 2:
                self._binaural = BinauralRenderer(azimuths, fs, lfe_channel=lfe)

    def process(self, x):
        """x: (frames, channels) float array -> (frames, 2) output."""
        x = np.asarray(x, dtype=np.float64)
        if x.ndim == 1:
            x = x[:, None]

        if self.mode == "bypass":
            return np.clip(_to_stereo(x), -1.0, 1.0)

        if self.mode == "headphones":
            return np.clip(self._binaural.process(x), -1.0, 1.0)

        ears = self._binaural.process(x) if self._binaural else _to_stereo(x)
        return np.clip(self._ctc.process(ears), -1.0, 1.0)
