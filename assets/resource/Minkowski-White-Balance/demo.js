/*
 * 《白平衡的 p 范数：从灰色世界到 Max-RGB》一文的交互演示。
 *
 * 光源估计按 van de Weijer 等 (2007) 的 e^{n,p,σ} 框架，与 tools/minkowski_awb.py 同一套定义：
 *   n = 0：对像素值求闵可夫斯基均值（Shades of Gray；p = 1 为 Grey-World，p = ∞ 为 Max-RGB）
 *   n = 1：对各通道高斯一阶导数的模求闵可夫斯基均值（Grey-Edge）
 * 图像是 Cube++（Ershov et al. 2020，CC BY 4.0）的线性相机 RGB，扣过黑电平、缩小 4 倍。
 *
 * 显示路径固定：相机 RGB ÷ 估计光源（以 G 为基准）→ 显示矩阵 → sRGB 编码。
 * 显示矩阵与曝光只由真值光源决定，拖动 p 时画面的变化全部来自白平衡这一步。
 */
(function () {
  'use strict';

  var P_LIST = [];
  for (var i = 1; i <= 20; i++) P_LIST.push(i);
  P_LIST.push(Infinity);
  var SIGMA = 1; // Grey-Edge 的高斯尺度（像素，按缩小后的图计）

  // ------------------------------------------------------------ 数学

  function angularError(a, b) {
    var d = a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
    var na = Math.hypot(a[0], a[1], a[2]), nb = Math.hypot(b[0], b[1], b[2]);
    return Math.acos(Math.min(1, Math.max(-1, d / (na * nb)))) * 180 / Math.PI;
  }

  function mul3(M, v) {
    return [M[0] * v[0] + M[1] * v[1] + M[2] * v[2],
            M[3] * v[0] + M[4] * v[1] + M[5] * v[2],
            M[6] * v[0] + M[7] * v[1] + M[8] * v[2]];
  }

  function srgbEncode(x) {
    x = x <= 0 ? 0 : x >= 1 ? 1 : x;
    return x <= 0.0031308 ? 12.92 * x : 1.055 * Math.pow(x, 1 / 2.4) - 0.055;
  }

  function xyzToLab(xyz, white) {
    function f(t) { return t > 216 / 24389 ? Math.cbrt(t) : (24389 / 27 * t + 16) / 116; }
    var fx = f(xyz[0] / white[0]), fy = f(xyz[1] / white[1]), fz = f(xyz[2] / white[2]);
    return [116 * fy - 16, 500 * (fx - fy), 200 * (fy - fz)];
  }

  // CIEDE2000（Sharma, Wu & Dalal 2005 的写法；用其 34 组测试数据校验过）
  function deltaE00(lab1, lab2) {
    var L1 = lab1[0], a1 = lab1[1], b1 = lab1[2], L2 = lab2[0], a2 = lab2[1], b2 = lab2[2];
    var rad = Math.PI / 180;
    var C1 = Math.hypot(a1, b1), C2 = Math.hypot(a2, b2), Cm = (C1 + C2) / 2;
    var G = 0.5 * (1 - Math.sqrt(Math.pow(Cm, 7) / (Math.pow(Cm, 7) + Math.pow(25, 7))));
    var a1p = (1 + G) * a1, a2p = (1 + G) * a2;
    var C1p = Math.hypot(a1p, b1), C2p = Math.hypot(a2p, b2);
    function hue(b, ap) { if (b === 0 && ap === 0) return 0; var h = Math.atan2(b, ap) / rad; return h < 0 ? h + 360 : h; }
    var h1p = hue(b1, a1p), h2p = hue(b2, a2p);
    var dLp = L2 - L1, dCp = C2p - C1p, dhp;
    if (C1p * C2p === 0) dhp = 0;
    else if (Math.abs(h2p - h1p) <= 180) dhp = h2p - h1p;
    else if (h2p - h1p > 180) dhp = h2p - h1p - 360;
    else dhp = h2p - h1p + 360;
    var dHp = 2 * Math.sqrt(C1p * C2p) * Math.sin(dhp / 2 * rad);
    var Lpm = (L1 + L2) / 2, Cpm = (C1p + C2p) / 2, hpm;
    if (C1p * C2p === 0) hpm = h1p + h2p;
    else if (Math.abs(h1p - h2p) <= 180) hpm = (h1p + h2p) / 2;
    else if (h1p + h2p < 360) hpm = (h1p + h2p + 360) / 2;
    else hpm = (h1p + h2p - 360) / 2;
    var T = 1 - 0.17 * Math.cos((hpm - 30) * rad) + 0.24 * Math.cos(2 * hpm * rad)
          + 0.32 * Math.cos((3 * hpm + 6) * rad) - 0.20 * Math.cos((4 * hpm - 63) * rad);
    var dTheta = 30 * Math.exp(-Math.pow((hpm - 275) / 25, 2));
    var RC = 2 * Math.sqrt(Math.pow(Cpm, 7) / (Math.pow(Cpm, 7) + Math.pow(25, 7)));
    var SL = 1 + 0.015 * Math.pow(Lpm - 50, 2) / Math.sqrt(20 + Math.pow(Lpm - 50, 2));
    var SC = 1 + 0.045 * Cpm, SH = 1 + 0.015 * Cpm * T;
    var RT = -Math.sin(2 * dTheta * rad) * RC;
    return Math.sqrt(Math.pow(dLp / SL, 2) + Math.pow(dCp / SC, 2) + Math.pow(dHp / SH, 2)
                     + RT * (dCp / SC) * (dHp / SH));
  }

  // ------------------------------------------------------------ 特征与估计

  function gaussKernels(sigma) {
    var r = Math.ceil(4 * sigma), g = [], d = [], sg = 0;
    for (var k = -r; k <= r; k++) {
      var v = Math.exp(-k * k / (2 * sigma * sigma));
      g.push(v); d.push(-k / (sigma * sigma) * v); sg += v;
    }
    for (var j = 0; j < g.length; j++) { g[j] /= sg; d[j] /= sg; }
    return { r: r, g: g, d: d };
  }

  // 一维可分离卷积。边界按最近像素延拓，与 scipy.ndimage 默认的 reflect 不同，
  // 但边界一圈会被掩膜腐蚀掉，不影响结果
  function conv1d(src, w, h, k, r, horizontal) {
    var out = new Float32Array(w * h);
    for (var y = 0; y < h; y++) {
      for (var x = 0; x < w; x++) {
        var s = 0;
        for (var t = -r; t <= r; t++) {
          var xx = horizontal ? Math.min(w - 1, Math.max(0, x + t)) : x;
          var yy = horizontal ? y : Math.min(h - 1, Math.max(0, y + t));
          s += k[t + r] * src[yy * w + xx];
        }
        out[y * w + x] = s;
      }
    }
    return out;
  }

  function erode(mask, w, h, iters) {
    var cur = mask;
    for (var it = 0; it < iters; it++) {
      var nxt = new Uint8Array(w * h);
      for (var y = 1; y < h - 1; y++) {
        for (var x = 1; x < w - 1; x++) {
          var i = y * w + x;
          nxt[i] = cur[i] & cur[i - 1] & cur[i + 1] & cur[i - w] & cur[i + w];
        }
      }
      cur = nxt;
    }
    return cur;
  }

  // 返回每个通道参与求范数的样本（已除以该通道最大值，避免大 p 溢出）与尺度
  function featureSamples(img, mask, w, h, n) {
    var chans = [], valid = mask;
    if (n === 1) {
      var K = gaussKernels(SIGMA);
      valid = erode(mask, w, h, Math.ceil(3 * SIGMA) + 1);
      for (var c = 0; c < 3; c++) {
        var gx = conv1d(conv1d(img[c], w, h, K.d, K.r, true), w, h, K.g, K.r, false);
        var gy = conv1d(conv1d(img[c], w, h, K.g, K.r, true), w, h, K.d, K.r, false);
        var m = new Float32Array(w * h);
        for (var i = 0; i < m.length; i++) m[i] = Math.hypot(gx[i], gy[i]);
        chans.push(m);
      }
    } else {
      chans = img;
    }
    var count = 0;
    for (var j = 0; j < valid.length; j++) count += valid[j];
    var out = [], scale = [];
    for (var c2 = 0; c2 < 3; c2++) {
      var v = new Float32Array(count), mx = 0, q = 0;
      for (var k = 0; k < valid.length; k++) if (valid[k]) { v[q] = chans[c2][k]; if (v[q] > mx) mx = v[q]; q++; }
      if (mx === 0) mx = 1;
      for (var s = 0; s < count; s++) v[s] /= mx;
      out.push(v); scale.push(mx);
    }
    return { v: out, scale: scale };
  }

  function sweep(samples) {
    var res = [];
    for (var a = 0; a < P_LIST.length; a++) {
      var p = P_LIST[a], e = [];
      for (var c = 0; c < 3; c++) {
        var v = samples.v[c];
        if (p === Infinity) { e.push(samples.scale[c]); continue; }
        var s = 0;
        for (var i = 0; i < v.length; i++) s += Math.pow(v[i], p);
        e.push(samples.scale[c] * Math.pow(s / v.length, 1 / p));
      }
      res.push(e);
    }
    return res;
  }

  // ------------------------------------------------------------ 数据

  function fetchBin(url) {
    return fetch(url).then(function (r) {
      if (!r.ok) throw new Error(url + ' ' + r.status);
      if (/\.gz$/.test(url) && typeof DecompressionStream !== 'undefined') {
        return new Response(r.body.pipeThrough(new DecompressionStream('gzip'))).arrayBuffer();
      }
      return r.arrayBuffer();
    });
  }

  // 数据格式：w·h·3 个 uint16（线性相机 RGB，已扣黑电平，小端）+ w·h 个 uint8 掩膜
  // （0 = 不参与估计：饱和像素，以及右下角 SpyderCube 所在的矩形）
  function loadImage(base, meta) {
    return fetchBin(base + meta.file).then(function (buf) {
      var w = meta.w, h = meta.h, N = w * h;
      var u = new Uint16Array(buf, 0, 3 * N), mask = new Uint8Array(buf, 6 * N, N);
      var img = [new Float32Array(N), new Float32Array(N), new Float32Array(N)];
      for (var i = 0; i < N; i++) { img[0][i] = u[3 * i]; img[1][i] = u[3 * i + 1]; img[2][i] = u[3 * i + 2]; }
      return { img: img, mask: mask, sweeps: {} };
    });
  }

  // ------------------------------------------------------------ 界面

  var NS = 'http://www.w3.org/2000/svg';
  function el(tag, attrs, parent, ns) {
    var e = ns ? document.createElementNS(NS, tag) : document.createElement(tag);
    for (var k in attrs) if (attrs.hasOwnProperty(k)) {
      if (k === 'text') e.textContent = attrs[k]; else e.setAttribute(k, attrs[k]);
    }
    if (parent) parent.appendChild(e);
    return e;
  }

  function pLabel(p) { return p === Infinity ? '∞' : String(p); }

  function Demo(root) {
    this.root = root;
    this.base = root.getAttribute('data-base');
    this.state = { img: 0, n: 0, pIdx: 5, truth: false };
    this.cache = {};
    var self = this;
    fetch(this.base + 'images.json').then(function (r) { return r.json(); }).then(function (cfg) {
      self.cfg = cfg;
      self.build();
      self.select(0);
    }).catch(function (e) {
      root.textContent = '演示数据加载失败：' + e.message;
    });
  }

  Demo.prototype.build = function () {
    var self = this, root = this.root, cfg = this.cfg;
    root.textContent = '';
    var bar = el('div', { 'class': 'mawb-bar' }, root);
    var pick = el('div', { 'class': 'mawb-pick', role: 'group', 'aria-label': '选择图片' }, bar);
    this.picks = cfg.images.map(function (m, i) {
      var b = el('button', { type: 'button', text: m.label }, pick);
      b.addEventListener('click', function () { self.select(i); });
      return b;
    });
    // data-modes="pixel" 时只用像素法（n = 0），不显示「像素 / 边缘」开关
    this.modes = [];
    if (root.getAttribute('data-modes') !== 'pixel') {
      var mode = el('div', { 'class': 'mawb-pick', role: 'group', 'aria-label': '求范数的对象' }, bar);
      this.modes = [['像素', 0], ['边缘', 1]].map(function (t) {
        var b = el('button', { type: 'button', text: t[0] }, mode);
        b.addEventListener('click', function () { self.state.n = t[1]; self.update(true); });
        return b;
      });
    }

    var ctl = el('div', { 'class': 'mawb-ctl' }, root);
    el('label', { 'for': 'mawb-p', text: 'p' }, ctl);
    this.slider = el('input', { id: 'mawb-p', type: 'range', min: 0, max: P_LIST.length - 1, step: 1, value: this.state.pIdx }, ctl);
    this.pOut = el('output', { 'for': 'mawb-p', 'class': 'mawb-pval' }, ctl);
    this.slider.addEventListener('input', function () { self.state.pIdx = +self.slider.value; self.update(false); });
    var tl = el('label', { 'class': 'mawb-truth' }, ctl);
    this.truthBox = el('input', { type: 'checkbox' }, tl);
    tl.appendChild(document.createTextNode('按真值校正（对照）'));
    this.truthBox.addEventListener('change', function () { self.state.truth = self.truthBox.checked; self.update(false); });

    var main = el('div', { 'class': 'mawb-main' }, root);
    var figL = el('figure', { 'class': 'mawb-fig' }, main);
    this.canvas = el('canvas', { 'class': 'mawb-canvas' }, figL);
    this.caption = el('figcaption', {}, figL);

    var side = el('div', { 'class': 'mawb-side' }, main);
    var stat = el('div', { 'class': 'mawb-stat' }, side);
    el('div', { 'class': 'mawb-k', text: '角度误差' }, stat);
    this.errOut = el('div', { 'class': 'mawb-v' }, stat);
    this.faces = el('div', { 'class': 'mawb-faces' }, side);
    this.chart = el('svg', { 'class': 'mawb-chart', viewBox: '0 0 320 190', role: 'img' }, side, true);
    this.status = el('p', { 'class': 'mawb-status', 'aria-live': 'polite' }, root);
    var credit = el('p', { 'class': 'mawb-credit' }, root);
    credit.appendChild(document.createTextNode('图像：'));
    el('a', { href: 'https://github.com/Visillect/CubePlusPlus', text: 'Cube++' }, credit);
    credit.appendChild(document.createTextNode('（Ershov et al., 2020），'));
    el('a', { href: 'https://creativecommons.org/licenses/by/4.0/', text: 'CC BY 4.0' }, credit);
    credit.appendChild(document.createTextNode('；已缩小 4 倍，按文中的方法重新显示。'));
  };

  Demo.prototype.select = function (i) {
    var self = this, meta = this.cfg.images[i];
    this.state.img = i;
    this.picks.forEach(function (b, k) { b.setAttribute('aria-pressed', k === i ? 'true' : 'false'); });
    if (this.cache[i]) { this.update(true); return; }
    this.status.textContent = '正在加载 ' + meta.label + '……';
    loadImage(this.base, meta).then(function (d) {
      self.cache[i] = d;
      self.status.textContent = '';
      self.update(true);
    }).catch(function (e) { self.status.textContent = '加载失败：' + e.message; });
  };

  Demo.prototype.current = function () {
    var d = this.cache[this.state.img], n = this.state.n, meta = this.cfg.images[this.state.img];
    if (!d) return null;
    if (!d.sweeps[n]) {
      var est = sweep(featureSamples(d.img, d.mask, meta.w, meta.h, n));
      d.sweeps[n] = { est: est, err: est.map(function (e) { return angularError(e, meta.gt); }) };
    }
    return { d: d, meta: meta, sw: d.sweeps[n] };
  };

  Demo.prototype.update = function (full) {
    var cur = this.current();
    this.modes.forEach(function (b, k) { b.setAttribute('aria-pressed', k === this.state.n ? 'true' : 'false'); }, this);
    var p = P_LIST[this.state.pIdx];
    this.pOut.textContent = pLabel(p) + (p === 1 ? '（平均）' : p === Infinity ? '（最大值）' : '');
    if (!cur) return;
    var est = this.state.truth ? cur.meta.gt : cur.sw.est[this.state.pIdx];
    var err = cur.sw.err[this.state.pIdx];
    this.errOut.textContent = this.state.truth ? '0°（真值）' : err.toFixed(1) + '°';
    this.render(cur, est);
    this.renderFaces(cur, est);
    this.renderChart(cur);
    this.caption.textContent = cur.meta.caption;
  };

  // 以 G 为基准的白平衡增益：只改 R、B 的相对比例，不动整体亮度
  function gains(est) { return [est[1] / est[0], 1, est[1] / est[2]]; }

  Demo.prototype.render = function (cur, est) {
    var meta = cur.meta, w = meta.w, h = meta.h, img = cur.d.img;
    var cv = this.canvas;
    if (cv.width !== w) { cv.width = w; cv.height = h; }
    var ctx = cv.getContext('2d'), out = ctx.createImageData(w, h), px = out.data;
    var g = gains(est), M = meta.M_rgb, k = meta.exposure;
    var m0 = M[0] * g[0] * k, m1 = M[1] * k, m2 = M[2] * g[2] * k,
        m3 = M[3] * g[0] * k, m4 = M[4] * k, m5 = M[5] * g[2] * k,
        m6 = M[6] * g[0] * k, m7 = M[7] * k, m8 = M[8] * g[2] * k;
    var lut = this.lut || (this.lut = (function () {
      var t = new Uint8ClampedArray(4097);
      for (var i = 0; i <= 4096; i++) t[i] = Math.round(255 * srgbEncode(i / 4096));
      return t;
    })());
    function enc(x) { return lut[x <= 0 ? 0 : x >= 1 ? 4096 : (x * 4096) | 0]; }
    for (var i = 0, j = 0; i < w * h; i++, j += 4) {
      var r = img[0][i], gg = img[1][i], b = img[2][i];
      px[j] = enc(m0 * r + m1 * gg + m2 * b);
      px[j + 1] = enc(m3 * r + m4 * gg + m5 * b);
      px[j + 2] = enc(m6 * r + m7 * gg + m8 * b);
      px[j + 3] = 255;
    }
    ctx.putImageData(out, 0, 0);
    // 右下角不参与估计的矩形
    var ex = meta.exclude;
    ctx.save();
    ctx.setLineDash([6, 4]); ctx.lineWidth = 1.5; ctx.strokeStyle = 'rgba(255,255,255,0.85)';
    ctx.strokeRect(ex[0] + 1, ex[1] + 1, w - ex[0] - 2, h - ex[1] - 2);
    ctx.restore();
  };

  Demo.prototype.renderFaces = function (cur, est) {
    var meta = cur.meta, box = this.faces, g = gains(est), k = meta.exposure;
    box.textContent = '';
    (meta.faces || []).forEach(function (f) {
      var cam = [f.rgb[0] * g[0] * k, f.rgb[1] * k, f.rgb[2] * g[2] * k];
      var lin = mul3(meta.M_rgb, cam), xyz = mul3(meta.M_xyz, cam);
      var lab = xyzToLab(xyz, meta.white);
      var de = deltaE00(lab, [lab[0], 0, 0]);
      var row = el('div', { 'class': 'mawb-face' }, box);
      var sw = el('span', { 'class': 'mawb-swatch' }, row);
      sw.style.background = 'rgb(' + lin.map(function (x) { return Math.round(255 * srgbEncode(x)); }).join(',') + ')';
      el('span', { 'class': 'mawb-fk', text: f.label }, row);
      el('span', { 'class': 'mawb-fv', text: 'ΔE00 ' + de.toFixed(1) }, row);
    });
  };

  Demo.prototype.renderChart = function (cur) {
    var svg = this.chart, err = cur.sw.err, self = this;
    svg.textContent = '';
    var W = 320, H = 190, L = 36, R = 12, T = 22, B = 30;
    var ymax = Math.max(2, Math.ceil(Math.max.apply(null, err) / 2) * 2);
    // p = 1..20 等距排开；∞ 与 20 之间空出两格，用虚线相连，表示中间不连续
    var LAST = P_LIST.length - 1, SPAN = LAST + 2;
    function pos(i) { return i === LAST ? SPAN : i; }
    function X(i) { return L + (W - L - R) * pos(i) / SPAN; }
    function Y(v) { return T + (H - T - B) * (1 - v / ymax); }
    el('text', { x: L, y: 13, 'class': 'mawb-ct', text: '这张图的角度误差随 p 的变化（度）' }, svg, true);
    var step = ymax > 16 ? 5 : ymax > 8 ? 4 : 2;
    for (var t = 0; t <= ymax; t += step) {
      el('line', { x1: L, x2: W - R, y1: Y(t), y2: Y(t), 'class': 'mawb-grid' }, svg, true);
      el('text', { x: L - 6, y: Y(t) + 4, 'class': 'mawb-tick', 'text-anchor': 'end', text: t }, svg, true);
    }
    [0, 4, 9, 14, 19, LAST].forEach(function (i) {
      el('text', { x: X(i), y: H - B + 16, 'class': 'mawb-tick', 'text-anchor': 'middle', text: pLabel(P_LIST[i]) }, svg, true);
    });
    el('text', { x: W - R, y: H - 2, 'class': 'mawb-tick', 'text-anchor': 'end', text: 'p' }, svg, true);
    var d = err.slice(0, LAST).map(function (v, i) { return (i ? 'L' : 'M') + X(i).toFixed(1) + ' ' + Y(v).toFixed(1); }).join(' ');
    el('path', { d: d, 'class': 'mawb-line' }, svg, true);
    el('path', { d: 'M' + X(LAST - 1).toFixed(1) + ' ' + Y(err[LAST - 1]).toFixed(1) + 'L' + X(LAST).toFixed(1) + ' ' + Y(err[LAST]).toFixed(1),
                 'class': 'mawb-line mawb-gap' }, svg, true);
    el('circle', { cx: X(LAST), cy: Y(err[LAST]), r: 3, 'class': 'mawb-end' }, svg, true);
    var best = err.indexOf(Math.min.apply(null, err));
    el('circle', { cx: X(best), cy: Y(err[best]), r: 4, 'class': 'mawb-best' }, svg, true);
    el('text', { x: X(best), y: Y(err[best]) + 16, 'class': 'mawb-tick', 'text-anchor': 'middle', text: '最小 p=' + pLabel(P_LIST[best]) }, svg, true);
    var i0 = this.state.pIdx;
    el('circle', { cx: X(i0), cy: Y(err[i0]), r: 5, 'class': 'mawb-now' }, svg, true);
    // 悬停：显示该 p 的夹角，点击跳到该 p
    var tip = el('text', { 'class': 'mawb-tip', x: 0, y: 0 }, svg, true);
    var hit = el('rect', { x: L, y: T, width: W - L - R, height: H - T - B, fill: 'transparent' }, svg, true);
    function idxAt(ev) {
      var pt = svg.createSVGPoint(); pt.x = ev.clientX; pt.y = ev.clientY;
      var q = pt.matrixTransform(svg.getScreenCTM().inverse());
      var u = (q.x - L) / (W - L - R) * SPAN;
      return u > (LAST - 1 + SPAN) / 2 ? LAST : Math.max(0, Math.min(LAST - 1, Math.round(u)));
    }
    hit.addEventListener('mousemove', function (ev) {
      var i = idxAt(ev);
      tip.setAttribute('x', Math.min(W - R - 60, X(i) + 6)); tip.setAttribute('y', Math.max(T + 10, Y(err[i]) - 8));
      tip.textContent = 'p=' + pLabel(P_LIST[i]) + '：' + err[i].toFixed(1) + '°';
    });
    hit.addEventListener('mouseleave', function () { tip.textContent = ''; });
    hit.addEventListener('click', function (ev) {
      self.state.pIdx = idxAt(ev); self.slider.value = self.state.pIdx; self.update(false);
    });
    svg.setAttribute('aria-label', '角度误差随 p 的变化，最小值在 p=' + pLabel(P_LIST[best]) + '，为 ' + err[best].toFixed(1) + ' 度');
  };

  function init() {
    var roots = document.querySelectorAll('.mawb-demo');
    for (var i = 0; i < roots.length; i++) new Demo(roots[i]);
  }
  if (typeof document !== 'undefined') {
    if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
    else init();
  }

  // 供 node 下的自测使用
  if (typeof module !== 'undefined') module.exports = { mul3: mul3, xyzToLab: xyzToLab, srgbEncode: srgbEncode, deltaE00: deltaE00, angularError: angularError, sweep: sweep, featureSamples: featureSamples, P_LIST: P_LIST };
})();
