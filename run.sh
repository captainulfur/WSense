#!/bin/bash
# WallSense Aşama 1'i başlatır: okuyucuyu (gerekirse) derler ve sunucuyu açar.
# Kullanım: ./run.sh [--open] [--no-ping] [--threshold 2.5] [--port 8765]
#           ./run.sh --replay data/rssi-....csv   (Wi-Fi yerine kayıtlı oturumu oynatır, derleme gerekmez)
set -euo pipefail
cd "$(dirname "$0")"

REPLAY=0
for a in "$@"; do
  case "$a" in --replay|--replay=*) REPLAY=1 ;; esac
done

SRC=phase1_rssi/rssi_reader.swift
BIN=phase1_rssi/build/rssi_reader
if [ "$REPLAY" = 0 ] && { [ ! -x "$BIN" ] || [ "$SRC" -nt "$BIN" ]; }; then
  mkdir -p phase1_rssi/build
  echo "[bilgi] RSSI okuyucu derleniyor..."
  swiftc -O "$SRC" -o "$BIN"
fi

exec python3 phase1_rssi/server.py "$@"
