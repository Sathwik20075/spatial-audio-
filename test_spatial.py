import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from spatial.devices import classify                      # noqa: E402
from spatial.hrir import synthetic_hrir                   # noqa: E402
from spatial.processor import SpatialProcessor            # noqa: E402
from spatial.render import CrosstalkCanceller, StreamingFIR  # noqa: E402

FS = 48000


def test_itd_points_to_source_side():
    hl, hr = synthetic_hrir(60, FS)
    assert np.argmax(np.abs(hr)) < np.argmax(np.abs(hl))


def test_ild_louder_at_near_ear():
    hl, hr = synthetic_hrir(60, FS)
    assert np.sum(hr ** 2) > np.sum(hl ** 2)
    hl, hr = synthetic_hrir(-60, FS)
    assert np.sum(hl ** 2) > np.sum(hr ** 2)


def test_streaming_fir_matches_full_convolution():
    rng = np.random.default_rng(0)
    x = rng.standard_normal(5000)
    h = rng.standard_normal(64)
    f = StreamingFIR(h)
    y = np.concatenate([f.process(x[i:i + 317]) for i in range(0, len(x), 317)])
    assert np.allclose(y, np.convolve(x, h)[:len(x)])


def test_crosstalk_cancellation_reduces_leakage():
    ctc = CrosstalkCanceller(FS, speaker_angle=30)
    impulse = np.zeros((4096, 2))
    impulse[0, 1] = 1.0                       # signal for the right ear only
    spk = ctc.process(impulse)

    hL = synthetic_hrir(-30, FS)
    hR = synthetic_hrir(30, FS)
    ear_left = np.convolve(spk[:, 0], hL[0]) + np.convolve(spk[:, 1], hR[0])
    ear_right = np.convolve(spk[:, 0], hL[1]) + np.convolve(spk[:, 1], hR[1])

    energy = lambda v: float(np.sum(v ** 2))  # noqa: E731
    ratio_with = energy(ear_left) / energy(ear_right)
    ratio_without = energy(hR[0]) / energy(hR[1])
    assert ratio_with < 0.5 * ratio_without


def test_processor_output_shape_all_layouts():
    rng = np.random.default_rng(1)
    for ch in (1, 2, 6):
        for mode in ("headphones", "speakers", "bypass"):
            p = SpatialProcessor(mode, ch, FS)
            out = p.process(rng.standard_normal((512, ch)) * 0.1)
            assert out.shape == (512, 2)
            assert np.all(np.isfinite(out))


def test_processor_is_block_size_independent():
    rng = np.random.default_rng(2)
    x = rng.standard_normal((4096, 6)) * 0.1
    full = SpatialProcessor("headphones", 6, FS).process(x)
    p = SpatialProcessor("headphones", 6, FS)
    chunks = np.concatenate([p.process(x[i:i + 256]) for i in range(0, len(x), 256)])
    assert np.allclose(full, chunks)


def test_device_classification():
    assert classify("Headphones (Bluetooth)") == ("headphones", True)
    assert classify("AirPods Pro") == ("headphones", True)
    assert classify("Speakers (Realtek)") == ("speakers", False)
    assert classify("Samsung Q80 HDMI")[0] == "speakers"
    assert classify("Bluetooth Speaker") == ("speakers", True)
    assert classify("Mystery device")[0] == "unknown"


if __name__ == "__main__":
    tests = [v for k, v in dict(globals()).items() if k.startswith("test_")]
    for t in tests:
        t()
        print("PASS", t.__name__)
    print(f"{len(tests)} tests passed")
