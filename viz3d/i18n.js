// WallSense - dil desteği (Türkçe / English)
//
// Kullanım:
//   HTML:  <span data-i18n="anahtar"></span>, <p data-i18n-html="anahtar"></p>, <button data-i18n-title="anahtar">
//   JS:    t("anahtar", { degisken: 1 })
// Seçilen dil tarayıcıda hatırlanır (localStorage).

const STORE_KEY = "wallsense.lang";

export const DICT = {
  tr: {
    // ortak durumlar
    "st.waiting": "Bekleniyor",
    "st.warming": "Isınıyor…",
    "st.calibrating": "Kalibre ediliyor…",
    "st.motion": "HAREKET VAR",
    "st.calm": "Sakin",
    "st.nodata": "Veri yok",
    "pct": "%{v}",

    // 2D sayfa
    "p2.subtitle": "Aşama 1: Mac Wi-Fi sinyal gücü",
    "p2.link3d": "3D görünüm",
    "connecting": "bağlanıyor…",
    "card.status": "Durum",
    "card.signal": "Sinyal (RSSI)",
    "card.baseline": "Sakin seviye",
    "card.score": "Hareket skoru / eşik",
    "chart.rssi": "Sinyal gücü, son 60 saniye",
    "chart.score": "Hareket skoru (eşiği geçince alarm)",
    "lg.rssi": "RSSI",
    "lg.base": "sakin seviye",
    "lg.motion": "hareket",
    "lg.mark": "işaret",
    "axis.now": "şimdi",
    "btn.calibrate": "Sakinken kalibre et (10 sn)",
    "btn.mark": "Şimdi yürüdüm (işaretle)",
    "lbl.threshold": "Eşik:",
    "p2.hint": "Router odanın dışında, Mac odanın içinde olsun. Önce kimse hareket etmezken <b>kalibre et</b>'e basın. Sonra biri router ile oda arasından geçsin ve tam geçtiği anda <b>işaretle</b>'ye basın. Turuncu çizgiler kırmızı alanlarla çakışıyorsa sistem hareketi yakalıyor demektir.",
    "banner.nowifi": "Wi-Fi bağlı görünmüyor.",
    "banner.lost": "Sunucuya bağlantı koptu. ./run.sh çalışıyor mu?",
    "info.router": "router {v}",
    "info.channel": "kanal {v}",
    "info.rate": "{v} ölçüm/sn",
    "info.log": "kayıt: {v}",

    // 3D sayfa
    "p3.help": "Fareyle döndür, tekerlekle yakınlaştır.",
    "p3.back2d": "2D grafiğe dön",
    "hud.state": "Durum:",
    "mode.live": "Canlı veri",
    "mode.sim": "Simülasyon",
    "badge.live": "Canlı veri",
    "badge.sim": "SİMÜLASYON: sanal ESP32'ler ve sanal kişi",
    "note.live": "Evinizden gelen gerçek ölçüm. Şu an tek hat (Router–Mac) var: hat kırmızılaşırsa üzerinde hareket var demektir.",
    "note.sim": "Gerçek veri değil. ESP32'lerle kurulunca sistemin nasıl görüneceğini gösterir. Yeşil kafes gerçek konum, turuncu figür sistemin tahmini.",
    "sec.area": "Alan (metre)",
    "area.w": "Genişlik (x)",
    "area.d": "Derinlik (y)",
    "area.h": "Yükseklik",
    "sec.nodes": "Cihazlar",
    "btn.addNode": "+ ESP32 ekle",
    "sec.walls": "Duvarlar",
    "btn.addWall": "+ Duvar ekle",
    "sec.links": "Sinyal hatları",
    "btn.autoLinks": "Hatları otomatik oluştur",
    "note.links": "Router–Mac hattı şu an canlı veri alıyor. ESP32 hatları kartlar bağlanınca veri alacak.",
    "links.count": "{n} hat: {list}",
    "links.one": "1 hat: {list}",
    "links.none": "Hat yok",
    "sec.figure": "İnsan figürü (tek hat)",
    "figure.q": "Biri hattan geçince figür nerede görünsün?",
    "note.figure": "Tek hatla kişinin hat üzerindeki yeri ölçülemez. Figürü insanların genelde geçtiği yere (kapı, koridor) koyun. Kaydırınca figür 2 saniye önizlenir.",
    "btn.save": "Kaydet",
    "btn.reset": "Kayıtlıya dön",
    "saved": "Kaydedildi",
    "saveErr": "Hata: {v}",
    "f.name": "Ad",
    "f.type": "Tür",
    "f.height": "yükseklik",
    "f.pick": "Haritada yerini seç",
    "f.delete": "Sil",
    "pick.hint": "{name}: haritada bir noktaya tıklayın",
    "sim.node": "Sanal {i}",
    "detail.simErr": "Tahmin hatası: {v} m",
    "detail.noPerson": "Kişi algılanmadı",
    "detail.waitLive": "Canlı veri bekleniyor (./run.sh çalışıyor mu?)",
    "detail.single": "Tek hat: skor {s} / eşik {t}. Konum için en az 3 hat gerekir.",
    "detail.walking": "Router–Mac hattında biri yürüyor. Figürün hat üzerindeki yeri temsili.",
    "detail.standing": "Router–Mac hattında biri duruyor. Figürün hat üzerindeki yeri temsili.",
    "detail.pos": "Tahmini konum: x {x} m, y {y} m",
  },

  en: {
    "st.waiting": "Waiting",
    "st.warming": "Warming up…",
    "st.calibrating": "Calibrating…",
    "st.motion": "MOTION",
    "st.calm": "Calm",
    "st.nodata": "No data",
    "pct": "{v}%",

    "p2.subtitle": "Phase 1: Mac Wi-Fi signal strength",
    "p2.link3d": "3D view",
    "connecting": "connecting…",
    "card.status": "Status",
    "card.signal": "Signal (RSSI)",
    "card.baseline": "Calm level",
    "card.score": "Motion score / threshold",
    "chart.rssi": "Signal strength, last 60 seconds",
    "chart.score": "Motion score (alarm above threshold)",
    "lg.rssi": "RSSI",
    "lg.base": "calm level",
    "lg.motion": "motion",
    "lg.mark": "mark",
    "axis.now": "now",
    "btn.calibrate": "Calibrate while still (10 s)",
    "btn.mark": "I just walked (mark)",
    "lbl.threshold": "Threshold:",
    "p2.hint": "Put the router outside the room and the Mac inside it. First press <b>calibrate</b> while nobody is moving. Then have someone walk between the router and the room, and press <b>mark</b> right as they pass. If the orange lines line up with the red areas, the system is catching the motion.",
    "banner.nowifi": "Wi-Fi does not seem to be connected.",
    "banner.lost": "Lost connection to the server. Is ./run.sh running?",
    "info.router": "router {v}",
    "info.channel": "channel {v}",
    "info.rate": "{v} samples/s",
    "info.log": "log: {v}",

    "p3.help": "Drag to rotate, scroll to zoom.",
    "p3.back2d": "Back to 2D chart",
    "hud.state": "Status:",
    "mode.live": "Live data",
    "mode.sim": "Simulation",
    "badge.live": "Live data",
    "badge.sim": "SIMULATION: virtual ESP32s and a virtual person",
    "note.live": "Real measurements from your home. Right now there is a single link (Router–Mac): when it turns red, something is moving on it.",
    "note.sim": "Not real data. Shows how the system will look once ESP32s are set up. The green wireframe is the true position, the orange figure is the system's estimate.",
    "sec.area": "Area (meters)",
    "area.w": "Width (x)",
    "area.d": "Depth (y)",
    "area.h": "Height",
    "sec.nodes": "Devices",
    "btn.addNode": "+ Add ESP32",
    "sec.walls": "Walls",
    "btn.addWall": "+ Add wall",
    "sec.links": "Signal links",
    "btn.autoLinks": "Generate links automatically",
    "note.links": "The Router–Mac link is receiving live data now. ESP32 links will get data once the boards are connected.",
    "links.count": "{n} links: {list}",
    "links.one": "1 link: {list}",
    "links.none": "No links",
    "sec.figure": "Human figure (single link)",
    "figure.q": "Where should the figure appear when someone crosses the link?",
    "note.figure": "A single link cannot measure where on the link the person is. Place the figure where people usually cross (a door or hallway). Moving the slider previews the figure for 2 seconds.",
    "btn.save": "Save",
    "btn.reset": "Revert to saved",
    "saved": "Saved",
    "saveErr": "Error: {v}",
    "f.name": "Name",
    "f.type": "Type",
    "f.height": "height",
    "f.pick": "Pick position on the map",
    "f.delete": "Delete",
    "pick.hint": "{name}: click a point on the map",
    "sim.node": "Virtual {i}",
    "detail.simErr": "Estimate error: {v} m",
    "detail.noPerson": "No person detected",
    "detail.waitLive": "Waiting for live data (is ./run.sh running?)",
    "detail.single": "Single link: score {s} / threshold {t}. Position needs at least 3 links.",
    "detail.walking": "Someone is walking on the Router–Mac link. The figure's spot on the link is illustrative.",
    "detail.standing": "Someone is standing on the Router–Mac link. The figure's spot on the link is illustrative.",
    "detail.pos": "Estimated position: x {x} m, y {y} m",
  },
};

function detect() {
  try {
    const s = localStorage.getItem(STORE_KEY);
    if (s && DICT[s]) return s;
  } catch { /* depolama kapalı olabilir */ }
  return (navigator.language || "").toLowerCase().startsWith("tr") ? "tr" : "en";
}

let lang = detect();
const listeners = new Set();

export const getLang = () => lang;

export function t(key, vars = {}) {
  const s = DICT[lang][key] ?? DICT.tr[key] ?? key;
  return s.replace(/\{(\w+)\}/g, (_, k) => (vars[k] ?? ""));
}

export function applyI18n(root = document) {
  document.documentElement.lang = lang;
  root.querySelectorAll("[data-i18n]").forEach(el => { el.textContent = t(el.dataset.i18n); });
  root.querySelectorAll("[data-i18n-html]").forEach(el => { el.innerHTML = t(el.dataset.i18nHtml); });
  root.querySelectorAll("[data-i18n-title]").forEach(el => { el.title = t(el.dataset.i18nTitle); });
}

export function onLangChange(fn) { listeners.add(fn); }

export function setLang(l) {
  if (!DICT[l] || l === lang) return;
  lang = l;
  try { localStorage.setItem(STORE_KEY, l); } catch { /* yoksay */ }
  applyI18n();
  syncToggles();
  listeners.forEach(fn => fn(l));
}

/** el içine TR | EN düğmelerini koyar. */
export function mountLangToggle(el) {
  el.classList.add("langtoggle");
  el.setAttribute("role", "group");
  el.setAttribute("aria-label", "Language / Dil");
  for (const l of ["tr", "en"]) {
    const b = document.createElement("button");
    b.type = "button";
    b.dataset.lang = l;
    b.textContent = l.toUpperCase();
    b.onclick = () => setLang(l);
    el.append(b);
  }
  syncToggles();
}

function syncToggles() {
  document.querySelectorAll(".langtoggle button").forEach(b => {
    const on = b.dataset.lang === lang;
    b.classList.toggle("on", on);
    b.setAttribute("aria-pressed", String(on));
  });
}
