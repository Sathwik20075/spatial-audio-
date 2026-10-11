"""Real-time loop: loopback/virtual input -> spatial processing -> output device."""
import sys

import numpy as np

from .processor import SpatialProcessor


def run_live(in_index, out_index, mode, fs, blocksize, in_channels, spread_deg):
    import sounddevice as sd

    proc = SpatialProcessor(mode, in_channels, fs, spread_deg)

    def callback(indata, outdata, frames, time, status):
        if status:
            print(f"audio status: {status}", file=sys.stderr)
        outdata[:] = proc.process(indata.astype(np.float64)).astype(np.float32)

    with sd.Stream(device=(in_index, out_index), samplerate=fs, blocksize=blocksize,
                   channels=(in_channels, 2), dtype="float32", callback=callback):
        print(f"Running in '{mode}' mode (latency ~{proc.latency_samples / fs * 1000:.1f} ms "
              f"from processing). Press Enter to stop.")
        input()
