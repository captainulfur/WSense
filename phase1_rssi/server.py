#!/usr/bin/env python3
"""WallSense - Aşama 1: Mac Wi-Fi sinyal gücü (RSSI) ile hareket algılama.

rssi_reader'ı çalıştırır, gelen ölçümlerden hareket skoru hesaplar,
her şeyi data/ klasörüne CSV olarak kaydeder ve tarayıcıya canlı yayınlar.

Sadece standart Python kütüphanesi kullanır.
"""

import argparse
import csv
import json
import queue
import re
import statistics
import subprocess
import sys
import threading
import time
from collections import deque
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

__version__ = "0.1.0"

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
READER = HERE / "build" / "rssi_reader"
DATA_DIR = ROOT / "data"
VIZ_DIR = ROOT / "viz3d"
ROOM_PATH = ROOT / "config" / "room.json"

# Mac'in ölçtüğü tek hattın adı. 3D sayfadaki "router" ve "mac" cihazlarına karşılık gelir.
LIVE_LINK = "router-mac"

DEFAULT_ROOM = {
    "area": {"w": 8.0, "d": 5.0, "h": 2.7},
    "walls": [{"x1": 4.0, "y1": 0.0, "x2": 4.0, "y2": 3.8}],
    "nodes": [
        {"id": "router", "name": "Router", "type": "router", "x": 1.5, "y": 2.5, "z": 1.0},
        {"id": "mac", "name": "Mac", "type": "mac", "x": 6.5, "y": 2.5, "z": 0.8},
    ],
    "links": [["router", "mac"]],
    "crossing": 0.5,
}


# ---------------------------------------------------------------- oda ayarı

def _num(v, lo, hi) -> float:
    f = float(v)
    if not (lo <= f <= hi):
        raise ValueError(f"{f} değeri {lo}-{hi} aralığında değil")
    return round(f, 3)


def validate_room(obj: dict) -> dict:
    """3D sayfadan gelen oda ayarını kontrol eder ve temizlenmiş halini döndürür."""
    a = obj["area"]
    area = {"w": _num(a["w"], 1, 50), "d": _num(a["d"], 1, 50), "h": _num(a["h"], 1.5, 10)}
    nodes, ids = [], set()
    for n in obj["nodes"][:32]:
        nid = str(n["id"])
        if not re.fullmatch(r"[A-Za-z0-9_-]{1,24}", nid) or nid in ids:
            raise ValueError(f"geçersiz cihaz kimliği: {nid!r}")
        if n["type"] not in ("router", "mac", "esp32"):
            raise ValueError(f"geçersiz cihaz türü: {n['type']!r}")
        ids.add(nid)
        nodes.append({"id": nid, "name": str(n.get("name") or nid)[:24], "type": n["type"],
                      "x": _num(n["x"], 0, area["w"]), "y": _num(n["y"], 0, area["d"]),
                      "z": _num(n["z"], 0, area["h"])})
    if not {"router", "mac"} <= ids:
        raise ValueError("router ve mac cihazları silinemez")
    walls = [{k: _num(w[k], -1, 51) for k in ("x1", "y1", "x2", "y2")} for w in obj.get("walls", [])[:32]]
    links = []
    for pair in obj.get("links", [])[:256]:
        a_id, b_id = str(pair[0]), str(pair[1])
        if a_id in ids and b_id in ids and a_id != b_id:
            links.append([a_id, b_id])
    crossing = _num(obj.get("crossing", 0.5), 0, 1)  # tek hatta insan figürünün yeri (0=router, 1=mac)
    return {"area": area, "walls": walls, "nodes": nodes, "links": links, "crossing": crossing}


def load_room() -> dict:
    try:
        return validate_room(json.loads(ROOM_PATH.read_text()))
    except (OSError, ValueError, KeyError, TypeError, IndexError):
        return json.loads(json.dumps(DEFAULT_ROOM))


def save_room(room: dict):
    ROOM_PATH.parent.mkdir(exist_ok=True)
    ROOM_PATH.write_text(json.dumps(room, ensure_ascii=False, indent=2))


# ---------------------------------------------------------------- algılayıcı

class Detector:
    """Sinyalin kendi normalinden ne kadar saptığını ölçer.

    - taban (baseline): sakin anlardaki son 20 saniyenin medyanı, odanın "boş" hali.
      Hareket varken taban güncellenmez. Böylece hatta duran biri de algılanmaya devam eder.
    - sapma: son 1 saniyenin ortalamasının tabandan farkı (duran kişi bunu yükseltir)
    - dalgalanma: son 2 saniyenin standart sapması (yürüyen kişi bunu yükseltir)
    - skor = sapma + dalgalanma (dBm cinsinden)
    Skor eşiği geçince "hareket var" der ve bunu 1.5 saniye tutar.
    Alarm 60 saniyeden uzun sürerse ortam kalıcı değişmiş sayılır (kapı kapandı, eşya taşındı)
    ve taban yeniden öğrenilir.
    """

    RELEARN_AFTER = 60.0

    def __init__(self, rate_hz: float, threshold: float = 2.0):
        self.rate = rate_hz
        self.buf: deque[int] = deque(maxlen=int(30 * rate_hz))
        self.calm: deque[int] = deque(maxlen=int(20 * rate_hz))
        self.threshold = threshold
        self.hold_until = 0.0
        self.motion_since: float | None = None
        self.calib_until = 0.0
        self.calib_scores: list[float] = []
        self.lock = threading.Lock()

    def _last(self, seconds: float) -> list[int]:
        n = max(1, int(seconds * self.rate))
        return list(self.buf)[-n:]

    def update(self, t: float, rssi: int) -> dict:
        with self.lock:
            self.buf.append(rssi)
            warm = len(self.buf) >= 3 * self.rate
            if len(self.calm) >= 2 * self.rate:
                baseline = statistics.median(self.calm)
            else:
                baseline = statistics.median(self._last(20))
            dev = spread = score = 0.0
            if warm:
                dev = abs(statistics.fmean(self._last(1.0)) - baseline)
                spread = statistics.pstdev(self._last(2.0))
                score = dev + spread

            calibrating = t < self.calib_until
            if calibrating:
                self.calib_scores.append(score)
            elif self.calib_scores:
                self._finish_calibration()

            if warm and not calibrating and score >= self.threshold:
                self.hold_until = t + 1.5
            motion = t < self.hold_until

            if motion:
                if self.motion_since is None:
                    self.motion_since = t
                elif t - self.motion_since > self.RELEARN_AFTER:
                    print("[bilgi] 60 sn'dir alarm var, sakin seviye yeniden öğreniliyor", flush=True)
                    self.calm.clear()
                    self.calm.extend(self._last(5))
                    self.hold_until = 0.0
                    self.motion_since = None
                    motion = False
            else:
                self.motion_since = None
                self.calm.append(rssi)

            # yürüyen kişi sinyali oynatır, duran kişi sabit bir düşüş yaratır
            state = ("walking" if spread >= 0.5 * self.threshold else "standing") if motion else "none"

            return {
                "baseline": round(baseline, 2),
                "score": round(score, 3),
                "dev": round(dev, 3),
                "spread": round(spread, 3),
                "threshold": round(self.threshold, 2),
                "motion": motion,
                "state": state,
                "warm": warm,
                "calibrating": calibrating,
            }

    def start_calibration(self, seconds: float = 10.0):
        with self.lock:
            self.calib_scores = []
            self.calib_until = time.time() + seconds

    def _finish_calibration(self):
        s = self.calib_scores
        self.calib_scores = []
        if len(s) < 5:
            return
        mean = statistics.fmean(s)
        sd = statistics.pstdev(s)
        # Sakin odadaki skorların biraz üstü. Çok düşük eşik sürekli alarm verir.
        # RSSI tam sayı olduğu için 1 dBm'lik oynamalar normal; eşiği 1.5'in altına indirmeyiz.
        self.threshold = round(max(1.5, mean + 3 * sd, max(s) + 0.5), 2)
        print(f"[kalibrasyon] sakin skor ort={mean:.2f} sd={sd:.2f} max={max(s):.2f}"
              f" -> yeni eşik {self.threshold}", flush=True)

    def set_threshold(self, value: float):
        with self.lock:
            self.threshold = max(0.2, min(20.0, value))


# ---------------------------------------------------------------- yayın

class Hub:
    """Ölçümleri tüm bağlı tarayıcılara dağıtır, son 2 dakikayı saklar."""

    def __init__(self):
        self.clients: set[queue.Queue] = set()
        self.history: deque[dict] = deque(maxlen=1200)
        self.lock = threading.Lock()

    def publish(self, msg: dict):
        with self.lock:
            self.history.append(msg)
            for q in list(self.clients):
                try:
                    q.put_nowait(msg)
                except queue.Full:
                    pass

    def subscribe(self) -> tuple[queue.Queue, list[dict]]:
        q: queue.Queue = queue.Queue(maxsize=500)
        with self.lock:
            self.clients.add(q)
            return q, list(self.history)

    def unsubscribe(self, q: queue.Queue):
        with self.lock:
            self.clients.discard(q)


# ---------------------------------------------------------------- uygulama

class App:
    def __init__(self, interval_ms: int, threshold: float, ping: bool,
                 replay: Path | None = None, replay_from: float = 0.0):
        self.interval_ms = interval_ms
        self.replay = replay
        self.replay_from = replay_from
        self.detector = Detector(1000 / interval_ms, threshold)
        self.hub = Hub()
        self.ping_enabled = ping and replay is None
        self.gateway = None
        self.procs: list[subprocess.Popen] = []
        self.pending_mark: str | None = None
        self.mark_lock = threading.Lock()
        self.info = {"channel": None, "noise": None}

        # Tekrar oynatırken yeni kayıt dosyası açılmaz
        self.csv_path = self.csv_file = self.csv = None
        if replay is None:
            DATA_DIR.mkdir(exist_ok=True)
            self.csv_path = DATA_DIR / f"rssi-{datetime.now():%Y%m%d-%H%M%S}.csv"
            self.csv_file = open(self.csv_path, "w", newline="")
            self.csv = csv.writer(self.csv_file)
            self.csv.writerow(["t", "rssi", "noise", "channel", "baseline", "score",
                               "threshold", "motion", "mark"])

    def mark(self, label: str):
        with self.mark_lock:
            self.pending_mark = label[:40] or "işaret"

    def _take_mark(self) -> str:
        with self.mark_lock:
            m, self.pending_mark = self.pending_mark, None
            return m or ""

    def start(self):
        if self.replay is not None:
            threading.Thread(target=self._replay_loop, daemon=True).start()
            return
        if not READER.exists():
            sys.exit("rssi_reader derlenmemiş. Projeyi ./run.sh ile başlatın.")
        if self.ping_enabled:
            self._start_ping()
        reader = subprocess.Popen([str(READER), str(self.interval_ms)],
                                  stdout=subprocess.PIPE, text=True, bufsize=1)
        self.procs.append(reader)
        threading.Thread(target=self._read_loop, args=(reader,), daemon=True).start()

    def _start_ping(self):
        """Router'a sürekli küçük ping atar. Trafik olunca Mac RSSI'ı daha sık günceller."""
        try:
            out = subprocess.run(["route", "-n", "get", "default"],
                                 capture_output=True, text=True, timeout=5).stdout
            for line in out.splitlines():
                if "gateway:" in line:
                    self.gateway = line.split(":", 1)[1].strip()
        except Exception:
            pass
        if not self.gateway:
            print("[uyarı] router adresi bulunamadı, ping kapalı", flush=True)
            return
        print(f"[bilgi] router {self.gateway} adresine saniyede 10 ping atılıyor", flush=True)
        self.procs.append(subprocess.Popen(
            ["ping", "-i", "0.1", "-q", self.gateway],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL))

    def _ingest(self, s: dict, recorded_mark: str = "") -> dict | None:
        """Tek bir ölçümü algılayıcıdan geçirir ve tarayıcılara yayınlar."""
        if s["rssi"] == 0:  # Wi-Fi bağlı değil
            self.hub.publish({"t": s["t"], "disconnected": True})
            return None
        self.info = {"channel": s["ch"], "noise": s["noise"]}
        d = self.detector.update(s["t"], s["rssi"])
        mark = self._take_mark() or recorded_mark
        msg = {"t": s["t"], "link": LIVE_LINK, "rssi": s["rssi"], "noise": s["noise"],
               "ch": s["ch"], "mark": mark, **d}
        self.hub.publish(msg)
        return msg

    def _read_loop(self, proc: subprocess.Popen):
        rows = 0
        for line in proc.stdout:
            try:
                s = json.loads(line)
            except json.JSONDecodeError:
                continue
            msg = self._ingest(s)
            if msg is None:
                continue
            self.csv.writerow([f"{s['t']:.3f}", s["rssi"], s["noise"], s["ch"],
                               msg["baseline"], msg["score"], msg["threshold"],
                               int(msg["motion"]), msg["mark"]])
            rows += 1
            if rows % 20 == 0:
                self.csv_file.flush()
        print("[hata] rssi_reader durdu", flush=True)

    def _replay_loop(self):
        """Kayıtlı bir oturumu (data/*.csv) gerçek hızında, canlıymış gibi oynatır.

        Algılayıcı her şeyi yeniden hesaplar; CSV'den sadece ham ölçüm ve işaretler alınır.
        Dosya bitince baştan başlar.
        """
        rows = load_replay(self.replay, self.replay_from)
        print(f"[bilgi] tekrar oynatılıyor: {rows_label(self.replay)}, "
              f"{len(rows)} ölçüm, {rows[-1]['t'] - rows[0]['t']:.0f} sn", flush=True)
        while True:
            start, t0 = time.time(), rows[0]["t"]
            for r in rows:
                wait = start + (r["t"] - t0) - time.time()
                if wait > 0:
                    time.sleep(wait)
                self._ingest({**r, "t": start + (r["t"] - t0)}, r["mark"])
            print("[bilgi] kayıt bitti, baştan oynatılıyor", flush=True)

    def stop(self):
        for p in self.procs:
            p.terminate()
        if self.csv_file:
            self.csv_file.close()


def rows_label(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return path.name


def load_replay(path: Path, start_s: float = 0.0) -> list[dict]:
    """Kayıt CSV'sini okur. start_s: kaydın kaçıncı saniyesinden başlanacağı."""
    rows = []
    with open(path, newline="") as f:
        for r in csv.DictReader(f):
            try:
                rows.append({"t": float(r["t"]), "rssi": int(r["rssi"]), "noise": int(r["noise"]),
                             "ch": int(r["channel"]), "mark": r.get("mark") or ""})
            except (KeyError, TypeError, ValueError):
                continue
    if rows:
        first = rows[0]["t"]
        rows = [r for r in rows if r["t"] - first >= start_s]
    if len(rows) < 2:
        sys.exit(f"{path}: oynatılacak ölçüm yok")
    return rows


def make_handler(app: App):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def _json(self, obj, code=200):
            body = json.dumps(obj).encode()
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _file(self, path: Path, ctype: str):
            try:
                body = path.read_bytes()
            except OSError:
                return self.send_error(404)
            self.send_response(200)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-cache")
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            path = urlparse(self.path).path
            if path == "/":
                self._file(HERE / "index.html", "text/html; charset=utf-8")
            elif path in ("/3d", "/3d/"):
                self._file(VIZ_DIR / "room3d.html", "text/html; charset=utf-8")
            elif path.startswith("/viz3d/"):
                name = path[len("/viz3d/"):]
                types = {".js": "text/javascript; charset=utf-8", ".html": "text/html; charset=utf-8"}
                ext = Path(name).suffix
                if re.fullmatch(r"[A-Za-z0-9_.-]+", name) and ext in types:
                    self._file(VIZ_DIR / name, types[ext])
                else:
                    self.send_error(404)
            elif path == "/api/room":
                self._json({"room": load_room()})
            elif path == "/events":
                self._events()
            elif path == "/api/info":
                self._json({"gateway": app.gateway,
                            "csv": str(app.csv_path.relative_to(ROOT)) if app.csv_path else None,
                            "replay": rows_label(app.replay) if app.replay else None,
                            "rate_hz": app.detector.rate, **app.info})
            else:
                self.send_error(404)

        def do_POST(self):
            u = urlparse(self.path)
            qs = parse_qs(u.query)
            if u.path == "/api/calibrate":
                app.detector.start_calibration(10)
                self._json({"ok": True, "seconds": 10})
            elif u.path == "/api/threshold":
                try:
                    app.detector.set_threshold(float(qs["value"][0]))
                except (KeyError, ValueError):
                    return self._json({"ok": False}, 400)
                self._json({"ok": True, "threshold": app.detector.threshold})
            elif u.path == "/api/mark":
                app.mark(qs.get("label", ["işaret"])[0])
                self._json({"ok": True})
            elif u.path == "/api/room":
                try:
                    length = int(self.headers.get("Content-Length", 0))
                    if length > 64_000:
                        raise ValueError("ayar çok büyük")
                    room = validate_room(json.loads(self.rfile.read(length)))
                except (ValueError, KeyError, TypeError, IndexError) as e:
                    return self._json({"ok": False, "error": str(e)}, 400)
                save_room(room)
                self._json({"ok": True, "room": room})
            else:
                self.send_error(404)

        def _events(self):
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Cache-Control", "no-cache")
            self.end_headers()
            q, history = app.hub.subscribe()
            try:
                self.wfile.write(f"event: history\ndata: {json.dumps(history)}\n\n".encode())
                self.wfile.flush()
                while True:
                    try:
                        msg = q.get(timeout=5)
                        self.wfile.write(f"data: {json.dumps(msg)}\n\n".encode())
                    except queue.Empty:
                        self.wfile.write(b": canli\n\n")
                    self.wfile.flush()
            except (BrokenPipeError, ConnectionResetError):
                pass
            finally:
                app.hub.unsubscribe(q)

    return Handler


def main():
    ap = argparse.ArgumentParser(description="WallSense Aşama 1 - RSSI hareket algılama")
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--interval-ms", type=int, default=100, help="ölçüm aralığı (ms)")
    ap.add_argument("--threshold", type=float, default=2.0, help="başlangıç eşiği (dBm)")
    ap.add_argument("--no-ping", action="store_true", help="router'a ping atma")
    ap.add_argument("--open", action="store_true", help="tarayıcıda aç")
    ap.add_argument("--replay", type=Path, metavar="CSV",
                    help="Wi-Fi yerine kayıtlı bir oturumu (data/*.csv) oynat")
    ap.add_argument("--replay-from", type=float, default=0.0, metavar="SN",
                    help="kaydın kaçıncı saniyesinden başlansın")
    args = ap.parse_args()
    if args.replay and not args.replay.exists():
        ap.error(f"dosya yok: {args.replay}")

    app = App(args.interval_ms, args.threshold, not args.no_ping, args.replay, args.replay_from)
    app.start()
    server = ThreadingHTTPServer(("127.0.0.1", args.port), make_handler(app))
    server.daemon_threads = True
    url = f"http://127.0.0.1:{args.port}"
    print(f"[bilgi] WallSense {__version__} çalışıyor: {url}", flush=True)
    if app.csv_path:
        print(f"[bilgi] kayıt dosyası: {app.csv_path.relative_to(ROOT)}", flush=True)
    if args.open:
        subprocess.Popen(["open", url])
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        app.stop()


if __name__ == "__main__":
    main()
