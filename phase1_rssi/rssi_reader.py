#!/usr/bin/env python3
"""WallSense - Aşama 1: Linux ve Windows için sinyal gücü (RSSI) okuyucu.

macOS'taki rssi_reader.swift ile aynı işi yapar: client'ın Wi-Fi kartından
sinyal gücünü okur ve her ölçümü bir satır JSON olarak stdout'a yazar.
server.py hangi okuyucunun çalıştığını bilmez, sadece bu satırları okur.

  Linux:   /proc/net/wireless (boşsa "iw dev <arayüz> link")
  Windows: Native Wi-Fi API (wlanapi.dll), ctypes ile

Kullanım: python3 rssi_reader.py [aralık_ms]   (varsayılan 100 ms = saniyede 10 ölçüm)
Sadece standart Python kütüphanesi kullanır.
"""

import json
import os
import re
import shutil
import subprocess
import sys
import time


def freq_to_channel(mhz: int) -> int:
    if mhz == 2484:
        return 14
    if 2412 <= mhz < 2484:
        return (mhz - 2407) // 5
    if 5150 <= mhz < 5925:
        return (mhz - 5000) // 5
    if 5945 <= mhz <= 7125:
        return (mhz - 5950) // 5
    return -1


# ---------------------------------------------------------------- Linux

class Linux:
    """Çekirdek, bağlı Wi-Fi arayüzünün sinyal seviyesini /proc/net/wireless'ta tutar.
    Bazı yeni sürücüler bu dosyayı doldurmaz; o zaman "iw" aracına soruyoruz."""

    PROC = "/proc/net/wireless"

    def __init__(self):
        # iw bazı dağıtımlarda kullanıcının PATH'inde olmayan /usr/sbin'dedir
        self.iw = shutil.which("iw") or next((p for p in ("/usr/sbin/iw", "/sbin/iw") if os.path.exists(p)), None)
        if not os.path.exists(self.PROC) and not self.iw:
            sys.exit("Wi-Fi arayüzü bulunamadı (/proc/net/wireless ve iw yok)")
        self.iface = None
        self.ch, self.ch_at = -1, 0.0

    def sample(self) -> tuple[int, int, int]:
        rssi, noise = self._proc() or self._iw() or (0, 0)
        if rssi and time.time() >= self.ch_at:  # kanal sık değişmez, 5 sn'de bir sor
            self.ch, self.ch_at = self._channel(), time.time() + 5
        return rssi, noise, self.ch

    def _proc(self):
        """'wlan0: 0000   54.  -56.  -256 ...' satırından (seviye, gürültü) okur."""
        try:
            with open(self.PROC) as f:
                lines = f.read().splitlines()[2:]
        except OSError:
            return None
        for line in lines:
            name, _, rest = line.partition(":")
            p = rest.split()
            if len(p) < 4:
                continue
            # bazı sürücüler değerleri 0-255 aralığında yazar
            level, noise = (v - 256 if v > 0 else v for v in (int(float(p[2])), int(float(p[3]))))
            if level == 0:
                continue
            self.iface = name.strip()
            return level, (noise if -200 < noise < 0 else 0)  # 0 = gürültü bilinmiyor
        return None

    def _run(self, *args) -> str:
        if not self.iw:
            return ""
        try:
            return subprocess.run([self.iw, *args], capture_output=True, text=True, errors="replace",
                                  timeout=2).stdout
        except (OSError, subprocess.SubprocessError):
            return ""

    def _iw(self):
        if self.iface is None:
            m = re.search(r"Interface (\S+)", self._run("dev"))
            if not m:
                return None
            self.iface = m.group(1)
        m = re.search(r"signal:\s*(-\d+)", self._run("dev", self.iface, "link"))
        return (int(m.group(1)), 0) if m else None

    def _channel(self) -> int:
        if self.iface:
            m = re.search(r"freq:\s*(\d+)", self._run("dev", self.iface, "link"))
            if m:
                return freq_to_channel(int(m.group(1)))
        return -1


# ---------------------------------------------------------------- Windows

class Windows:
    """Windows'un Native Wi-Fi API'si bağlı arayüzün RSSI değerini dBm olarak verir."""

    RSSI, CHANNEL = 0x10000102, 8  # WLAN_INTF_OPCODE değerleri
    CONNECTED = 1                  # wlan_interface_state_connected

    def __init__(self):
        import ctypes
        from ctypes import wintypes as w

        class GUID(ctypes.Structure):
            _fields_ = [("a", w.DWORD), ("b", w.WORD), ("c", w.WORD), ("d", ctypes.c_ubyte * 8)]

        class INFO(ctypes.Structure):
            _fields_ = [("guid", GUID), ("desc", ctypes.c_wchar * 256), ("state", ctypes.c_int)]

        class LIST(ctypes.Structure):
            _fields_ = [("n", w.DWORD), ("index", w.DWORD), ("items", INFO * 1)]

        self.c, self.GUID, self.INFO, self.LIST = ctypes, GUID, INFO, LIST
        api = self.api = ctypes.WinDLL("wlanapi.dll")
        api.WlanOpenHandle.argtypes = [w.DWORD, ctypes.c_void_p, ctypes.POINTER(w.DWORD),
                                       ctypes.POINTER(w.HANDLE)]
        api.WlanEnumInterfaces.argtypes = [w.HANDLE, ctypes.c_void_p, ctypes.POINTER(ctypes.POINTER(LIST))]
        api.WlanQueryInterface.argtypes = [w.HANDLE, ctypes.POINTER(GUID), ctypes.c_int, ctypes.c_void_p,
                                           ctypes.POINTER(w.DWORD), ctypes.POINTER(ctypes.c_void_p),
                                           ctypes.c_void_p]
        api.WlanFreeMemory.argtypes = [ctypes.c_void_p]
        api.WlanFreeMemory.restype = None
        for f in (api.WlanOpenHandle, api.WlanEnumInterfaces, api.WlanQueryInterface):
            f.restype = w.DWORD

        self.h, version = w.HANDLE(), w.DWORD()
        if api.WlanOpenHandle(2, None, ctypes.byref(version), ctypes.byref(self.h)) != 0:
            sys.exit("Wi-Fi arayüzü bulunamadı (WLAN AutoConfig hizmeti çalışıyor mu?)")
        self.guid = None

    def _connected(self):
        """Bağlı ilk Wi-Fi arayüzünün kimliğini (GUID) döndürür."""
        c = self.c
        p = c.POINTER(self.LIST)()
        if self.api.WlanEnumInterfaces(self.h, None, c.byref(p)) != 0:
            return None
        try:
            items = c.cast(c.addressof(p.contents) + self.LIST.items.offset, c.POINTER(self.INFO))
            for k in range(p.contents.n):
                if items[k].state == self.CONNECTED:
                    return self.GUID.from_buffer_copy(items[k].guid)
        finally:
            self.api.WlanFreeMemory(p)
        return None

    def _query(self, opcode: int, ctype):
        c = self.c
        size, data = c.c_ulong(), c.c_void_p()
        if self.api.WlanQueryInterface(self.h, c.byref(self.guid), opcode, None,
                                       c.byref(size), c.byref(data), None) != 0:
            return None
        try:
            return c.cast(data, c.POINTER(ctype)).contents.value
        finally:
            self.api.WlanFreeMemory(data)

    def sample(self) -> tuple[int, int, int]:
        if self.guid is None:
            self.guid = self._connected()
            if self.guid is None:
                return 0, 0, -1
        rssi = self._query(self.RSSI, self.c.c_long)
        if rssi is None:  # bağlantı koptu, bir sonraki ölçümde arayüzü yeniden ara
            self.guid = None
            return 0, 0, -1
        ch = self._query(self.CHANNEL, self.c.c_ulong)
        return rssi, 0, (-1 if ch is None else ch)


def main():
    interval_ms = int(sys.argv[1]) if len(sys.argv) > 1 else 100
    if sys.platform.startswith("linux"):
        reader = Linux()
    elif sys.platform == "win32":
        reader = Windows()
    else:
        sys.exit("Bu okuyucu Linux ve Windows içindir. macOS'ta rssi_reader.swift kullanılır.")
    try:
        while True:
            t = time.time()
            rssi, noise, ch = reader.sample()
            # rssi == 0: bağlı değil (Swift okuyucuyla aynı anlam)
            print(json.dumps({"t": t, "rssi": rssi, "noise": noise, "ch": ch}, separators=(",", ":")),
                  flush=True)
            time.sleep(interval_ms / 1000)
    except (KeyboardInterrupt, BrokenPipeError):
        pass


if __name__ == "__main__":
    main()
