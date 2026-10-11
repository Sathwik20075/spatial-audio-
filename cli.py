"""Spatial sound for headphones and speakers.

Examples:
  python app.py devices
  python app.py render input.wav output.wav --mode headphones
  python app.py live --input "CABLE Output" --output "Headphones" --mode auto
"""
import argparse
import sys

import numpy as np

from spatial.devices import find_device, list_devices
from spatial.processor import MODES, SpatialProcessor, resolve_mode

BLOCK = 1024


def cmd_devices(_args):
    outputs, inputs = list_devices()
    print("OUTPUT devices (where audio plays):")
    for d in outputs:
        bt = " [bluetooth]" if d.bluetooth else ""
        print(f"  [{d.index:>3}] {d.name}  ({d.host_api}, {d.channels}ch) -> {d.kind}{bt}")
    print("\nINPUT devices (loopback / virtual cables, used for live mode):")
    for d in inputs:
        print(f"  [{d.index:>3}] {d.name}  ({d.host_api}, {d.channels}ch)")


def cmd_render(args):
    import soundfile as sf

    with sf.SoundFile(args.input) as src:
        fs, ch = src.samplerate, src.channels
        proc = SpatialProcessor(args.mode, ch, fs, args.spread)
        with sf.SoundFile(args.output, "w", samplerate=fs, channels=2,
                          subtype="PCM_24") as dst:
            while True:
                block = src.read(BLOCK, dtype="float64", always_2d=True)
                if block.shape[0] == 0:
                    break
                dst.write(proc.process(block))
            # Flush filter tails so the last samples are not cut off.
            dst.write(proc.process(np.zeros((512, ch))))
    print(f"Wrote {args.output} ({args.mode}, {ch} ch in, {fs} Hz)")


def cmd_live(args):
    from spatial.live import run_live

    outputs, inputs = list_devices()
    in_dev = find_device(args.input, inputs)
    out_dev = find_device(args.output, outputs)

    mode = args.mode
    if mode == "auto":
        mode = resolve_mode(out_dev.kind)
        if out_dev.kind == "unknown":
            print("Warning: could not tell whether the output is headphones or speakers; "
                  "using headphones mode. Override with --mode.", file=sys.stderr)
    channels = args.channels or min(in_dev.channels, 6)
    print(f"Input : [{in_dev.index}] {in_dev.name} ({channels} ch used)")
    print(f"Output: [{out_dev.index}] {out_dev.name} ({out_dev.kind}"
          f"{', bluetooth' if out_dev.bluetooth else ''})")
    run_live(in_dev.index, out_dev.index, mode, args.rate, args.blocksize,
             channels, args.spread)


def build_parser():
    p = argparse.ArgumentParser(description="Spatial sound for headphones and speakers.")
    sub = p.add_subparsers(dest="command", required=True)

    sub.add_parser("devices", help="list audio devices").set_defaults(func=cmd_devices)

    r = sub.add_parser("render", help="process a WAV/FLAC file offline")
    r.add_argument("input")
    r.add_argument("output")
    r.add_argument("--mode", choices=MODES, default="headphones")
    r.add_argument("--spread", type=float, default=30.0,
                   help="virtual/real speaker half-angle in degrees (default 30)")
    r.set_defaults(func=cmd_render)

    lv = sub.add_parser("live", help="process system audio in real time")
    lv.add_argument("--input", required=True,
                    help="loopback/virtual input device (index or name part)")
    lv.add_argument("--output", required=True,
                    help="real output device: headphones, speakers, TV, Bluetooth")
    lv.add_argument("--mode", choices=("auto",) + MODES, default="auto")
    lv.add_argument("--rate", type=int, default=48000)
    lv.add_argument("--blocksize", type=int, default=512,
                    help="frames per block; raise to 1024 for Bluetooth stability")
    lv.add_argument("--channels", type=int, default=None,
                    help="input channels to use (default: device max, up to 6)")
    lv.add_argument("--spread", type=float, default=30.0)
    lv.set_defaults(func=cmd_live)
    return p


def main():
    args = build_parser().parse_args()
    try:
        args.func(args)
    except (ValueError, RuntimeError) as exc:
        sys.exit(f"error: {exc}")


if __name__ == "__main__":
    main()
