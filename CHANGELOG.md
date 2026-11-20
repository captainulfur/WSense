# Changelog

## 0.2.0 (2026-11-20): any client

The device that measures the signal is now called the **client**: any Wi-Fi computer running WallSense, not only a Mac.

### Added
- `phase1_rssi/rssi_reader.py`: RSSI reader for **Linux** (`/proc/net/wireless`, falls back to `iw`) and **Windows** (Native Wi-Fi API via ctypes). Same JSON lines as the Swift reader. Experimental: not tested in a real home yet.
- `server.py` picks the reader for the client's OS, finds the router address on macOS, Linux and Windows, and adapts the ping command.
- `--replay <csv>` and `--replay-from <seconds>`: play a recorded session from `data/` through the same detector in real time, instead of live Wi-Fi. No compile step, no ping, no new log file; loops at the end. Recorded marks are shown on the chart.
- `run.sh` compiles the Swift reader only on macOS, and skips it when `--replay` is given.

### Changed
- The "Mac" device is now "Client" everywhere (UI, `config/room.json`, link name `router-client`). A saved 0.1 `config/room.json` needs its `"mac"` id renamed to `"client"`.
- `--open` uses Python's `webbrowser`, so it works on every OS.
- CSV logs and the room file are always read and written as UTF-8.

## 0.1.0 (2026-11-19): first public prototype

Early prototype. Works with a single signal link (router ↔ client, macOS reader only) and cannot locate a person yet.

### Added
- Wi-Fi signal strength (RSSI) reader for macOS using CoreWLAN, ~10 samples per second.
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
