"""Audio device discovery and classification (headphones / speakers / Bluetooth)."""
import re
from dataclasses import dataclass


@dataclass
class DeviceInfo:
    index: int
    name: str
    direction: str       # "output" or "input"
    channels: int
    host_api: str
    kind: str            # "headphones", "speakers", or "unknown"
    bluetooth: bool


_BLUETOOTH = [r"bluetooth", r"\bbt\b", r"\bhfp\b", r"airpods", r"\bbuds\b", r"\bwh-",
              r"\bwf-", r"beats", r"jabra", r"soundcore", r"\bbose\b"]
_HEADPHONE = [r"headphone", r"headset", r"earphone", r"earbud", r"earpod", r"airpods",
              r"\bbuds\b", r"\bwh-", r"\bwf-", r"beats", r"jabra", r"soundcore",
              r"\bbose\b", r"\bhfp\b"]
_SPEAKER = [r"speaker", r"hdmi", r"displayport", r"\bdp\b", r"\btv\b", r"soundbar",
            r"receiver", r"theat", r"built-in", r"built in", r"macbook", r"\bmonitor\b",
            r"\bdisplay\b", r"line out"]


def _matches(patterns, text):
    return any(re.search(p, text) for p in patterns)


def classify(name):
    """Return (kind, is_bluetooth) for a device name.

    Name heuristics are not perfect. Use --mode to override them.
    """
    n = name.lower()
    bluetooth = _matches(_BLUETOOTH, n)
    if _matches(_HEADPHONE, n):
        kind = "headphones"
    elif _matches(_SPEAKER, n):
        kind = "speakers"
    else:
        kind = "unknown"
    return kind, bluetooth


def list_devices():
    """Return (outputs, inputs) as lists of DeviceInfo."""
    import sounddevice as sd

    apis = sd.query_hostapis()
    outputs, inputs = [], []
    for idx, d in enumerate(sd.query_devices()):
        api = apis[d["hostapi"]]["name"]
        kind, bt = classify(d["name"])
        if d["max_output_channels"] > 0:
            outputs.append(DeviceInfo(idx, d["name"], "output",
                                      d["max_output_channels"], api, kind, bt))
        if d["max_input_channels"] > 0:
            inputs.append(DeviceInfo(idx, d["name"], "input",
                                     d["max_input_channels"], api, kind, bt))
    return outputs, inputs


def find_device(spec, devices):
    """Resolve a device by index (e.g. '3') or name substring (e.g. 'CABLE Output')."""
    if spec.isdigit():
        for d in devices:
            if d.index == int(spec):
                return d
        raise ValueError(f"no device with index {spec}")
    matches = [d for d in devices if spec.lower() in d.name.lower()]
    if not matches:
        raise ValueError(f"no device name contains '{spec}'")
    return matches[0]
