# Changelog

## 0.1.0 - Initial release

- Headphone mode: binaural rendering of stereo and 5.1 input using a built-in
  spherical-head HRIR model.
- Speaker mode: crosstalk cancellation for stereo speakers, with virtual surround
  for multichannel input.
- Bypass mode for comparison.
- Device discovery with automatic headphone/speaker and Bluetooth detection.
- `render` command for offline file processing (WAV, FLAC).
- `live` command for real-time processing through a loopback/virtual input device.
- Unit tests and GitHub Actions CI on Python 3.10 and 3.12.

## 0.1.1 - Packaging and releases

- Installable package (`pip install .`) with a `spatial-sound` command.
- CLI moved to `spatial/cli.py`; `app.py` is now a thin wrapper.
- Release workflow builds Windows, macOS, and Linux executables and a Python
  package, and attaches them to the GitHub release on each `v*` tag.
