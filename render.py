"""Signal-processing building blocks.

StreamingFIR          - block-by-block FIR filter (keeps state between blocks)
BinauralRenderer      - places each input channel at a virtual direction, renders to 2 ears
CrosstalkCanceller    - turns an ear-signal pair into loudspeaker feeds so each ear
                        hears only its own channel
"""
import numpy as np

from .hrir import synthetic_hrir


class StreamingFIR:
    """Causal FIR filter that can be fed audio in arbitrary block sizes."""

    def __init__(self, taps):
        self.taps = np.asarray(taps, dtype=np.float64)
        self._hist = np.zeros(len(self.taps) - 1)

    def process(self, x):
        x = np.asarray(x, dtype=np.float64)
        if self._hist.size:
            ext = np.concatenate([self._hist, x])
            y = np.convolve(ext, self.taps, mode="valid")
            self._hist = ext[-self._hist.size:]
        else:
            y = np.convolve(x, self.taps, mode="valid")
        return y


class BinauralRenderer:
    """Renders multichannel audio to two ears using HRIRs.

    `azimuths` maps channel index -> virtual speaker azimuth in degrees.
    `lfe_channel` (optional) is mixed into both ears without spatialisation,
    since bass localisation is weak anyway.
    """

    def __init__(self, azimuths, fs, hrir_len=128, lfe_channel=None, lfe_gain=0.7):
        self.lfe_channel = lfe_channel
        self.lfe_gain = lfe_gain
        self._filters = {}
        for ch, az in azimuths.items():
            hl, hr = synthetic_hrir(az, fs, hrir_len)
            self._filters[ch] = (StreamingFIR(hl), StreamingFIR(hr))

    def process(self, x):
        """x: (frames, channels) -> (frames, 2) ear signals."""
        out = np.zeros((x.shape[0], 2))
        for ch, (f_left, f_right) in self._filters.items():
            out[:, 0] += f_left.process(x[:, ch])
            out[:, 1] += f_right.process(x[:, ch])
        if self.lfe_channel is not None:
            out += self.lfe_gain * x[:, [self.lfe_channel]]
        return out


class CrosstalkCanceller:
    """Stereo crosstalk cancellation for two loudspeakers at +/- speaker_angle.

    Each speaker reaches both ears. The 2x2 speaker-to-ear plant is inverted
    per frequency with Tikhonov regularisation (so the inverse stays bounded
    where the plant is nearly singular, i.e. at low frequencies), then the
    inverse is converted to short FIR filters.
    """

    def __init__(self, fs, speaker_angle=30.0, hrir_len=128, filter_len=256,
                 nfft=2048, regularisation=0.01):
        if filter_len > nfft:
            raise ValueError("filter_len must not exceed nfft")

        h_left_spk = synthetic_hrir(-speaker_angle, fs, hrir_len)
        h_right_spk = synthetic_hrir(speaker_angle, fs, hrir_len)

        # plant[ear, speaker, n]
        plant = np.zeros((2, 2, hrir_len))
        plant[0, 0] = h_left_spk[0]    # left ear  <- left speaker
        plant[0, 1] = h_right_spk[0]   # left ear  <- right speaker
        plant[1, 0] = h_left_spk[1]    # right ear <- left speaker
        plant[1, 1] = h_right_spk[1]   # right ear <- right speaker

        P = np.moveaxis(np.fft.rfft(plant, n=nfft, axis=-1), -1, 0)   # (F, ear, spk)
        PH = np.conj(np.transpose(P, (0, 2, 1)))                      # (F, spk, ear)
        inv = np.linalg.inv(P @ PH + regularisation * np.eye(2))
        C = PH @ inv                                                  # (F, spk, ear)

        c = np.fft.irfft(np.moveaxis(C, 0, -1), n=nfft, axis=-1)      # (spk, ear, nfft)
        # Shift so the non-causal part of the inverse is kept, then truncate.
        c = np.roll(c, filter_len // 2, axis=-1)[..., :filter_len]
        fade = np.ones(filter_len)
        n_fade = filter_len // 4
        fade[-n_fade:] = 0.5 * (1 + np.cos(np.linspace(0, np.pi, n_fade)))
        c = c * fade

        self.latency_samples = filter_len // 2
        self._filters = [[StreamingFIR(c[s, e]) for e in range(2)] for s in range(2)]

    def process(self, ears):
        """ears: (frames, 2) desired ear signals -> (frames, 2) speaker feeds."""
        out = np.zeros((ears.shape[0], 2))
        for s in range(2):
            for e in range(2):
                out[:, s] += self._filters[s][e].process(ears[:, e])
        return out
