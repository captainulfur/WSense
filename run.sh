#!/bin/bash
# WallSense Aşama 1'i başlatır: okuyucuyu (gerekirse) derler ve sunucuyu açar.
# Kullanım: ./run.sh [--open] [--no-ping] [--threshold 2.5] [--port 8765]
set -euo pipefail
cd "$(dirname "$0")"

SRC=phase1_rssi/rssi_reader.swift
BIN=phase1_rssi/build/rssi_reader
mkdir -p phase1_rssi/build
if [ ! -x "$BIN" ] || [ "$SRC" -nt "$BIN" ]; then
  echo "[bilgi] RSSI okuyucu derleniyor..."
  swiftc -O "$SRC" -o "$BIN"
fi

exec python3 phase1_rssi/server.py "$@"
