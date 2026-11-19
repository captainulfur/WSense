// WallSense - Radyo Tomografisi (RTI)
//
// Fikir: Alanı küçük karelere (hücre) böleriz. Her sinyal hattı (iki cihaz arası),
// iki cihazı odak kabul eden ince bir elips içindeki hücrelerden etkilenir.
// Bir hat "bozulduğunda" (hareket skoru yükseldiğinde) o elipsin içindeki
// hücrelere puan veririz. Birden çok bozulan hattın kesiştiği yer, kişinin
// bulunduğu yer olur.
//
// Tek hatta kesişim olmadığı için sadece "bu hat üzerinde bir yerde" diyebiliriz.

export function linkKey(a, b) {
  return `${a}-${b}`;
}

export class RTI {
  /**
   * @param {{w:number,d:number}} area  metre cinsinden alan (x: genişlik, y: derinlik)
   * @param {Array<{id:string,x:number,y:number}>} nodes
   * @param {Array<[string,string]>} links
   * @param {{cell?:number, lambda?:number}} opts
   *   cell: hücre boyu (m), lambda: elips kalınlığı (m)
   */
  constructor(area, nodes, links, opts = {}) {
    this.cell = opts.cell ?? 0.2;
    this.lambda = opts.lambda ?? 0.3;
    this.nx = Math.max(1, Math.ceil(area.w / this.cell));
    this.ny = Math.max(1, Math.ceil(area.d / this.cell));
    const N = this.nx * this.ny;
    const byId = Object.fromEntries(nodes.map(n => [n.id, n]));

    this.links = [];
    for (const [ia, ib] of links) {
      const a = byId[ia], b = byId[ib];
      if (!a || !b) continue;
      const dab = Math.hypot(a.x - b.x, a.y - b.y);
      if (dab < 0.1) continue;
      const cells = [], ws = [];
      for (let j = 0; j < this.ny; j++) {
        const cy = (j + 0.5) * this.cell;
        for (let i = 0; i < this.nx; i++) {
          const cx = (i + 0.5) * this.cell;
          // fazla yol: hücre üzerinden gitmek düz yoldan ne kadar uzun?
          const excess = Math.hypot(cx - a.x, cy - a.y) + Math.hypot(cx - b.x, cy - b.y) - dab;
          if (excess < this.lambda) {
            cells.push(j * this.nx + i);
            ws.push(1 - excess / this.lambda); // hatta yakın hücre daha çok etkilenir
          }
        }
      }
      this.links.push({ id: linkKey(ia, ib), rid: linkKey(ib, ia), a, b,
                        cells: Int32Array.from(cells), ws: Float32Array.from(ws) });
    }
    this.image = new Float32Array(N);
    this.cov = new Float32Array(N);
  }

  /** values: Map(linkId -> değer). 0 = sakin, 1 = eşikte, >1 = güçlü hareket. */
  reconstruct(values) {
    const img = this.image, cov = this.cov;
    img.fill(0); cov.fill(0);
    let used = 0;
    for (const L of this.links) {
      const v = values.get(L.id) ?? values.get(L.rid);
      if (v == null) continue;
      used++;
      for (let k = 0; k < L.cells.length; k++) {
        const c = L.cells[k], w = L.ws[k];
        img[c] += v * w;
        cov[c] += w;
      }
    }
    // Her hücre: üzerinden geçen hatların ağırlıklı ortalaması.
    // +0.3, az hattın geçtiği hücrelerin abartılmasını engeller.
    for (let i = 0; i < img.length; i++) img[i] = cov[i] > 0 ? img[i] / (cov[i] + 0.3) : 0;
    this.usedLinks = used;
    return img;
  }

  /** En güçlü bölgenin ağırlık merkezi. Yeterince güçlü bir tepe yoksa null. */
  estimate(img, minPeak = 0.9) {
    let max = 0;
    for (let i = 0; i < img.length; i++) if (img[i] > max) max = img[i];
    if (max < minPeak) return null;
    const cut = max * 0.75;
    let sx = 0, sy = 0, sw = 0;
    for (let j = 0; j < this.ny; j++) {
      for (let i = 0; i < this.nx; i++) {
        const v = img[j * this.nx + i];
        if (v < cut) continue;
        const w = v - cut;
        sx += (i + 0.5) * this.cell * w;
        sy += (j + 0.5) * this.cell * w;
        sw += w;
      }
    }
    return sw > 0 ? { x: sx / sw, y: sy / sw, peak: max } : null;
  }
}
