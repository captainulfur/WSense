# Changelog

## Unreleased

### Added
- `--replay <csv>` and `--replay-from <seconds>`: play a recorded session from `data/` through the same detector in real time, instead of live Wi-Fi. No compile step, no ping, no new log file; loops at the end. Recorded marks are shown on the chart.
- `run.sh` skips compiling the Swift reader when `--replay` is given, so replay works on any OS with Python 3.10+.

## 0.1.0 (2026-11-19): first public prototype

Early prototype. Works with a single signal link (router ↔ Mac) and cannot locate a person yet.

### Added
- Mac Wi-Fi signal strength (RSSI) reader using CoreWLAN, ~10 samples per second.
- Motion detection: calm level, deviation + fluctuation score, calibration, walking vs. standing.
- Calm level is frozen during motion, so a person standing still keeps being detected; relearned after 60 s of continuous alarm.
- Live 2D chart with threshold control and manual marks.
- CSV logging of every session in `data/`.
- 3D floor plan (three.js): editable room, walls and devices; link glows on motion; animated human figure.
- Radio tomographic imaging engine (`viz3d/rti.js`) and a simulation mode with 6 virtual ESP32s.
- Turkish and English UI.

### Not included yet
- ESP32 / CSI hardware support.
- Real position estimation (needs at least 3 links).
