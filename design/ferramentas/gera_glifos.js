// Gera os glifos dos cinco sólidos a partir da MESMA geometria do motor da cena (src/espaco3d.js).
// Cada glifo é a projeção ortográfica do sólido: contorno (casco convexo) + arestas das faces da frente.
// Uso: node design/ferramentas/gera_glifos.js   → escreve design/solidos.svg
// Não há dependência: só a biblioteca padrão do Node.
const fs = require('fs'), path = require('path'), vm = require('vm');
const RAIZ = path.resolve(__dirname, '..', '..');
const ctx = { window: {} };
vm.runInNewContext(fs.readFileSync(path.join(RAIZ, 'src', 'espaco3d.js'), 'utf8'), ctx);
const SOL = ctx.window.Espaco3D.SOL;

// Vista de cada sólido, escolhida para a silhueta ser inconfundível a 16 px:
//   icosa  — de frente para uma face (eixo de ordem 3): hexágono com um triângulo no centro
//   cubo   — pela diagonal do corpo (isométrica): hexágono com o "Y" das três faces
//   tetra  — de frente para um vértice: triângulo com as três arestas encontrando-se no centro
//   octa   — levemente girado: losango com o equador aparente
//   dodeca — de frente para uma face (eixo de ordem 5): decágono com o pentágono no centro
const r3 = 1 / Math.sqrt(3);
const VISTA = {
  icosa: { para: S => S.n[0] },
  cubo: { para: () => [r3, r3, r3] },
  tetra: { para: S => S.v[0] },
  octa: { euler: [12, 24, 0] },
  dodeca: { para: S => S.n[0] }
};
const NOME = { icosa: 'Cibernética — icosaedro', cubo: 'Regulação — cubo', tetra: 'Política industrial — tetraedro', octa: 'Complexidade — octaedro', dodeca: 'A nota — dodecaedro' };

function euler(v, a) {
  const r = a.map(g => g * Math.PI / 180); let [x, y, z] = v, t;
  t = y * Math.cos(r[0]) - z * Math.sin(r[0]); z = y * Math.sin(r[0]) + z * Math.cos(r[0]); y = t;      // x
  t = x * Math.cos(r[1]) + z * Math.sin(r[1]); z = -x * Math.sin(r[1]) + z * Math.cos(r[1]); x = t;     // y
  t = x * Math.cos(r[2]) - y * Math.sin(r[2]); y = x * Math.sin(r[2]) + y * Math.cos(r[2]); x = t;      // z
  return [x, y, z];
}
// rotação (Rodrigues) que leva a direção d para o eixo z, isto é, para o olho de quem vê
function alinhador(d) {
  const n = Math.hypot(d[0], d[1], d[2]), u = [d[0] / n, d[1] / n, d[2] / n];
  const k = [u[1], -u[0], 0], s = Math.hypot(k[0], k[1]), c = u[2];
  if (s < 1e-9) return v => v.slice();
  const e = [k[0] / s, k[1] / s, 0];
  return v => {
    const cx = [e[1] * v[2] - e[2] * v[1], e[2] * v[0] - e[0] * v[2], e[0] * v[1] - e[1] * v[0]], pe = e[0] * v[0] + e[1] * v[1] + e[2] * v[2];
    return [0, 1, 2].map(i => v[i] * c + cx[i] * s + e[i] * pe * (1 - c));
  };
}
// vista completa: alinha e depois gira no plano para um vértice do contorno apontar para cima
function vista(S, cfg) {
  if (cfg.euler) return v => euler(v, cfg.euler);
  const al = alinhador(cfg.para(S)), ps = S.v.map(al);
  let m = 0; for (let i = 1; i < ps.length; i++) if (Math.hypot(ps[i][0], ps[i][1]) > Math.hypot(ps[m][0], ps[m][1]) + 1e-9) m = i;
  const g = Math.PI / 2 - Math.atan2(ps[m][1], ps[m][0]), cg = Math.cos(g), sg = Math.sin(g);
  return v => { const q = al(v); return [q[0] * cg - q[1] * sg, q[0] * sg + q[1] * cg, q[2]]; };
}
function casco(ps) {                                   // cadeia monótona
  const p = ps.map((q, i) => [q[0], q[1], i]).sort((a, b) => a[0] - b[0] || a[1] - b[1]);
  const cz = (o, a, b) => (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0]);
  const lo = [], up = [];
  for (const q of p) { while (lo.length >= 2 && cz(lo[lo.length - 2], lo[lo.length - 1], q) <= 1e-9) lo.pop(); lo.push(q); }
  for (const q of p.slice().reverse()) { while (up.length >= 2 && cz(up[up.length - 2], up[up.length - 1], q) <= 1e-9) up.pop(); up.push(q); }
  return lo.slice(0, -1).concat(up.slice(0, -1));
}
const n2 = x => (Math.round(x * 100) / 100).toString();

let simbolos = '';
for (const k of Object.keys(VISTA)) {
  const S = SOL[k], R = vista(S, VISTA[k]), v = S.v.map(R);
  const frente = S.f.filter((f, i) => R(S.n[i])[2] > 1e-6);
  const arestas = new Map();
  for (const f of frente) for (let i = 0; i < f.length; i++) { const a = f[i], b = f[(i + 1) % f.length]; arestas.set(a < b ? a + '-' + b : b + '-' + a, [a, b]); }
  // enquadra em 20×20, centrado em (12,12); y da tela cresce para baixo
  const xs = v.map(p => p[0]), ys = v.map(p => -p[1]);
  const mnx = Math.min(...xs), mxx = Math.max(...xs), mny = Math.min(...ys), mxy = Math.max(...ys);
  const e = 20 / Math.max(mxx - mnx, mxy - mny), ox = 12 - e * (mnx + mxx) / 2, oy = 12 - e * (mny + mxy) / 2;
  const P = v.map(p => [ox + e * p[0], oy - e * p[1]]);
  const h = casco(P);
  const dCasco = 'M' + h.map(q => n2(q[0]) + ' ' + n2(q[1])).join('L') + 'Z';
  const noCasco = new Set(h.map(q => q[2]));
  let dLin = '';
  for (const [a, b] of arestas.values()) {
    // aresta que coincide com o contorno já está desenhada pelo casco
    const ia = h.findIndex(q => q[2] === a), ib = h.findIndex(q => q[2] === b);
    if (noCasco.has(a) && noCasco.has(b) && (Math.abs(ia - ib) === 1 || Math.abs(ia - ib) === h.length - 1)) continue;
    dLin += 'M' + n2(P[a][0]) + ' ' + n2(P[a][1]) + 'L' + n2(P[b][0]) + ' ' + n2(P[b][1]);
  }
  simbolos += `  <symbol id="sd-sol-${k}" viewBox="0 0 24 24"><title>${NOME[k]}</title>` +
    `<path d="${dCasco}" fill="var(--sol-fundo,none)" stroke="currentColor" stroke-width="var(--sol-traco,1.5)" stroke-linejoin="round"/>` +
    `<path d="${dLin}" fill="none" stroke="var(--sol-linha,currentColor)" stroke-width="var(--sol-traco-dentro,1.1)" stroke-linecap="round"/></symbol>\n`;
}
const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="0" height="0" style="position:absolute" aria-hidden="true" focusable="false">\n` +
  `  <!-- Gerado por design/ferramentas/gera_glifos.js a partir de src/espaco3d.js. Não editar à mão. -->\n` + simbolos + `</svg>\n`;
fs.writeFileSync(path.join(RAIZ, 'design', 'solidos.svg'), svg);
console.log('design/solidos.svg:', Buffer.byteLength(svg), 'bytes;', Object.keys(VISTA).length, 'símbolos');
