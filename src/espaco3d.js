/* =========================================================================
   Espaço 3D — cena navegável em Canvas 2D. Sem dependências, sem WebGL, sem rede.

   A posição de cada obra é a MISTURA da sua cocitação entre quatro tradições
   (coordenadas baricêntricas num tetraedro regular). É regra, não física: nada
   aqui é layout de forças. Depois da regra, as obras são afastadas no máximo
   TETO_AFASTA (% da aresta) só para não se interpenetrarem.

   Forma = tradição (repete a cor, para a leitura não depender dela):
     icosaedro = cibernética · cubo = regulação · tetraedro = política industrial
     octaedro = complexidade · dodecaedro = a nota (lista de referências)
   Cheio = rótulo observado · vazado = rótulo inferido da vizinhança.

   Canvas 2D em vez de WebGL de propósito: funciona em máquina sem aceleração
   gráfica e em rede restrita, que é onde este sítio precisa abrir.
   ========================================================================= */
(function (global) {
  'use strict';

  var TAU = Math.PI * 2;
  var A = 100;                                   // aresta do tetraedro (unidade da cena)
  var H = A * Math.sqrt(2 / 3);                  // altura
  var RB = A / Math.sqrt(3);                     // raio da base
  var TETO_AFASTA = 5;                           // afastamento máximo, em % da aresta
  var QUEDA = 90;                                // distância entre os dois andares (lente da origem)
  var ANO0 = 1972, ESC_ANO = 2.15;               // lente do tempo: x = (ano - ANO0) * ESC_ANO
  var RAIA = [-36, -12, 12, 36];                 // raias da lente do tempo (z)
  var ALT_MIX = 60;                              // altura que corresponde a 100% fora da própria tradição
  var NOME = ['Cibernética', 'Regulação', 'Política industrial', 'Complexidade'];
  var FORMA = ['icosa', 'cubo', 'tetra', 'octa'];
  var COR = [[75, 63, 194], [26, 122, 94], [184, 92, 16], [42, 157, 143]];
  var PAPEL = [245, 242, 237], TINTA = [14, 14, 14], NEUTRO = [107, 101, 96];
  var N_TOM = 6, N_NEB = 5, NEB = [0, 0.13, 0.27, 0.42, 0.58];
  var FOV = 0.66, PIT0 = -0.12, PIT1 = 1.45, DIST0 = 62, DIST1 = 640;

  function g2r(g) { return g * Math.PI / 180; }
  var VERT = [
    [RB * Math.cos(g2r(210)), -H / 4, RB * Math.sin(g2r(210))],
    [RB * Math.cos(g2r(330)), -H / 4, RB * Math.sin(g2r(330))],
    [RB * Math.cos(g2r(90)), -H / 4, RB * Math.sin(g2r(90))],
    [0, 3 * H / 4, 0]
  ];
  var AR_TETRA = [[0, 1], [1, 2], [2, 0], [0, 3], [1, 3], [2, 3]];

  // ───────────────────────── sólidos ─────────────────────────
  function cruz(a, b) { return [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]]; }
  function solido(vs, fs) {
    var v = [], i, j, r;
    for (i = 0; i < vs.length; i++) {
      r = Math.sqrt(vs[i][0] * vs[i][0] + vs[i][1] * vs[i][1] + vs[i][2] * vs[i][2]) || 1;
      v.push([vs[i][0] / r, vs[i][1] / r, vs[i][2] / r]);
    }
    var faces = [], normais = [];
    for (i = 0; i < fs.length; i++) {
      var f = fs[i].slice(), a = v[f[0]], b = v[f[1]], c = v[f[2]];
      var n = cruz([b[0] - a[0], b[1] - a[1], b[2] - a[2]], [c[0] - a[0], c[1] - a[1], c[2] - a[2]]);
      var cx = 0, cy = 0, cz = 0;
      for (j = 0; j < f.length; j++) { cx += v[f[j]][0]; cy += v[f[j]][1]; cz += v[f[j]][2]; }
      if (n[0] * cx + n[1] * cy + n[2] * cz < 0) { f.reverse(); n = [-n[0], -n[1], -n[2]]; }   // face para fora
      r = Math.sqrt(n[0] * n[0] + n[1] * n[1] + n[2] * n[2]) || 1;
      faces.push(f); normais.push([n[0] / r, n[1] / r, n[2] / r]);
    }
    return { v: v, f: faces, n: normais };
  }
  function dual(S) {                              // dodecaedro = dual do icosaedro
    var centros = S.f.map(function (f) {
      var x = 0, y = 0, z = 0;
      f.forEach(function (i) { x += S.v[i][0]; y += S.v[i][1]; z += S.v[i][2]; });
      return [x, y, z];
    });
    var faces = S.v.map(function (p, vi) {
      var ad = [];
      S.f.forEach(function (f, fi) { if (f.indexOf(vi) >= 0) ad.push(fi); });
      var e1 = cruz(p, Math.abs(p[0]) < 0.9 ? [1, 0, 0] : [0, 1, 0]);
      var e2 = cruz(p, e1);
      var ang = function (c) {
        return Math.atan2(c[0] * e2[0] + c[1] * e2[1] + c[2] * e2[2], c[0] * e1[0] + c[1] * e1[1] + c[2] * e1[2]);
      };
      return ad.sort(function (x, y) { return ang(centros[x]) - ang(centros[y]); });
    });
    return solido(centros, faces);
  }
  var PHI = (1 + Math.sqrt(5)) / 2;
  var SOL = {
    tetra: solido([[1, 1, 1], [1, -1, -1], [-1, 1, -1], [-1, -1, 1]], [[0, 1, 2], [0, 3, 1], [0, 2, 3], [1, 3, 2]]),
    cubo: solido([[-1, -1, -1], [1, -1, -1], [-1, 1, -1], [1, 1, -1], [-1, -1, 1], [1, -1, 1], [-1, 1, 1], [1, 1, 1]],
      [[0, 1, 3, 2], [4, 5, 7, 6], [0, 2, 6, 4], [1, 3, 7, 5], [0, 1, 5, 4], [2, 3, 7, 6]]),
    octa: solido([[1, 0, 0], [-1, 0, 0], [0, 1, 0], [0, -1, 0], [0, 0, 1], [0, 0, -1]],
      [[0, 2, 4], [0, 4, 3], [0, 3, 5], [0, 5, 2], [1, 4, 2], [1, 3, 4], [1, 5, 3], [1, 2, 5]]),
    icosa: solido([[-1, PHI, 0], [1, PHI, 0], [-1, -PHI, 0], [1, -PHI, 0], [0, -1, PHI], [0, 1, PHI],
      [0, -1, -PHI], [0, 1, -PHI], [PHI, 0, -1], [PHI, 0, 1], [-PHI, 0, -1], [-PHI, 0, 1]],
      [[0, 11, 5], [0, 5, 1], [0, 1, 7], [0, 7, 10], [0, 10, 11], [1, 5, 9], [5, 11, 4], [11, 10, 2], [10, 7, 6], [7, 1, 8],
        [3, 9, 4], [3, 4, 2], [3, 2, 6], [3, 6, 8], [3, 8, 9], [4, 9, 5], [2, 4, 11], [6, 2, 10], [8, 6, 7], [9, 8, 1]])
  };
  SOL.dodeca = dual(SOL.icosa);

  // ───────────────────────── utilidades ─────────────────────────
  function ruido(i, k) { var x = Math.sin(i * 127.1 + k * 311.7) * 43758.5453; return x - Math.floor(x); }
  function limita(v, a, b) { return v < a ? a : v > b ? b : v; }
  function mistura(c1, c2, t) { return [c1[0] + (c2[0] - c1[0]) * t, c1[1] + (c2[1] - c1[1]) * t, c1[2] + (c2[2] - c1[2]) * t]; }
  function css(c, a) {
    var s = Math.round(c[0]) + ',' + Math.round(c[1]) + ',' + Math.round(c[2]);
    return (a == null || a >= 1) ? 'rgb(' + s + ')' : 'rgba(' + s + ',' + a + ')';
  }
  function gira3(v, a, b, c) {
    var x = v[0], y = v[1], z = v[2], t;
    var ca = Math.cos(a), sa = Math.sin(a); t = y * ca - z * sa; z = y * sa + z * ca; y = t;
    var cb = Math.cos(b), sb = Math.sin(b); t = x * cb + z * sb; z = -x * sb + z * cb; x = t;
    var cc = Math.cos(c), sc = Math.sin(c); t = x * cc - y * sc; y = x * sc + y * cc; x = t;
    return [x, y, z];
  }
  // tabela de tons: TOM[grupo][neblina][tom]; grupos 0-3 = tradições, 4 = sem tradição, 5 = a nota
  var LUZ = (function () { var l = [-0.45, 0.78, -0.43], r = Math.sqrt(l[0] * l[0] + l[1] * l[1] + l[2] * l[2]); return [l[0] / r, l[1] / r, l[2] / r]; })();
  var BASES = COR.concat([NEUTRO, [38, 36, 34]]);
  var TOM = [], VAZ = [], TRACO = [];
  BASES.forEach(function (c, g) {
    TOM[g] = []; VAZ[g] = []; TRACO[g] = [];
    var escuro = mistura(c, [0, 0, 0], 0.36), claro = mistura(c, [255, 255, 255], 0.42);
    for (var nb = 0; nb < N_NEB; nb++) {
      TOM[g][nb] = []; VAZ[g][nb] = [];
      for (var t = 0; t < N_TOM; t++) {
        var k = t / (N_TOM - 1);
        TOM[g][nb][t] = css(mistura(mistura(escuro, claro, k), PAPEL, NEB[nb]));
        VAZ[g][nb][t] = css(mistura(mistura(PAPEL, c, 0.20 - 0.14 * k), PAPEL, NEB[nb]));
      }
      TRACO[g][nb] = css(mistura(c, PAPEL, NEB[nb]));
    }
  });

  // ───────────────────────── a cena ─────────────────────────
  function criarCena(canvas, D, opt) {
    opt = opt || {};
    var ctx = canvas.getContext('2d');
    var mini = !!opt.mini;
    var N = D.nos.length, i;
    var mq = global.matchMedia ? global.matchMedia('(prefers-reduced-motion: reduce)') : null;
    var reduz = !!(mq && mq.matches);

    var eixo = new Int8Array(N), obs = new Uint8Array(N), sem = new Uint8Array(N), alvo = new Uint8Array(N), naNota = new Uint8Array(N);
    var raio = new Float32Array(N), mix = new Float32Array(N), pesos = [], cmax = 1;
    for (i = 0; i < N; i++) if (D.nos[i].c > cmax) cmax = D.nos[i].c;
    for (i = 0; i < N; i++) {
      var d = D.nos[i], k = d.k, tot = k[0] + k[1] + k[2] + k[3];
      eixo[i] = d.a; obs[i] = d.o; sem[i] = d.s; alvo[i] = d.g; naNota[i] = d.t || 0;
      raio[i] = (1.2 + 4.3 * Math.sqrt(d.c / cmax)) * (mini ? 1.15 : 1);
      pesos.push(tot ? [k[0] / tot, k[1] / tot, k[2] / tot, k[3] / tot] : null);
      mix[i] = (tot && d.a >= 0) ? 1 - k[d.a] / tot : 0;
    }

    function baricentro(w) {
      var x = 0, y = 0, z = 0;
      for (var a = 0; a < 4; a++) { x += w[a] * VERT[a][0]; y += w[a] * VERT[a][1]; z += w[a] * VERT[a][2]; }
      return [x, y, z];
    }
    // afasta sólidos que se interpenetram, sem passar do teto em relação à posição da regra
    function afasta(P, livre, teto, voltas) {
      var P0 = new Float32Array(P), it, a, b, dx, dy, dz, dd, m, e, nn;
      for (it = 0; it < voltas; it++) {
        for (a = 0; a < N; a++) for (b = a + 1; b < N; b++) {
          dx = P[3 * b] - P[3 * a]; dy = P[3 * b + 1] - P[3 * a + 1]; dz = P[3 * b + 2] - P[3 * a + 2];
          m = (raio[a] + raio[b]) * 0.92;
          if (dx > m || dx < -m || dy > m || dy < -m || dz > m || dz < -m) continue;
          dd = Math.sqrt(dx * dx + dy * dy + dz * dz);
          if (dd >= m) continue;
          if (dd < 1e-4) {                       // coincidentes: direção fixa, sempre a mesma
            var u = 1 - 2 * ruido(a * 31 + b, 1), rr = Math.sqrt(1 - u * u), th = TAU * ruido(a + b * 17, 2);
            dx = rr * Math.cos(th); dy = u; dz = rr * Math.sin(th); dd = 1;
          }
          e = (m - dd) / 2 / dd;
          P[3 * a] -= dx * e * livre[0]; P[3 * a + 1] -= dy * e * livre[1]; P[3 * a + 2] -= dz * e * livre[2];
          P[3 * b] += dx * e * livre[0]; P[3 * b + 1] += dy * e * livre[1]; P[3 * b + 2] += dz * e * livre[2];
        }
        for (a = 0; a < N; a++) {
          dx = P[3 * a] - P0[3 * a]; dy = P[3 * a + 1] - P0[3 * a + 1]; dz = P[3 * a + 2] - P0[3 * a + 2];
          nn = Math.sqrt(dx * dx + dy * dy + dz * dz);
          if (nn > teto) { P[3 * a] = P0[3 * a] + dx / nn * teto; P[3 * a + 1] = P0[3 * a + 1] + dy / nn * teto; P[3 * a + 2] = P0[3 * a + 2] + dz / nn * teto; }
        }
      }
    }

    // posições por lente
    var POS = {};
    POS.silos = new Float32Array(3 * N);
    for (i = 0; i < N; i++) { var b0 = pesos[i] ? baricentro(pesos[i]) : [0, 0, 0]; POS.silos[3 * i] = b0[0]; POS.silos[3 * i + 1] = b0[1]; POS.silos[3 * i + 2] = b0[2]; }
    afasta(POS.silos, [1, 1, 1], TETO_AFASTA, 40);
    POS.agenda = POS.silos; POS.nota = POS.silos;
    if (!mini) {
      POS.prov = new Float32Array(POS.silos);
      for (i = 0; i < N; i++) if (!obs[i]) POS.prov[3 * i + 1] -= QUEDA;
      POS.tempo = new Float32Array(3 * N);
      for (i = 0; i < N; i++) {
        POS.tempo[3 * i] = (D.nos[i].y - ANO0) * ESC_ANO;
        POS.tempo[3 * i + 1] = raio[i] + mix[i] * ALT_MIX;
        POS.tempo[3 * i + 2] = (eixo[i] >= 0 ? RAIA[eixo[i]] : 0) + (ruido(i, 3) - 0.5) * 9;
      }
      afasta(POS.tempo, [0, 0, 1], 9, 30);       // só a profundidade da raia se mexe: ano e altura ficam exatos
    }

    // geometria de cada nó (orientação fixa e tom por face, com luz fixa no modelo)
    var geo = [];
    for (i = 0; i < N; i++) {
      var S = SOL[eixo[i] >= 0 ? FORMA[eixo[i]] : 'octa'];
      var ra = ruido(i, 5) * TAU, rb = ruido(i, 6) * TAU, rc = ruido(i, 7) * TAU;
      var off = new Float32Array(S.v.length * 3), nor = new Float32Array(S.f.length * 3), tom = new Uint8Array(S.f.length), j;
      for (j = 0; j < S.v.length; j++) { var p = gira3(S.v[j], ra, rb, rc); off[3 * j] = p[0] * raio[i]; off[3 * j + 1] = p[1] * raio[i]; off[3 * j + 2] = p[2] * raio[i]; }
      for (j = 0; j < S.f.length; j++) {
        var q = gira3(S.n[j], ra, rb, rc); nor[3 * j] = q[0]; nor[3 * j + 1] = q[1]; nor[3 * j + 2] = q[2];
        tom[j] = Math.round(limita(0.20 + 0.80 * Math.max(0, q[0] * LUZ[0] + q[1] * LUZ[1] + q[2] * LUZ[2]), 0, 1) * (N_TOM - 1));
      }
      geo.push({ S: S, off: off, nor: nor, tom: tom });
    }

    // arestas e tríades
    var AR = D.arestas || [], nAr = AR.length / 3, visAr = [], modoLinhas = mini ? 'nenhuma' : 'cruz', pesoMin = 3;
    var viz = [];                                 // vizinhas de cada nó: [outro, peso, outro, peso, ...]
    for (i = 0; i < N; i++) viz.push([]);
    for (i = 0; i < nAr; i++) { viz[AR[3 * i]].push(AR[3 * i + 1], AR[3 * i + 2]); viz[AR[3 * i + 1]].push(AR[3 * i], AR[3 * i + 2]); }
    var TRI = D.triades || [];
    var listas = (D.num && D.num.listas && D.num.listas.comps) || [];
    var LP = listas.map(function (c) { var t = c[0] + c[1] + c[2] + c[3]; return baricentro([c[0] / t, c[1] / t, c[2] / t, c[3] / t]); });
    var notaPos = null, notaGeo = null;
    if (D.nota && D.nota.k) {
      var kt = D.nota.k[0] + D.nota.k[1] + D.nota.k[2] + D.nota.k[3];
      if (kt) {
        notaPos = baricentro([D.nota.k[0] / kt, D.nota.k[1] / kt, D.nota.k[2] / kt, D.nota.k[3] / kt]);
        var SD = SOL.dodeca, RN = 5.6, off2 = new Float32Array(SD.v.length * 3), nor2 = new Float32Array(SD.f.length * 3), tom2 = new Uint8Array(SD.f.length);
        for (i = 0; i < SD.v.length; i++) { off2[3 * i] = SD.v[i][0] * RN; off2[3 * i + 1] = SD.v[i][1] * RN; off2[3 * i + 2] = SD.v[i][2] * RN; }
        for (i = 0; i < SD.f.length; i++) {
          nor2[3 * i] = SD.n[i][0]; nor2[3 * i + 1] = SD.n[i][1]; nor2[3 * i + 2] = SD.n[i][2];
          tom2[i] = Math.round(limita(0.20 + 0.80 * Math.max(0, SD.n[i][0] * LUZ[0] + SD.n[i][1] * LUZ[1] + SD.n[i][2] * LUZ[2]), 0, 1) * (N_TOM - 1));
        }
        notaGeo = { S: SD, off: off2, nor: nor2, tom: tom2, r: RN };
      }
    }

    // estado
    var YAW0 = 0.50;
    var cam = { yaw: YAW0, pit: 0.52, dist: 340, tx: 0, ty: 4, tz: 0 };
    var PRE = {                                     // cada lente tem o ponto de vista em que a sua regra se lê melhor
      silos: { ty: 4, dist: 340, pit: 0.52, tetra: 1, baixo: 0, tempo: 0, tri: 0, nuvem: 0, chao: -H / 4 - 14 },
      tempo: { tx: -4, ty: 14, dist: 440, yaw: -0.26, pit: 0.50, tetra: 0, baixo: 0, tempo: 1, tri: 0, nuvem: 0, chao: 0 },
      prov: { ty: -36, dist: 470, pit: 0.34, tetra: 1, baixo: 1, tempo: 0, tri: 0, nuvem: 0, chao: -H / 4 - QUEDA - 14 },
      agenda: { ty: 4, dist: 340, pit: 0.52, tetra: 1, baixo: 0, tempo: 0, tri: 1, nuvem: 0, chao: -H / 4 - 14 },
      nota: { ty: 2, dist: 325, pit: 0.68, tetra: 1, baixo: 0, tempo: 0, tri: 0, nuvem: 1, chao: -H / 4 - 14 }
    };
    var fr = { tetra: 1, baixo: 0, tempo: 0, tri: 0, nuvem: 0, chao: -H / 4 - 14 };
    var lente = 'silos', pos = new Float32Array(POS.silos), alfa = new Float32Array(N);
    var oculto = [false, false, false, false], rotulosTopo = false;
    var sel = { t: '', i: -1 }, hov = { t: '', i: -1 };
    var SX = new Float32Array(N), SY = new Float32Array(N), SZ = new Float32Array(N), SR = new Float32Array(N);
    var ordem = []; for (i = 0; i < N; i++) { ordem.push(i); alfa[i] = 1; }
    var porCitacao = ordem.slice().sort(function (a, b) { return D.nos[b].c - D.nos[a].c; });
    var larg = 300, alt = 300, dpr = 1, foco = 400, cx0 = 150, cy0 = 150, margemDir = 0;
    var cyw = 1, syw = 0, cpt = 1, spt = 0, px = 0, py = 0, pz = 1, ps = 1;
    var tw = [], raf = 0, ultimo = 0, inercia = false, vyaw = 0, vpit = 0;
    var girando = !reduz && !mini && opt.girar !== false, arrastando = false;
    var LX = [], LY = [], LR = [];                // posição em tela das listas (lente da nota)
    var notaTela = null;

    function alvoAlfa(nome) {
      var a = new Float32Array(N);
      for (var n = 0; n < N; n++) {
        var v = 1;
        if (nome === 'agenda') v = alvo[n] ? 1 : 0.13;
        else if (nome === 'nota') v = naNota[n] ? 1 : 0.13;
        if (eixo[n] >= 0 && oculto[eixo[n]]) v = 0;
        a[n] = v;
      }
      return a;
    }

    // ── projeção ──
    function proj(x, y, z) {
      var dx = x - cam.tx, dy = y - cam.ty, dz = z - cam.tz;
      var x1 = dx * cyw - dz * syw, z1 = dx * syw + dz * cyw;
      var y2 = dy * cpt + z1 * spt, z2 = -dy * spt + z1 * cpt;
      pz = z2 + cam.dist;
      var zc = pz < 1 ? 1 : pz;
      ps = foco / zc; px = cx0 + x1 * ps; py = cy0 - y2 * ps;
    }
    // segmento 3D com recorte no plano próximo; devolve [x1,y1,x2,y2,profundidade] ou null
    function seg(ax, ay, az, bx, by, bz) {
      proj(ax, ay, az); var x1 = px, y1 = py, z1 = pz;
      proj(bx, by, bz); var x2 = px, y2 = py, z2 = pz, PERTO = 6, t;
      if (z1 < PERTO && z2 < PERTO) return null;
      if (z1 < PERTO) { t = (PERTO - z1) / (z2 - z1); proj(ax + (bx - ax) * t, ay + (by - ay) * t, az + (bz - az) * t); x1 = px; y1 = py; z1 = PERTO; }
      else if (z2 < PERTO) { t = (PERTO - z2) / (z1 - z2); proj(bx + (ax - bx) * t, by + (ay - by) * t, bz + (az - bz) * t); x2 = px; y2 = py; z2 = PERTO; }
      return [x1, y1, x2, y2, (z1 + z2) / 2];
    }
    function neblina(z) { return limita(Math.round((z - (cam.dist - 70)) / 165 * (N_NEB - 1)), 0, N_NEB - 1); }

    // ── texto com halo de papel ──
    var FONTE = '"DM Sans", system-ui, sans-serif', caixas = [];
    function texto(s, x, y, o) {
      o = o || {};
      ctx.font = (o.peso || 500) + ' ' + (o.tam || 12.5) + 'px ' + FONTE;
      ctx.textAlign = o.alinha || 'left'; ctx.textBaseline = o.base || 'middle';
      var w = ctx.measureText(s).width, h = (o.tam || 12.5) + 4;
      var x0 = o.alinha === 'right' ? x - w : o.alinha === 'center' ? x - w / 2 : x;
      var lim = larg - margemDir - 5;
      if (x0 + w > lim) { x -= x0 + w - lim; x0 -= x0 + w - lim; }
      if (x0 < 5) { x += 5 - x0; x0 = 5; }
      if (o.evita) {
        for (var c = 0; c < caixas.length; c++) { var b = caixas[c]; if (x0 < b[2] && x0 + w > b[0] && y - h / 2 < b[3] && y + h / 2 > b[1]) return false; }
      }
      caixas.push([x0 - 3, y - h / 2, x0 + w + 3, y + h / 2]);
      ctx.lineJoin = 'round'; ctx.lineWidth = 3.5; ctx.strokeStyle = css(PAPEL, o.alfa == null ? 0.92 : 0.92 * o.alfa);
      ctx.strokeText(s, x, y);
      ctx.fillStyle = css(o.cor || TINTA, o.alfa == null ? 1 : o.alfa);
      ctx.fillText(s, x, y);
      return true;
    }
    function glifo(g, x, y, r, cheio, cor) {      // silhueta 2D da forma (para obras distantes e rótulos)
      ctx.beginPath();
      if (g === 0) ctx.arc(x, y, r, 0, TAU);
      else if (g === 1) ctx.rect(x - r * 0.86, y - r * 0.86, r * 1.72, r * 1.72);
      else if (g === 2) { ctx.moveTo(x, y - r * 1.12); ctx.lineTo(x + r, y + r * 0.72); ctx.lineTo(x - r, y + r * 0.72); ctx.closePath(); }
      else { ctx.moveTo(x, y - r * 1.15); ctx.lineTo(x + r * 0.95, y); ctx.lineTo(x, y + r * 1.15); ctx.lineTo(x - r * 0.95, y); ctx.closePath(); }
      if (cheio) { ctx.fillStyle = cor; ctx.fill(); }
      else { ctx.fillStyle = css(PAPEL); ctx.fill(); ctx.lineWidth = 1.2; ctx.strokeStyle = cor; ctx.stroke(); }
    }

    // ── desenho de um sólido convexo (corte de face oculta pela normal) ──
    var vx = new Float32Array(20), vy = new Float32Array(20);
    function desenhaSolido(G, X, Y, Z, grupo, cheio, nb, tinta) {
      var S = G.S, off = G.off, nor = G.nor, f, j, n = S.v.length, idx, n1z, n2z;
      for (j = 0; j < n; j++) { proj(X + off[3 * j], Y + off[3 * j + 1], Z + off[3 * j + 2]); vx[j] = px; vy[j] = py; }
      var tons = cheio ? TOM[grupo][nb] : VAZ[grupo][nb];
      ctx.lineJoin = 'round';
      for (f = 0; f < S.f.length; f++) {
        n1z = nor[3 * f] * syw + nor[3 * f + 2] * cyw;
        n2z = -nor[3 * f + 1] * spt + n1z * cpt;
        if (n2z > -0.03) continue;               // face virada para o outro lado
        idx = S.f[f];
        ctx.beginPath(); ctx.moveTo(vx[idx[0]], vy[idx[0]]);
        for (j = 1; j < idx.length; j++) ctx.lineTo(vx[idx[j]], vy[idx[j]]);
        ctx.closePath();
        ctx.fillStyle = tons[G.tom[f]]; ctx.fill();
        if (tinta) { ctx.lineWidth = 1.05; ctx.strokeStyle = css(TINTA, 0.78); }
        else if (cheio) { ctx.lineWidth = 0.7; ctx.strokeStyle = tons[0]; }
        else { ctx.lineWidth = 1.1; ctx.strokeStyle = TRACO[grupo][nb]; }
        ctx.stroke();
      }
    }

    // ── camadas ──
    function chao() {
      if (cam.pit < 0.07) return;
      var y0 = fr.chao, k, s, a = limita((cam.pit - 0.07) * 4, 0, 1), n;
      ctx.lineWidth = 1; ctx.strokeStyle = css(TINTA, 0.055 * a); ctx.beginPath();
      for (k = -6; k <= 6; k++) {
        s = seg(k * 20, y0, -120, k * 20, y0, 120); if (s) { ctx.moveTo(s[0], s[1]); ctx.lineTo(s[2], s[3]); }
        s = seg(-120, y0, k * 20, 120, y0, k * 20); if (s) { ctx.moveTo(s[0], s[1]); ctx.lineTo(s[2], s[3]); }
      }
      ctx.stroke();
      ctx.fillStyle = css(TINTA, 0.06 * a);       // sombras: dizem a que altura cada obra está
      for (n = 0; n < N; n++) {
        if (alfa[n] < 0.3) continue;
        proj(pos[3 * n], y0, pos[3 * n + 2]);
        if (pz < 8) continue;
        ctx.beginPath(); ctx.ellipse(px, py, raio[n] * ps, Math.max(0.6, raio[n] * ps * spt), 0, 0, TAU); ctx.fill();
      }
    }
    function tracoTetra(dy, a, tracejado) {
      var k, s, e;
      ctx.lineWidth = 1;
      for (k = 0; k < 6; k++) {
        e = AR_TETRA[k];
        s = seg(VERT[e[0]][0], VERT[e[0]][1] + dy, VERT[e[0]][2], VERT[e[1]][0], VERT[e[1]][1] + dy, VERT[e[1]][2]);
        if (!s) continue;
        ctx.setLineDash(tracejado || k >= 3 ? [5, 5] : []);     // arestas até o 4º eixo vão tracejadas
        ctx.strokeStyle = css(TINTA, (k >= 3 ? 0.22 : 0.34) * a);
        ctx.beginPath(); ctx.moveTo(s[0], s[1]); ctx.lineTo(s[2], s[3]); ctx.stroke();
      }
      ctx.setLineDash([]);
    }
    function moldura() {
      var k, s, a;
      if (fr.tetra > 0.02) tracoTetra(0, fr.tetra, false);
      if (fr.baixo > 0.02) tracoTetra(-QUEDA, fr.baixo * fr.tetra, true);
      if (fr.tempo > 0.02) {
        a = fr.tempo;
        var X0 = (1920 - ANO0) * ESC_ANO - 6, X1 = (2025 - ANO0) * ESC_ANO + 4;
        for (k = 0; k < 4; k++) {                  // raias
          s = seg(X0, 0, RAIA[k], X1, 0, RAIA[k]);
          if (s) { ctx.lineWidth = 1.4; ctx.strokeStyle = css(COR[k], 0.45 * a); ctx.beginPath(); ctx.moveTo(s[0], s[1]); ctx.lineTo(s[2], s[3]); ctx.stroke(); }
        }
        ctx.lineWidth = 1; ctx.strokeStyle = css(TINTA, 0.10 * a); ctx.beginPath();
        for (k = 1920; k <= 2020; k += 20) {       // marcas de 20 em 20 anos
          s = seg((k - ANO0) * ESC_ANO, 0, -50, (k - ANO0) * ESC_ANO, 0, 50); if (s) { ctx.moveTo(s[0], s[1]); ctx.lineTo(s[2], s[3]); }
        }
        ctx.stroke();
        s = seg(X1 + 8, 0, -50, X1 + 8, ALT_MIX, -50);   // régua da altura, no fim da linha do tempo
        if (s) { ctx.strokeStyle = css(TINTA, 0.5 * a); ctx.beginPath(); ctx.moveTo(s[0], s[1]); ctx.lineTo(s[2], s[3]); ctx.stroke(); }
      }
    }
    function linhas() {
      var n = visAr.length, b, k, e, s, t, z, fade = lente === 'tempo' ? 0 : (lente === 'agenda' || lente === 'nota') ? 0.35 : 1;
      if (sel.t === 'no') fade *= 0.4;
      if (n && fade > 0) {
        var faixa = [[], [], []];
        for (k = 0; k < n; k++) {
          e = visAr[k]; s = AR[3 * e]; t = AR[3 * e + 1];
          if (alfa[s] < 0.5 || alfa[t] < 0.5 || SZ[s] < 8 || SZ[t] < 8) continue;
          z = (SZ[s] + SZ[t]) / 2;
          faixa[z < cam.dist - 12 ? 0 : z < cam.dist + 28 ? 1 : 2].push(s, t);
        }
        var al = [0.30, 0.19, 0.10];
        ctx.lineWidth = 0.8;
        for (b = 2; b >= 0; b--) {
          ctx.strokeStyle = css(TINTA, al[b] * fade); ctx.beginPath();
          for (k = 0; k < faixa[b].length; k += 2) { ctx.moveTo(SX[faixa[b][k]], SY[faixa[b][k]]); ctx.lineTo(SX[faixa[b][k + 1]], SY[faixa[b][k + 1]]); }
          ctx.stroke();
        }
      }
      if (sel.t === 'no' && sel.i >= 0) {           // as linhas da obra selecionada, na cor da tradição da vizinha
        var v = viz[sel.i], g;
        ctx.lineWidth = 1.15;
        for (g = -1; g < 4; g++) {
          ctx.strokeStyle = g < 0 ? css(NEUTRO, 0.5) : css(COR[g], 0.62); ctx.beginPath();
          for (k = 0; k < v.length; k += 2) {
            t = v[k];
            if (eixo[t] !== g || alfa[t] < 0.05 || SZ[t] < 8 || v[k + 1] < pesoMin) continue;
            ctx.moveTo(SX[sel.i], SY[sel.i]); ctx.lineTo(SX[t], SY[t]);
          }
          ctx.stroke();
        }
      }
    }
    function triangulos() {
      if (fr.tri < 0.02 || !TRI.length) return;
      var ord = [], k, t, m, a = fr.tri;
      for (k = 0; k < TRI.length; k++) {
        m = TRI[k].m;
        if (SZ[m[0]] < 8 || SZ[m[1]] < 8 || SZ[m[2]] < 8) continue;
        if (alfa[m[0]] < 0.05 || alfa[m[1]] < 0.05 || alfa[m[2]] < 0.05) continue;
        ord.push(k);
      }
      ord.sort(function (p, q) { return (SZ[TRI[q].m[0]] + SZ[TRI[q].m[1]] + SZ[TRI[q].m[2]]) - (SZ[TRI[p].m[0]] + SZ[TRI[p].m[1]] + SZ[TRI[p].m[2]]); });
      for (k = 0; k < ord.length; k++) {
        t = TRI[ord[k]]; m = t.m;
        var foco2 = (sel.t === 'tri' && sel.i === ord[k]) || (hov.t === 'tri' && hov.i === ord[k]);
        ctx.beginPath(); ctx.moveTo(SX[m[0]], SY[m[0]]); ctx.lineTo(SX[m[1]], SY[m[1]]); ctx.lineTo(SX[m[2]], SY[m[2]]); ctx.closePath();
        if (t.n) {                                 // núcleo duro: face cheia, contorno contínuo
          ctx.fillStyle = css(TINTA, (foco2 ? 0.26 : 0.075) * a); ctx.fill();
          ctx.setLineDash([]); ctx.lineWidth = foco2 ? 2.2 : 1.1; ctx.strokeStyle = css(TINTA, (foco2 ? 0.95 : 0.55) * a); ctx.stroke();
        } else {                                   // depende de rótulo inferido: só contorno, tracejado
          if (foco2) { ctx.fillStyle = css(TINTA, 0.12 * a); ctx.fill(); }
          ctx.setLineDash([5, 4]); ctx.lineWidth = foco2 ? 2 : 1; ctx.strokeStyle = css(TINTA, (foco2 ? 0.9 : 0.36) * a); ctx.stroke();
        }
      }
      ctx.setLineDash([]);
    }
    function nuvem() {
      LX.length = 0; LY.length = 0; LR.length = 0; notaTela = null;
      if (fr.nuvem < 0.02) return;
      var k, a = fr.nuvem, r;
      for (k = 0; k < LP.length; k++) {
        proj(LP[k][0], LP[k][1], LP[k][2]);
        r = Math.max(1.6, (0.55 + 0.40 * Math.sqrt(listas[k][4])) * ps);
        LX.push(px); LY.push(py); LR.push(pz < 8 ? 0 : r);
        if (pz < 8) continue;
        var f2 = (hov.t === 'lista' && hov.i === k) || (sel.t === 'lista' && sel.i === k);
        ctx.beginPath(); ctx.arc(px, py, r, 0, TAU);
        ctx.fillStyle = css(TINTA, (f2 ? 0.62 : 0.26) * a); ctx.fill();
        if (f2) { ctx.lineWidth = 2; ctx.strokeStyle = css(TINTA, 0.9 * a); ctx.stroke(); }
      }
      if (notaPos) {
        ctx.lineWidth = 1; ctx.strokeStyle = css(TINTA, 0.42 * a); ctx.beginPath();
        proj(notaPos[0], notaPos[1], notaPos[2]); var nx = px, ny = py, nz = pz, ns = ps;
        for (k = 0; k < N; k++) if (naNota[k] && alfa[k] > 0.05 && SZ[k] > 8) { ctx.moveTo(nx, ny); ctx.lineTo(SX[k], SY[k]); }
        ctx.stroke();
        notaTela = { x: nx, y: ny, z: nz, r: notaGeo.r * ns };
      }
    }
    function desenhaNota() {
      if (!notaTela || fr.nuvem < 0.02 || notaTela.z < 8) return;
      ctx.globalAlpha = fr.nuvem;
      desenhaSolido(notaGeo, notaPos[0], notaPos[1], notaPos[2], 5, true, 0, false);
      ctx.globalAlpha = 1;
      if (sel.t === 'nota' || hov.t === 'nota') { ctx.lineWidth = 2; ctx.strokeStyle = css(TINTA, 0.9); ctx.beginPath(); ctx.arc(notaTela.x, notaTela.y, notaTela.r + 4, 0, TAU); ctx.stroke(); }
    }
    function desenhaNos() {
      var k, n, a, nb, r, g, notaFeita = false;
      ordem.sort(function (p, q) { return SZ[q] - SZ[p]; });
      for (k = 0; k < N; k++) {
        n = ordem[k]; a = alfa[n];
        if (!notaFeita && notaTela && SZ[n] < notaTela.z) { desenhaNota(); notaFeita = true; }
        if (a < 0.02 || SZ[n] < 8) continue;
        nb = neblina(SZ[n]); r = SR[n]; g = eixo[n] >= 0 ? eixo[n] : 4;
        if (a < 1) ctx.globalAlpha = a;
        if (r < 3.3) glifo(eixo[n] >= 0 ? eixo[n] : 3, SX[n], SY[n], Math.max(1.8, r), !!obs[n], obs[n] ? TOM[g][nb][3] : TRACO[g][nb]);
        else desenhaSolido(geo[n], pos[3 * n], pos[3 * n + 1], pos[3 * n + 2], g, !!obs[n], nb, !!sem[n]);
        if (a < 1) ctx.globalAlpha = 1;
        if (lente === 'agenda' && alvo[n] && a > 0.5) { ctx.lineWidth = 1.5; ctx.strokeStyle = css(TINTA, 0.8); ctx.beginPath(); ctx.arc(SX[n], SY[n], r + 3.2, 0, TAU); ctx.stroke(); }
      }
      if (!notaFeita) desenhaNota();
      var dest = [];
      if (hov.t === 'no') dest.push(hov.i);
      if (sel.t === 'no') dest.push(sel.i);
      for (k = 0; k < dest.length; k++) {
        n = dest[k]; if (SZ[n] < 8) continue;
        var forte = sel.t === 'no' && sel.i === n;
        ctx.lineWidth = forte ? 4.5 : 3.5; ctx.strokeStyle = css(PAPEL, 0.95); ctx.beginPath(); ctx.arc(SX[n], SY[n], SR[n] + 4.5, 0, TAU); ctx.stroke();
        ctx.lineWidth = forte ? 2.4 : 1.4; ctx.strokeStyle = css(TINTA); ctx.beginPath(); ctx.arc(SX[n], SY[n], SR[n] + 4.5, 0, TAU); ctx.stroke();
      }
    }
    function rotuloVertice(k, dy, a, t) {          // nome do vértice: para fora do centro, na tela
      proj(0, dy + 8, 0); var ox = px, oy = py;
      proj(VERT[k][0], VERT[k][1] + dy, VERT[k][2]);
      if (pz < 8) return;
      if (px < -4 || px > larg - margemDir + 4 || py < -4 || py > alt + 4) return;   // vértice fora do quadro: o nome não fica pendurado na borda
      var dx = px - ox, dz = py - oy, n = Math.sqrt(dx * dx + dz * dz) || 1, x = px, y = py;
      dx /= n; dz /= n;
      ctx.font = '600 ' + t + 'px ' + FONTE;
      var w = ctx.measureText(NOME[k]).width + 16, afasta2 = 15;
      x += dx * afasta2; y += dz * afasta2;
      var x0 = dx < -0.35 ? x - w : dx > 0.35 ? x : x - w / 2;
      if (Math.abs(dx) <= 0.35) y += dz < 0 ? -9 : 11;
      x0 = limita(x0, 6, Math.max(6, larg - margemDir - w - 6));
      y = limita(y, 12, alt - 12);
      ctx.globalAlpha = a; glifo(k, x0 + 5.5, y, mini ? 4.5 : 5.2, true, css(COR[k])); ctx.globalAlpha = 1;
      texto(NOME[k], x0 + 16, y, { peso: 600, tam: t, alfa: a });
    }
    function curto(s, n) { return s.length > n ? s.slice(0, n - 1).replace(/[\s,·:;-]+$/, '') + '…' : s; }
    function rotulos() {
      var k, n, s, x, y, t = mini ? 11.5 : 13;
      caixas.length = 0;
      if (sel.t === 'no' && SZ[sel.i] > 8) texto(curto(D.nos[sel.i].l, 46), SX[sel.i] + SR[sel.i] + 9, SY[sel.i], { peso: 700, tam: 13 });
      if (hov.t === 'no' && !(sel.t === 'no' && sel.i === hov.i) && SZ[hov.i] > 8) texto(curto(D.nos[hov.i].l, 46), SX[hov.i] + SR[hov.i] + 9, SY[hov.i], { tam: 12.5 });
      if (sel.t === 'tri' && TRI[sel.i]) TRI[sel.i].m.forEach(function (m) { if (SZ[m] > 8) texto(curto(D.nos[m].l, 34), SX[m] + SR[m] + 8, SY[m], { tam: 12, evita: true }); });
      if (fr.tetra > 0.3) for (k = 0; k < 4; k++) rotuloVertice(k, 0, fr.tetra, t);
      if (fr.baixo > 0.3 && !mini) {
        var estreita = larg < 520;                 // tela estreita: rótulo curto, para não encostar nas obras
        proj(0, -H / 4 + 26, 0); texto(estreita ? 'em cima: observado' : 'em cima: rótulo observado', estreita ? 10 : 16, py, { tam: 13, peso: 600, alfa: fr.baixo });
        proj(0, -H / 4 - QUEDA + 26, 0); texto(estreita ? 'embaixo: inferido' : 'embaixo: rótulo inferido', estreita ? 10 : 16, py, { tam: 13, peso: 600, alfa: fr.baixo });
      }
      if (fr.tempo > 0.3) {
        var X0 = (1920 - ANO0) * ESC_ANO - 6;
        for (k = 1920; k <= 2020; k += 20) { proj((k - ANO0) * ESC_ANO, 0, -57); if (pz > 8) texto(String(k), px, py, { tam: 12, alinha: 'center', alfa: fr.tempo, cor: NEUTRO }); }
        for (k = 0; k < 4; k++) { proj(X0 - 5, 0, RAIA[k]); if (pz > 8) texto(NOME[k], px, py, { tam: 12.5, peso: 600, alinha: 'right', alfa: fr.tempo }); }
        var XR = (2025 - ANO0) * ESC_ANO + 12;
        proj(XR, ALT_MIX, -50); if (pz > 8) texto('100% fora da própria tradição', px - 7, py, { tam: 12, alinha: 'right', alfa: fr.tempo, cor: NEUTRO });
        proj(XR, 0, -50); if (pz > 8) texto('0%', px + 7, py, { tam: 12, alfa: fr.tempo, cor: NEUTRO });
      }
      if (fr.nuvem > 0.3 && notaTela && notaTela.z > 8) texto('a nota', notaTela.x + notaTela.r + 8, notaTela.y, { peso: 700, tam: 13, alfa: fr.nuvem });
      if (lente === 'nota' && fr.nuvem > 0.6) {
        for (k = 0; k < N; k++) { n = porCitacao[k]; if (naNota[n] && SZ[n] > 8 && !(sel.t === 'no' && sel.i === n)) texto(curto(D.nos[n].l, 30), SX[n] + SR[n] + 7, SY[n], { tam: 12, evita: true, alfa: fr.nuvem }); }
      } else if (rotulosTopo) {
        for (k = 0, s = 0; k < N && s < 14; k++) { n = porCitacao[k]; if (alfa[n] < 0.5 || SZ[n] < 8) continue; if (texto(curto(D.nos[n].l, 30), SX[n] + SR[n] + 7, SY[n], { tam: 12, evita: true })) s++; }
      }
    }
    var ultDes = 0;
    function desenha() {
      var n, t0 = agora();
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      ctx.globalAlpha = 1; ctx.setLineDash([]);
      ctx.fillStyle = css(PAPEL); ctx.fillRect(0, 0, larg, alt);
      cyw = Math.cos(cam.yaw); syw = Math.sin(cam.yaw); cpt = Math.cos(cam.pit); spt = Math.sin(cam.pit);
      foco = 0.5 * Math.min(larg - margemDir, alt * 1.22) / Math.tan(FOV / 2);
      cx0 = (larg - margemDir) / 2; cy0 = alt / 2 + (mini ? 0 : Math.min(34, alt * 0.05));
      for (n = 0; n < N; n++) { proj(pos[3 * n], pos[3 * n + 1], pos[3 * n + 2]); SX[n] = px; SY[n] = py; SZ[n] = pz; SR[n] = raio[n] * ps; }
      chao(); moldura(); linhas(); triangulos(); nuvem(); desenhaNos(); rotulos();
      ultDes = agora() - t0;
      if (opt.aoDesenhar) opt.aoDesenhar();
    }

    // ── animação ──
    function agora() { return global.performance && performance.now ? performance.now() : Date.now(); }
    function suave(k) { return k < 0.5 ? 4 * k * k * k : 1 - Math.pow(-2 * k + 2, 3) / 2; }
    function pede() { if (!raf) raf = global.requestAnimationFrame(quadro); }
    function anima(dur, f, fim) {
      if (reduz || dur <= 0) { f(1); if (fim) fim(); pede(); return; }
      tw.push({ t0: agora(), dur: dur, f: f, fim: fim }); pede();
    }
    function quadro(t) {
      raf = 0;
      var dt = ultimo ? Math.min(50, t - ultimo) : 16.7, mais = false, k, w, q;
      ultimo = t;
      for (k = tw.length - 1; k >= 0; k--) {
        w = tw[k]; q = (t - w.t0) / w.dur;
        if (q >= 1) { w.f(1); tw.splice(k, 1); if (w.fim) w.fim(); } else { w.f(suave(q < 0 ? 0 : q)); mais = true; }
      }
      if (inercia) {
        cam.yaw += vyaw; cam.pit = limita(cam.pit + vpit, PIT0, PIT1); vyaw *= 0.92; vpit *= 0.92;
        if (Math.abs(vyaw) + Math.abs(vpit) < 0.0006) inercia = false; else mais = true;
      }
      if (girando && !arrastando && !tw.length) { cam.yaw += 0.00011 * dt; mais = true; } else if (girando) mais = true;
      desenha();
      if (mais) pede(); else ultimo = 0;
    }
    function pertoDe(atual, alvoAng) { return alvoAng + Math.round((atual - alvoAng) / TAU) * TAU; }

    function definirLente(nome, imediato) {
      if (!POS[nome]) return false;
      var anterior = lente; lente = nome;
      var de = new Float32Array(pos), para = POS[nome], a0 = new Float32Array(alfa), a1 = alvoAlfa(nome);
      var p = PRE[nome], f0 = { tetra: fr.tetra, baixo: fr.baixo, tempo: fr.tempo, tri: fr.tri, nuvem: fr.nuvem, chao: fr.chao };
      var c0 = { yaw: cam.yaw, pit: cam.pit, dist: cam.dist, tx: cam.tx, ty: cam.ty, tz: cam.tz };
      var c1 = {
        yaw: p.yaw != null ? pertoDe(cam.yaw, p.yaw) : (anterior === 'tempo' ? pertoDe(cam.yaw, YAW0) : cam.yaw),
        pit: p.pit, dist: p.dist, tx: p.tx || 0, ty: p.ty, tz: 0
      };
      tw.length = 0;
      anima(imediato ? 0 : 900, function (q) {
        var n;
        for (n = 0; n < 3 * N; n++) pos[n] = de[n] + (para[n] - de[n]) * q;
        for (n = 0; n < N; n++) alfa[n] = a0[n] + (a1[n] - a0[n]) * q;
        for (var c in c1) cam[c] = c0[c] + (c1[c] - c0[c]) * q;
        for (var f in f0) fr[f] = f0[f] + (p[f] - f0[f]) * q;
      });
      atualizaLinhas();
      return true;
    }
    function reaplicaAlfa() {
      var a0 = new Float32Array(alfa), a1 = alvoAlfa(lente);
      anima(260, function (q) { for (var n = 0; n < N; n++) alfa[n] = a0[n] + (a1[n] - a0[n]) * q; });
    }
    function focar(x, y, z, dist) {
      var c0 = { tx: cam.tx, ty: cam.ty, tz: cam.tz, dist: cam.dist }, c1 = { tx: x, ty: y, tz: z, dist: dist || cam.dist };
      anima(520, function (q) { for (var c in c1) cam[c] = c0[c] + (c1[c] - c0[c]) * q; });
    }
    function recentrar() {
      var p = PRE[lente], c0 = { yaw: cam.yaw, pit: cam.pit, dist: cam.dist, tx: cam.tx, ty: cam.ty, tz: cam.tz };
      var c1 = { yaw: pertoDe(cam.yaw, p.yaw != null ? p.yaw : YAW0), pit: p.pit, dist: p.dist, tx: p.tx || 0, ty: p.ty, tz: 0 };
      inercia = false;
      anima(520, function (q) { for (var c in c1) cam[c] = c0[c] + (c1[c] - c0[c]) * q; });
    }
    function zoom(f) { var d0 = cam.dist, d1 = limita(cam.dist * f, DIST0, DIST1); anima(200, function (q) { cam.dist = d0 + (d1 - d0) * q; }); }
    function girar(liga) { girando = !!liga; if (opt.aoGiro) opt.aoGiro(girando); pede(); }

    // ── filtros ──
    function atualizaLinhas() {
      visAr = [];
      if (modoLinhas !== 'nenhuma') {
        for (var e = 0; e < nAr; e++) {
          var s = AR[3 * e], t = AR[3 * e + 1];
          if (AR[3 * e + 2] < pesoMin || eixo[s] < 0 || eixo[t] < 0 || eixo[s] === eixo[t]) continue;
          if (oculto[eixo[s]] || oculto[eixo[t]]) continue;
          if (modoLinhas === 'cruz' && !(obs[s] && obs[t])) continue;
          visAr.push(e);
        }
      }
      if (opt.aoLinhas) opt.aoLinhas(visAr.length, nAr);
      pede();
    }
    function filtrar(o) {
      if (o.linhas != null) modoLinhas = o.linhas;
      if (o.peso != null) pesoMin = o.peso;
      if (o.oculto) oculto = o.oculto.slice();
      if (o.rotulos != null) rotulosTopo = !!o.rotulos;
      atualizaLinhas();
      if (o.oculto) reaplicaAlfa();
    }

    // ── o que está sob o ponteiro ──
    function apanha(x, y, folga) {
      var k, n, dx, dy, r, m;
      for (k = N - 1; k >= 0; k--) {               // das obras mais próximas para as mais distantes
        n = ordem[k];
        if (alfa[n] < 0.3 || SZ[n] < 8) continue;
        dx = x - SX[n]; dy = y - SY[n]; r = Math.max(SR[n] + 2, folga);
        if (dx * dx + dy * dy <= r * r) return { t: 'no', i: n };
      }
      if (lente === 'nota' && notaTela) {
        dx = x - notaTela.x; dy = y - notaTela.y; r = Math.max(notaTela.r + 3, folga);
        if (dx * dx + dy * dy <= r * r) return { t: 'nota', i: 0 };
        var melhor = -1, md = 1e9;
        for (k = 0; k < LX.length; k++) {
          if (!LR[k]) continue;
          dx = x - LX[k]; dy = y - LY[k]; r = Math.max(LR[k] + 2, folga * 0.8);
          if (dx * dx + dy * dy <= r * r && dx * dx + dy * dy < md) { md = dx * dx + dy * dy; melhor = k; }
        }
        if (melhor >= 0) return { t: 'lista', i: melhor };
      }
      if (lente === 'agenda' && fr.tri > 0.5) {
        var bz = 1e9, bi = -1;
        for (k = 0; k < TRI.length; k++) {
          m = TRI[k].m;
          if (alfa[m[0]] < 0.05 || alfa[m[1]] < 0.05 || alfa[m[2]] < 0.05) continue;
          if (dentro(x, y, SX[m[0]], SY[m[0]], SX[m[1]], SY[m[1]], SX[m[2]], SY[m[2]])) {
            var z = SZ[m[0]] + SZ[m[1]] + SZ[m[2]];
            if (z < bz) { bz = z; bi = k; }
          }
        }
        if (bi >= 0) return { t: 'tri', i: bi };
      }
      return { t: '', i: -1 };
    }
    function dentro(x, y, x1, y1, x2, y2, x3, y3) {
      var d1 = (x - x2) * (y1 - y2) - (x1 - x2) * (y - y2), d2 = (x - x3) * (y2 - y3) - (x2 - x3) * (y - y3), d3 = (x - x1) * (y3 - y1) - (x3 - x1) * (y - y1);
      return !((d1 < 0 || d2 < 0 || d3 < 0) && (d1 > 0 || d2 > 0 || d3 > 0));
    }
    function selecionar(s, o) {
      o = o || {};
      sel = { t: s.t || '', i: s.i == null ? -1 : s.i };
      if (o.focar && sel.t === 'no') {
        var Pn = POS[lente], fy = Pn[3 * sel.i + 1], fd = 205;
        // lente da origem: o quadro fica entre os dois andares, porque as linhas da obra sobem
        // até as vizinhas de rótulo observado — é delas que sai a posição e o rótulo inferido
        if (lente === 'prov') { fy = POS.silos[3 * sel.i + 1] - QUEDA / 2; fd = 300; }
        focar(Pn[3 * sel.i], fy, Pn[3 * sel.i + 2], Math.min(cam.dist, fd));
      }
      if (o.focar && sel.t === 'tri' && TRI[sel.i]) {
        var m = TRI[sel.i].m, P = POS[lente];
        focar((P[3 * m[0]] + P[3 * m[1]] + P[3 * m[2]]) / 3, (P[3 * m[0] + 1] + P[3 * m[1] + 1] + P[3 * m[2] + 1]) / 3, (P[3 * m[0] + 2] + P[3 * m[1] + 2] + P[3 * m[2] + 2]) / 3, Math.min(cam.dist, 235));
      }
      if (!o.silencio && opt.aoSelecionar) opt.aoSelecionar(sel, o);
      pede();
    }

    // ── ponteiro, roda e teclado ──
    var pt = {}, nPt = 0, moveu = 0, ux = 0, uy = 0, pinca = 0, meioX = 0, meioY = 0, panoramica = false;
    function local(e) { var r = canvas.getBoundingClientRect(); return [e.clientX - r.left, e.clientY - r.top]; }
    function conta() { var c = 0; for (var k in pt) c++; return c; }
    function pan(dx, dy) {
      var s = cam.dist / foco;
      cam.tx -= cyw * dx * s; cam.tz += syw * dx * s;
      cam.tx += syw * spt * dy * s; cam.ty += cpt * dy * s; cam.tz += cyw * spt * dy * s;
    }
    canvas.addEventListener('pointerdown', function (e) {
      if (e.pointerType === 'mouse' && e.button !== 0 && e.button !== 2) return;
      try { canvas.setPointerCapture(e.pointerId); } catch (err) { /* ponteiro já solto */ }
      pt[e.pointerId] = [e.clientX, e.clientY]; nPt = conta();
      arrastando = true; inercia = false; moveu = 0; ux = e.clientX; uy = e.clientY;
      panoramica = e.button === 2 || e.shiftKey;
      if (girando) girar(false);
      tw = tw.filter(function (w) { return w.dur > 600; });   // interrompe ajustes de câmera, não a troca de lente
      if (nPt === 2) {
        var ks = Object.keys(pt), a = pt[ks[0]], b = pt[ks[1]];
        pinca = Math.hypot(a[0] - b[0], a[1] - b[1]); meioX = (a[0] + b[0]) / 2; meioY = (a[1] + b[1]) / 2;
      }
    });
    canvas.addEventListener('pointermove', function (e) {
      var l;
      if (!pt[e.pointerId]) {
        if (mini || e.pointerType !== 'mouse') return;
        l = local(e);
        var h = apanha(l[0], l[1], 7);
        if (h.t !== hov.t || h.i !== hov.i) { hov = h; canvas.style.cursor = h.t ? 'pointer' : 'grab'; if (opt.aoPassar) opt.aoPassar(h); pede(); }
        return;
      }
      pt[e.pointerId] = [e.clientX, e.clientY];
      if (nPt >= 2) {
        var ks = Object.keys(pt), a = pt[ks[0]], b = pt[ks[1]];
        var dd = Math.hypot(a[0] - b[0], a[1] - b[1]), mx = (a[0] + b[0]) / 2, my = (a[1] + b[1]) / 2;
        if (pinca > 0 && dd > 0) cam.dist = limita(cam.dist * pinca / dd, DIST0, DIST1);
        pan(mx - meioX, my - meioY);
        pinca = dd; meioX = mx; meioY = my; moveu += 10; pede();
        return;
      }
      var dx = e.clientX - ux, dy = e.clientY - uy; ux = e.clientX; uy = e.clientY;
      moveu += Math.abs(dx) + Math.abs(dy);
      if (panoramica) pan(dx, dy);
      else { vyaw = dx * 0.0062; vpit = dy * 0.0062; cam.yaw += vyaw; cam.pit = limita(cam.pit + vpit, PIT0, PIT1); }
      pede();
    });
    function solta(e) {
      if (!pt[e.pointerId]) return;
      delete pt[e.pointerId]; nPt = conta();
      if (nPt === 0) {
        arrastando = false;
        if (moveu < 6 && !mini && e.type === 'pointerup') {
          var l = local(e);
          selecionar(apanha(l[0], l[1], e.pointerType === 'mouse' ? 7 : 18), { origem: 'cena' });
        } else if (!reduz && !panoramica && Math.abs(vyaw) + Math.abs(vpit) > 0.004) { inercia = true; pede(); }
      }
    }
    canvas.addEventListener('pointerup', solta);
    canvas.addEventListener('pointercancel', solta);
    canvas.addEventListener('contextmenu', function (e) { e.preventDefault(); });
    if (!mini) {
      canvas.addEventListener('wheel', function (e) {
        e.preventDefault();
        if (girando) girar(false);
        cam.dist = limita(cam.dist * Math.exp(limita(e.deltaY, -120, 120) * 0.0011), DIST0, DIST1); pede();
      }, { passive: false });
      canvas.addEventListener('dblclick', function (e) {
        var l = local(e), h = apanha(l[0], l[1], 9);
        if (h.t === 'no') focar(pos[3 * h.i], pos[3 * h.i + 1], pos[3 * h.i + 2], 150);
      });
      canvas.addEventListener('pointerleave', function () { if (hov.t) { hov = { t: '', i: -1 }; pede(); } });
      canvas.addEventListener('keydown', function (e) {
        var usado = true, kk = e.key;
        if (kk === 'ArrowLeft') cam.yaw -= 0.12; else if (kk === 'ArrowRight') cam.yaw += 0.12;
        else if (kk === 'ArrowUp') cam.pit = limita(cam.pit + 0.08, PIT0, PIT1); else if (kk === 'ArrowDown') cam.pit = limita(cam.pit - 0.08, PIT0, PIT1);
        else if (kk === '+' || kk === '=') zoom(0.86); else if (kk === '-' || kk === '_') zoom(1.16);
        else if (kk === '0' || kk === 'Home') recentrar();
        else if (kk === 'PageDown' || kk === 'PageUp') passo(kk === 'PageDown' ? 1 : -1);
        else if (kk === 'Escape') selecionar({ t: '', i: -1 });
        else usado = false;
        if (usado) { e.preventDefault(); if (girando) girar(false); pede(); }
      });
    }
    function passo(d) {                            // percorre as obras visíveis, das mais citadas para as menos
      var vis = porCitacao.filter(function (n) { return alfa[n] > 0.5; });
      if (!vis.length) return;
      var at = sel.t === 'no' ? vis.indexOf(sel.i) : -1;
      selecionar({ t: 'no', i: vis[(at + d + vis.length) % vis.length] }, { focar: true, origem: 'teclado' });
    }

    function ajusta() {
      var r = canvas.getBoundingClientRect();
      if (r.width < 2 || r.height < 2) return;
      dpr = Math.min(global.devicePixelRatio || 1, 2);
      larg = r.width; alt = r.height;
      var w = Math.round(larg * dpr), h = Math.round(alt * dpr);
      if (canvas.width !== w || canvas.height !== h) { canvas.width = w; canvas.height = h; }
      pede();
    }
    if (global.ResizeObserver) new ResizeObserver(ajusta).observe(canvas); else global.addEventListener('resize', ajusta);
    if (mq) { var mudou = function () { reduz = mq.matches; if (reduz) { girando = false; inercia = false; if (opt.aoGiro) opt.aoGiro(false); } }; if (mq.addEventListener) mq.addEventListener('change', mudou); else if (mq.addListener) mq.addListener(mudou); }
    if (global.document && document.fonts && document.fonts.ready) document.fonts.ready.then(pede);

    // abertura: a cena se abre do centro até a posição da regra (uma vez; pulada com movimento reduzido)
    for (i = 0; i < N; i++) alfa[i] = alvoAlfa('silos')[i];
    atualizaLinhas(); ajusta();
    if (!reduz && opt.abertura !== false) {
      var fim = POS.silos, a1 = new Float32Array(alfa);
      for (i = 0; i < 3 * N; i++) pos[i] = fim[i] * 0.04;
      for (i = 0; i < N; i++) alfa[i] = 0;
      var y0 = cam.yaw - 0.55;
      anima(1150, function (q) {
        for (var n = 0; n < 3 * N; n++) pos[n] = fim[n] * (0.04 + 0.96 * q);
        for (n = 0; n < N; n++) alfa[n] = a1[n] * Math.min(1, q * 1.6);
        cam.yaw = y0 + 0.55 * q;
      });
    }
    if (opt.aoGiro) opt.aoGiro(girando);

    return {
      definirLente: definirLente, lente: function () { return lente; }, lentes: function () { return Object.keys(POS); },
      selecionar: selecionar, selecao: function () { return sel; }, recentrar: recentrar, zoom: zoom,
      girar: girar, girando: function () { return girando; }, filtrar: filtrar, redesenha: pede, ajusta: ajusta,
      vizinhas: function (n) { return viz[n]; }, passo: passo,
      margemDireita: function (m) { var m0 = margemDir; anima(240, function (q) { margemDir = m0 + (m - m0) * q; }); },
      emTela: function (n) { return [SX[n], SY[n], SR[n], SZ[n]]; },
      estado: function () { return { lente: lente, n: N, linhas: visAr.length, animando: tw.length > 0 || inercia, desenho_ms: ultDes, cam: { yaw: cam.yaw, pit: cam.pit, dist: cam.dist } }; },
      arrastou: function () { return moveu >= 6; }, limpaArrasto: function () { moveu = 0; }
    };
  }

  // ───────────────────────── abertura do relatório ─────────────────────────
  function heroi(canvas, compacto) {
    var D = { nos: compacto.map(function (r, i) { return { i: 'h' + i, l: '', a: r[0], o: r[1], s: 0, y: 0, c: r[2], g: 0, k: [r[3], r[4], r[5], r[6]], t: 0 }; }), arestas: [], triades: [] };
    return criarCena(canvas, D, { mini: true });
  }

  global.Espaco3D = { criarCena: criarCena, heroi: heroi, NOME: NOME, COR: COR, FORMA: FORMA, SOL: SOL, VERT: VERT, TETO_AFASTA: TETO_AFASTA };
})(typeof window !== 'undefined' ? window : globalThis);
