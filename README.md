# Spatial Sound

Spatial audio processing for headphones, earphones, earbuds, laptop/desktop
speakers, TV speakers and home-theatre setups, over wired or Bluetooth outputs.

## How it works

| Output device              | Mode         | Processing chain                                        |
|----------------------------|--------------|---------------------------------------------------------|
| Wired / Bluetooth headphones, earbuds | `headphones` | sources placed at virtual directions → HRIR binaural rendering → ears |
| Laptop / TV / soundbar / home-theatre speakers | `speakers` | sources → binaural → crosstalk cancellation → speakers |
| Anything                   | `bypass`     | pass-through (for A/B comparison)                       |

Input can be a file (`render`) or system audio via a loopback device (`live`).

## Download

Get the latest release from the [Releases page](https://github.com/Sathwik20075/spatial-audio/releases/latest).

| Platform | File |
|---|---|
| Windows (64-bit) | [spatial-sound-windows.exe](https://github.com/Sathwik20075/spatial-audio/releases/latest/download/spatial-sound-windows.exe) |
| macOS | [spatial-sound-macos](https://github.com/Sathwik20075/spatial-audio/releases/latest/download/spatial-sound-macos) |
| Linux (x86-64) | [spatial-sound-linux](https://github.com/Sathwik20075/spatial-audio/releases/latest/download/spatial-sound-linux) |
| Python package | `pip install spatial-sound` (from the release's `.whl` or `.tar.gz`) |

Executables need no Python installation. They are not code-signed yet, so
Windows SmartScreen and macOS Gatekeeper may warn you the first time. Choose
"Run anyway" (Windows) or right-click → Open (macOS). On Linux, install PortAudio
first: `sudo apt install libportaudio2`. macOS binaries are for Intel and Apple
silicon through Rosetta; no native arm64 build is provided yet.

## Install

```bash
pip install -r requirements.txt
python3 tests/test_spatial.py     # run the tests
pip install .                      # install the spatial-sound command
spatial-sound devices            # list outputs and inputs, with detected kind and Bluetooth flag
```

On Linux, `sounddevice` needs PortAudio (`sudo apt install libportaudio2`).

## Offline use (no setup needed)

```bash
spatial-sound render movie_track.wav out.wav --mode headphones
spatial-sound render movie_track.wav out.wav --mode speakers --spread 30
```

## Real-time system audio

Live mode reads from a loopback/virtual input and plays to your chosen output.
Set the OS default output to the virtual device, then route it to the real device.

**Windows**
1. Install VB-CABLE (free, vb-audio.com).
2. Set Windows' default playback device to "CABLE Input".
3. Run:
   ```
   spatial-sound live --input "CABLE Output" --output "Headphones" --mode auto
   ```
   Use `--output "Speakers"`, `--output "TV"` or a Bluetooth device name as needed.

**macOS**
1. Install BlackHole 2ch.
2. Set the system output to BlackHole.
3. Run `spatial-sound live --input "BlackHole" --output "AirPods" --mode auto`.
   Grant microphone permission when prompted. macOS requires this for any input device.

**Linux (PipeWire or PulseAudio)**
1. Create a virtual sink: `pactl load-module module-null-sink sink_name=spatial`
2. Make it the default output (`pactl set-default-sink spatial`).
3. Run `spatial-sound devices` and use the input named like "Monitor of spatial".
   Then run `spatial-sound live --input "Monitor of spatial" --output "<your device>"`.

Press Enter to stop.

## Choosing a mode

* `--mode auto` picks `headphones` or `speakers` from the output device name.
  If the name is unclear, it falls back to `headphones` and prints a warning. Set `--mode` explicitly if that is wrong.
* Headphones: a wider virtual stage with `--spread 45` can feel more open.
* Speakers: sit centred between the speakers, which should be about 30° from your seat each side.
  Crosstalk cancellation works best in that sweet spot and in a quiet room.

## Bluetooth notes

* Bluetooth codecs add latency (typically 100–200 ms) that this app cannot remove.
  Music is fine. Video will lip-sync badly, so use wired output for film or games.
* Use `--blocksize 1024` if you hear crackling on Bluetooth.
* Some earbuds (AirPods, Galaxy Buds) support only a low-quality hands-free profile when the mic is active.
  If the sound quality drops sharply, check whether the device is in "call" mode.

## Project layout

```
app.py                  CLI: devices, render, live
spatial/hrir.py         HRIR generation (spherical-head model, no dataset needed)
spatial/render.py       Streaming FIR, binaural renderer, crosstalk canceller
spatial/processor.py    Chooses the chain for headphones / speakers / bypass
spatial/devices.py      Device discovery and classification (wired, Bluetooth, kind)
spatial/live.py         Real-time duplex stream loop
tests/test_spatial.py   Unit tests
```

## Limitations (be aware before relying on it)

* **HRIRs are synthetic.** The built-in model gives left/right direction (ITD and ILD)
  but no reliable front/back or height cues. Localisation is approximate. The best
  upgrade is a loader for measured HRIRs (SOFA format: SADIE II, MIT KEMAR, or CIPIC),
  which would plug into `synthetic_hrir`. Check the dataset's licence before distribution.
* **Multichannel on speakers** is virtualised with crosstalk cancellation, not discrete
  surround. Results depend on room and speaker placement. For real home theatre, the
  receiver's own decoding is usually better; use this app for stereo or headphones.
* **Crosstalk cancellation** is sensitive to listener position and speaker placement, and
  it weakens at low frequencies.
* **Head tracking** is not included. Bluetooth earbuds usually do not expose their sensors.
* **Latency** is about 3 ms of processing plus whatever the OS and device add.
* **iOS and Android** cannot process system audio from third-party apps this way.
  Those would need a separate native app.

## Next steps

1. Add a SOFA/HRIR loader and let the user choose a measured dataset.
2. Add per-device profiles (save the mode and spread for each named device).
3. Build a small GUI (Qt or a web UI) on top of `SpatialProcessor`.
4. Add head tracking through a webcam (face-landmark yaw) or supported sensors.

## License

MIT. See [LICENSE](LICENSE).
