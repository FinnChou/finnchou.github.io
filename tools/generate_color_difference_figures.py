#!/usr/bin/env python3
"""生成《色差公式的演进：从 CIELAB 到 CIEDE2000》一文的插图。

依赖 Pillow 与 numpy；绘图工具与 sRGB 矩阵从同目录的 generate_cie_xyz_figures.py
导入，MacAdam 椭圆的数据与 xy 坐标变换从 generate_uniform_color_space_figures.py 导入。

用法：
    python3 tools/generate_color_difference_figures.py              # 全部
    python3 tools/generate_color_difference_figures.py --only weights
    python3 tools/generate_color_difference_figures.py --check      # 打印正文引用的数值

图里的数据：
    - MacAdam (1942) 颜色辨别椭圆：同《色差与均匀色空间》一文（W&S 表 2(5.4.1) 的拟合值）。
      椭圆边界逐点换算到 a*b*：白点取 D65，亮度统一取 L* = 50 对应的 Y。
      MacAdam 的实验在恒定亮度下进行；色度不变时 a*、b* 都与 Y 的立方根成正比，
      Y 取别的值只会把整张图等比缩放，椭圆之间的相对大小与形状不变
    - CMC(l:c)、CIE94、CIEDE2000 的权重函数与等色差轮廓：按公式直接计算。
      CIEDE2000 的实现用 Sharma et al. (2005) 公布的 34 组测试数据校验（--check）
    - RGB 误差与 ΔE00：sRGB 按 IEC 61966-2-1 的传递函数与矩阵（D65），
      在基准色周围沿均匀分布的随机方向偏移固定的欧氏距离，统计 ΔE00 的分布
    - LCH 分解为模式图，不承载数据
"""

import argparse
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from generate_cie_xyz_figures import (  # noqa: E402
    SS, WHITE, PANEL, GRID, BORDER, INK, MUTED, CURVE, ACCENT, RED, GREEN, BLUE,
    M_XYZ2RGB, _encode, font, ifont, canvas, finish, text, rect, line, polyline, poly,
    ellipse, arrow, dashed, callout, Axes,
)
from generate_uniform_color_space_figures import macadam_ellipses  # noqa: E402

ORANGE = (214, 130, 40)
D65 = np.array([0.95047, 1.0, 1.08883])
M_RGB2XYZ = np.linalg.inv(M_XYZ2RGB)

# Sharma, Wu & Dalal (2005) 的 CIEDE2000 测试数据：L1 a1 b1  L2 a2 b2  ΔE00
SHARMA_2005 = """
50.0000 2.6772 -79.7751  50.0000 0.0000 -82.7485  2.0425
50.0000 3.1571 -77.2803  50.0000 0.0000 -82.7485  2.8615
50.0000 2.8361 -74.0200  50.0000 0.0000 -82.7485  3.4412
50.0000 -1.3802 -84.2814  50.0000 0.0000 -82.7485  1.0000
50.0000 -1.1848 -84.8006  50.0000 0.0000 -82.7485  1.0000
50.0000 -0.9009 -85.5211  50.0000 0.0000 -82.7485  1.0000
50.0000 0.0000 0.0000  50.0000 -1.0000 2.0000  2.3669
50.0000 -1.0000 2.0000  50.0000 0.0000 0.0000  2.3669
50.0000 2.4900 -0.0010  50.0000 -2.4900 0.0009  7.1792
50.0000 2.4900 -0.0010  50.0000 -2.4900 0.0010  7.1792
50.0000 2.4900 -0.0010  50.0000 -2.4900 0.0011  7.2195
50.0000 2.4900 -0.0010  50.0000 -2.4900 0.0012  7.2195
50.0000 -0.0010 2.4900  50.0000 0.0009 -2.4900  4.8045
50.0000 -0.0010 2.4900  50.0000 0.0010 -2.4900  4.8045
50.0000 -0.0010 2.4900  50.0000 0.0011 -2.4900  4.7461
50.0000 2.5000 0.0000  50.0000 0.0000 -2.5000  4.3065
50.0000 2.5000 0.0000  73.0000 25.0000 -18.0000  27.1492
50.0000 2.5000 0.0000  61.0000 -5.0000 29.0000  22.8977
50.0000 2.5000 0.0000  56.0000 -27.0000 -3.0000  31.9030
50.0000 2.5000 0.0000  58.0000 24.0000 15.0000  19.4535
50.0000 2.5000 0.0000  50.0000 3.1736 0.5854  1.0000
50.0000 2.5000 0.0000  50.0000 3.2972 0.0000  1.0000
50.0000 2.5000 0.0000  50.0000 1.8634 0.5757  1.0000
50.0000 2.5000 0.0000  50.0000 3.2592 0.3350  1.0000
60.2574 -34.0099 36.2677  60.4626 -34.1751 39.4387  1.2644
63.0109 -31.0961 -5.8663  62.8187 -29.7946 -4.0864  1.2630
61.2901 3.7196 -5.3901  61.4292 2.2480 -4.9620  1.8731
35.0831 -44.1164 3.7933  35.0232 -40.0716 1.5901  1.8645
22.7233 20.0904 -46.6940  23.0331 14.9730 -42.5619  2.0373
36.4612 47.8580 18.3852  36.2715 50.5065 21.2231  1.4146
90.8027 -2.0831 1.4410  91.1528 -1.6435 0.0447  1.4441
90.9257 -0.5406 -0.9208  88.6381 -0.8985 -0.7239  1.5381
6.7747 -0.2908 -2.4247  5.8714 -0.0985 -2.2286  0.6377
2.0776 0.0795 -1.1350  0.9033 -0.0636 -0.5514  0.9082
"""


# ---------------------------------------------------------------- 色空间换算
def _f(t):
    d = 6 / 29
    return np.where(t > d ** 3, np.cbrt(t), t / (3 * d * d) + 4 / 29)


def _finv(t):
    d = 6 / 29
    return np.where(t > d, t ** 3, 3 * d * d * (t - 4 / 29))


def xyz_to_lab(xyz):
    fx, fy, fz = (_f(np.asarray(xyz, float)[..., k] / D65[k]) for k in range(3))
    return np.stack([116 * fy - 16, 500 * (fx - fy), 200 * (fy - fz)], axis=-1)


def lab_to_xyz(lab):
    lab = np.asarray(lab, float)
    fy = (lab[..., 0] + 16) / 116
    fx, fz = fy + lab[..., 1] / 500, fy - lab[..., 2] / 200
    return np.stack([D65[0] * _finv(fx), D65[1] * _finv(fy), D65[2] * _finv(fz)], axis=-1)


def decode(s):
    """sRGB 编码值 -> 线性值（IEC 61966-2-1）。"""
    s = np.asarray(s, float)
    return np.where(s <= 0.04045, s / 12.92, ((np.abs(s) + 0.055) / 1.055) ** 2.4)


def linear_to_lab(rgb):
    return xyz_to_lab(np.asarray(rgb, float) @ M_RGB2XYZ.T)


def srgb_to_lab(s):
    return linear_to_lab(decode(s))


def lab_to_linear(lab):
    return lab_to_xyz(lab) @ M_XYZ2RGB.T


def lch(L, C, h):
    return np.array([L, C * math.cos(math.radians(h)), C * math.sin(math.radians(h))])


def xy_to_ab(x, y, Y):
    X, Z = x / y * Y, (1 - x - y) / y * Y
    lab = xyz_to_lab(np.array([X, Y, Z]))
    return float(lab[1]), float(lab[2])


# ---------------------------------------------------------------- 色差公式
def _hue(a, b):
    return np.degrees(np.arctan2(b, a)) % 360


def de76(lab1, lab2):
    return np.linalg.norm(np.asarray(lab1, float) - np.asarray(lab2, float), axis=-1)


def _lch_diff(lab1, lab2):
    """ΔL*、ΔC*、ΔH*（ΔH* 取 ΔE*ab² = ΔL*² + ΔC*² + ΔH*² 的余量）与参考色的 C*、h。"""
    L1, a1, b1 = np.moveaxis(np.asarray(lab1, float), -1, 0)
    L2, a2, b2 = np.moveaxis(np.asarray(lab2, float), -1, 0)
    C1, C2 = np.hypot(a1, b1), np.hypot(a2, b2)
    dL, dC = L1 - L2, C1 - C2
    dH2 = np.maximum((a1 - a2) ** 2 + (b1 - b2) ** 2 - dC ** 2, 0)
    return dL, dC, dH2, L1, C1, _hue(a1, b1)


def cmc_weights(L1, C1, h1):
    SL = np.where(L1 < 16, 0.511, 0.040975 * L1 / (1 + 0.01765 * L1))
    SC = 0.0638 * C1 / (1 + 0.0131 * C1) + 0.638
    T = np.where((h1 > 164) & (h1 < 345), 0.56 + np.abs(0.2 * np.cos(np.radians(h1 + 168))),
                 0.36 + np.abs(0.4 * np.cos(np.radians(h1 + 35))))
    F = np.sqrt(C1 ** 4 / (C1 ** 4 + 1900))
    return SL, SC, SC * (F * T + 1 - F)


def de_cmc(lab1, lab2, l=2.0, c=1.0):
    """CMC(l:c)，lab1 为参考色（权重按参考色计算）。"""
    dL, dC, dH2, L1, C1, h1 = _lch_diff(lab1, lab2)
    SL, SC, SH = cmc_weights(L1, C1, h1)
    return np.sqrt((dL / (l * SL)) ** 2 + (dC / (c * SC)) ** 2 + dH2 / SH ** 2)


def cie94_weights(C):
    return 1.0, 1 + 0.045 * C, 1 + 0.015 * C


def de94(lab1, lab2):
    """CIE94，参数因子 kL = kC = kH = 1，lab1 为参考色。"""
    dL, dC, dH2, _, C1, _ = _lch_diff(lab1, lab2)
    SL, SC, SH = cie94_weights(C1)
    return np.sqrt((dL / SL) ** 2 + (dC / SC) ** 2 + dH2 / SH ** 2)


def ciede2000_T(H):
    r = np.radians
    return (1 - 0.17 * np.cos(r(H - 30)) + 0.24 * np.cos(r(2 * H)) + 0.32 * np.cos(r(3 * H + 6))
            - 0.20 * np.cos(r(4 * H - 63)))


def ciede2000_SL(L):
    return 1 + 0.015 * (L - 50) ** 2 / np.sqrt(20 + (L - 50) ** 2)


def de00(lab1, lab2, terms=False, no_rt=False):
    """CIEDE2000（Sharma et al., 2005 的写法），kL = kC = kH = 1。"""
    L1, a1, b1 = np.moveaxis(np.asarray(lab1, float), -1, 0)
    L2, a2, b2 = np.moveaxis(np.asarray(lab2, float), -1, 0)
    Cb = (np.hypot(a1, b1) + np.hypot(a2, b2)) / 2
    G = 0.5 * (1 - np.sqrt(Cb ** 7 / (Cb ** 7 + 25.0 ** 7)))
    a1p, a2p = a1 * (1 + G), a2 * (1 + G)
    C1p, C2p = np.hypot(a1p, b1), np.hypot(a2p, b2)
    h1p = np.where((a1p == 0) & (b1 == 0), 0, _hue(a1p, b1))
    h2p = np.where((a2p == 0) & (b2 == 0), 0, _hue(a2p, b2))
    zero = C1p * C2p == 0
    dh = h2p - h1p
    dh = np.where(dh > 180, dh - 360, np.where(dh < -180, dh + 360, dh))
    dh = np.where(zero, 0, dh)
    dL, dC = L2 - L1, C2p - C1p
    dH = 2 * np.sqrt(C1p * C2p) * np.sin(np.radians(dh / 2))
    Lb, Cbp = (L1 + L2) / 2, (C1p + C2p) / 2
    hs = h1p + h2p
    Hb = np.where(zero, hs, np.where(np.abs(h1p - h2p) <= 180, hs / 2,
                                     np.where(hs < 360, (hs + 360) / 2, (hs - 360) / 2)))
    T = ciede2000_T(Hb)
    SL, SC, SH = ciede2000_SL(Lb), 1 + 0.045 * Cbp, 1 + 0.015 * Cbp * T
    dtheta = 30 * np.exp(-((Hb - 275) / 25) ** 2)
    RC = 2 * np.sqrt(Cbp ** 7 / (Cbp ** 7 + 25.0 ** 7))
    RT = -np.sin(np.radians(2 * dtheta)) * RC
    if no_rt:
        RT = 0 * RT
    out = np.sqrt((dL / SL) ** 2 + (dC / SC) ** 2 + (dH / SH) ** 2 + RT * (dC / SC) * (dH / SH))
    if terms:
        return out, dict(G=G, SL=SL, SC=SC, SH=SH, T=T, RT=RT, Hb=Hb)
    return out


def sharma_check():
    rows = np.array([[float(v) for v in ln.split()] for ln in SHARMA_2005.strip().splitlines()])
    got = de00(rows[:, 0:3], rows[:, 3:6])
    return len(rows), float(np.max(np.abs(got - rows[:, 6])))


# ---------------------------------------------------------------- 等色差轮廓
def contour(center, fn, level=1.0, n=180):
    """以 center 为参考色，在 a*b* 平面上求 fn = level 的轮廓（逐方向二分）。"""
    c = np.asarray(center, float)
    pts = []
    for k in range(n):
        th = 2 * math.pi * k / n
        u = np.array([0.0, math.cos(th), math.sin(th)])
        lo, hi = 0.0, 1.0
        while fn(c, c + hi * u) < level:
            hi *= 2
        for _ in range(50):
            mid = (lo + hi) / 2
            if fn(c, c + mid * u) < level:
                lo = mid
            else:
                hi = mid
        pts.append((lo + hi) / 2 * u)
    return np.array(pts)


def contour_axes(pts):
    """轮廓（相对中心的点列）的长短半轴与长轴方向（度，0～180）。"""
    P = pts[:, 1:]
    r = np.hypot(P[:, 0], P[:, 1])
    i, j = int(np.argmax(r)), int(np.argmin(r))
    return r[i], r[j], math.degrees(math.atan2(P[i, 1], P[i, 0])) % 180


# ---------------------------------------------------------------- RGB 误差 -> ΔE00
RGB_STEP = 0.004   # 欧氏长度，约为 8 位图像的 1 个灰阶；对应的 ΔE00 基本落在 0～5 以内
_RNG = np.random.default_rng(2026)
DIRS = _RNG.normal(size=(4000, 3))
DIRS /= np.linalg.norm(DIRS, axis=1, keepdims=True)


def rgb_step_de(lab0, domain):
    """基准色 lab0 在 sRGB 编码值（domain='srgb'）或线性 sRGB（'linear'）上，
    沿 DIRS 的各个方向偏移 RGB_STEP，返回各方向的 ΔE00。"""
    lin0 = lab_to_linear(lab0)
    if domain == "linear":
        p0, p1 = lin0, lin0 + RGB_STEP * DIRS
        l0, l1 = linear_to_lab(p0), linear_to_lab(p1)
    else:
        s0 = _encode(np.clip(lin0, 0, 1))
        p0, p1 = s0, s0 + RGB_STEP * DIRS
        l0, l1 = srgb_to_lab(p0), srgb_to_lab(p1)
    return de00(np.broadcast_to(l0, l1.shape), l1)


def in_gamut(lab0, margin=RGB_STEP):
    lin = lab_to_linear(lab0)
    s = _encode(np.clip(lin, 0, 1))
    return bool((lin >= margin).all() and (lin <= 1 - margin).all()
                and (s >= margin).all() and (s <= 1 - margin).all())


# ---------------------------------------------------------------- 作图小工具
PURPLE = (132, 82, 170)
BAND = (214, 220, 240)
BAND2 = (246, 214, 204)


def lab_rgb8(lab):
    """L*a*b* -> sRGB 8 bit 显示色，超出色域的分量裁剪（只作示意）。"""
    lin = np.clip(lab_to_linear(lab), 0, 1)
    return tuple(int(v * 255 + 0.5) for v in _encode(lin))


def ab_panel(d, im, box, ar, br, step, fx, L=50, tint=170):
    """a*b* 平面：按 L* 着色（裁剪到 sRGB）后蒙一层白，再画坐标框。"""
    from PIL import Image
    ax = Axes(d, box, ar, br)
    xt = list(range(int(math.ceil(ar[0] / step) * step), int(ar[1]) + 1, step))
    yt = list(range(int(math.ceil(br[0] / step) * step), int(br[1]) + 1, step))
    ax.frame(xt, yt, fx)
    w, h = int((box[2] - box[0]) * SS), int((box[3] - box[1]) * SS)
    a = np.linspace(ar[0], ar[1], w)[None, :].repeat(h, 0)
    b = np.linspace(br[1], br[0], h)[:, None].repeat(w, 1)
    lab = np.stack([np.full_like(a, L), a, b], axis=-1)
    lin = np.clip(lab_to_linear(lab), 0, 1)
    rgb = (_encode(lin) * 255 + 0.5).astype(np.uint8)
    img = Image.fromarray(rgb, "RGB")
    im.paste(img, (int(box[0] * SS), int(box[1] * SS)))
    x0, y0, x1, y1 = [int(v * SS) for v in box]
    lay = Image.new("RGBA", (x1 - x0, y1 - y0), (255, 255, 255, tint))
    im.paste(lay, (x0, y0), lay)
    ax.grid(xt, yt)
    o = ax.px(0, 0)
    line(d, (box[0], o[1], box[2], o[1]), fill=MUTED, width=1)
    line(d, (o[0], box[1], o[0], box[3]), fill=MUTED, width=1)
    return ax


def closed(d, pts, col, width=1.6):
    polyline(d, list(pts) + [pts[0]], fill=col, width=width)


def legend_line(d, x, y, col, label, f, dash=False, width=2.4):
    if dash:
        dashed(d, (x, y), (x + 28, y), fill=col, width=width, dash=7, gap=5)
    else:
        line(d, (x, y, x + 28, y), fill=col, width=width)
    text(d, (x + 36, y), label, f, fill=col, anchor="lm")


def band(d, ax, xs, lo, hi, fill):
    pts = [ax.px(x, y) for x, y in zip(xs, hi)] + [ax.px(x, y) for x, y in zip(xs[::-1], lo[::-1])]
    poly(d, pts, fill=fill)


# ==========================================================================
# 图 1：MacAdam 椭圆画到 a*b* 平面上
# ==========================================================================
MAC_SCALE = 10.0
MAC_L = 50.0


def macadam_ab():
    """[(中心 a*b*, 边界点列 a*b*（未放大）)]。"""
    Y = ((MAC_L + 16) / 116) ** 3
    out = []
    for x0, y0, a, b, th in macadam_ellipses():
        c = np.array(xy_to_ab(x0, y0, Y))
        pts = []
        for k in range(120):
            t = 2 * math.pi * k / 120
            dx, dy = a * math.cos(t), b * math.sin(t)
            x = x0 + dx * math.cos(th) - dy * math.sin(th)
            y = y0 + dx * math.sin(th) + dy * math.cos(th)
            pts.append(np.array(xy_to_ab(x, y, Y)) - c)
        out.append((c, np.array(pts)))
    return out


def macadam_ab_stats():
    rows = []
    for c, P in macadam_ab():
        w, V = np.linalg.eigh(np.cov(P.T))
        s = np.sqrt(2 * w[::-1])
        rows.append((c[0], c[1], math.hypot(*c), s[0], s[1]))
    return np.array(rows)


def fig_macadam_ab(out):
    W, H = 900, 790
    im, d = canvas(W, H)
    fx, fs = font(13), font(12)
    ar, br = (-130, 140), (-170, 60)
    box = (90, 50, 850, 50 + (850 - 90) * (br[1] - br[0]) / (ar[1] - ar[0]))
    ax = ab_panel(d, im, box, ar, br, 20, fx, tint=185)
    for c, P in macadam_ab():
        pp = [ax.px(*(c + MAC_SCALE * p)) for p in P]
        closed(d, pp, INK, 1.5)
        px, py = ax.px(*c)
        ellipse(d, (px - 1.8, py - 1.8, px + 1.8, py + 1.8), fill=INK)
    # 参照圆：半径 1，同样放大 10 倍
    cx, cy = ax.px(-100, -150)
    r = ax.px(-100 + MAC_SCALE, -150)[0] - cx
    ellipse(d, (cx - r, cy - r, cx + r, cy + r), outline=ACCENT, width=1.6)
    text(d, (cx + r + 10, cy), "参照：半径为 1 的圆（同样放大 10 倍）", fs, fill=ACCENT, anchor="lm")
    callout(d, (104, 300, 330, 350), "绿色一侧：彩度越高，椭圆越长", fs, tail=ax.px(-109.7, 44.1))
    callout(d, (104, 460, 300, 496), "中性色附近：椭圆最小", fs, tail=ax.px(-0.6, -2.1))
    callout(d, (104, 540, 330, 590), "蓝～紫一侧：椭圆细长，\n长短轴之比可达 10 倍以上", fs, tail=ax.px(52.9, -86.0))
    text(d, ((box[0] + box[2]) / 2, box[3] + 40), "a*", ifont(18))
    text(d, (40, box[1]), "b*", ifont(18))
    text(d, (W / 2, 24), "MacAdam 椭圆（1942）在 CIELAB a*b* 平面上（椭圆放大 10 倍）", fx)
    text(d, (W / 2, H - 18), "白点 D65；亮度统一取 L* = 50 对应的值，换成别的亮度只会把整张图等比缩放；底色只作示意",
         fs, fill=MUTED)
    finish(im, os.path.join(out, "macadam-ab.png"))


# ==========================================================================
# 图 2：ΔE*ab 拆成明度、彩度、色相三个分量（模式图）
# ==========================================================================

def fig_lch(out):
    W, H = 760, 520
    im, d = canvas(W, H)
    fs, fb = font(12), font(13, bold=True)
    fi = ifont(17)
    o = (110, 440)
    arrow(d, o, (o[0] + 560, o[1]), fill=INK, width=1.4, head=9)
    arrow(d, o, (o[0], o[1] - 410), fill=INK, width=1.4, head=9)
    text(d, (o[0] + 576, o[1]), "a*", fi)
    text(d, (o[0], o[1] - 424), "b*", fi)
    text(d, (o[0] - 14, o[1] + 14), "O", fi)
    R1, R2 = 300, 380
    t1, t2 = math.radians(38), math.radians(50)
    P = (o[0] + R1 * math.cos(t1), o[1] - R1 * math.sin(t1))
    Q = (o[0] + R2 * math.cos(t2), o[1] - R2 * math.sin(t2))
    K = (o[0] + R2 * math.cos(t1), o[1] - R2 * math.sin(t1))
    # 两个彩度圆弧与两条径向线
    for R, col in ((R1, BORDER), (R2, BORDER)):
        pts = [(o[0] + R * math.cos(math.radians(a)), o[1] - R * math.sin(math.radians(a)))
               for a in np.linspace(8, 82, 120)]
        polyline(d, pts, fill=col, width=1.2)
    for t in (t1, t2):
        dashed(d, o, (o[0] + (R2 + 30) * math.cos(t), o[1] - (R2 + 30) * math.sin(t)), fill=MUTED, width=1)
    # 色相角
    for t, r, lab in ((t1, 70, "h1"), (t2, 100, "h2")):
        pts = [(o[0] + r * math.cos(a), o[1] - r * math.sin(a)) for a in np.linspace(0, t, 40)]
        polyline(d, pts, fill=MUTED, width=1.2)
        text(d, (o[0] + (r + 16) * math.cos(t / 2), o[1] - (r + 16) * math.sin(t / 2)), lab, fi, fill=MUTED)
    # ΔC：沿径向；ΔH：沿彩度圆弧（近似为垂直于径向的分量）
    line(d, (P[0], P[1], K[0], K[1]), fill=ACCENT, width=3)
    arc_pts = [(o[0] + R2 * math.cos(a), o[1] - R2 * math.sin(a)) for a in np.linspace(t1, t2, 40)]
    polyline(d, arc_pts, fill=GREEN, width=3)
    line(d, (P[0], P[1], Q[0], Q[1]), fill=CURVE, width=2.4)
    for pt, lab, anc, off in ((P, "P（参考色）", "lt", (10, 4)), (Q, "Q", "rb", (-8, -6))):
        ellipse(d, (pt[0] - 5, pt[1] - 5, pt[0] + 5, pt[1] + 5), fill=INK, outline=WHITE, width=1)
        text(d, (pt[0] + off[0], pt[1] + off[1]), lab, fb, anchor=anc)
    mid = ((P[0] + K[0]) / 2, (P[1] + K[1]) / 2)
    text(d, (mid[0] + 14, mid[1] + 6), "ΔC*", font(14, bold=True), fill=ACCENT, anchor="lt")
    am = arc_pts[20]
    text(d, (am[0] + 14, am[1] - 4), "ΔH*", font(14, bold=True), fill=GREEN, anchor="lm")
    pq = ((P[0] + Q[0]) / 2, (P[1] + Q[1]) / 2)
    text(d, (pq[0] - 12, pq[1]), "ΔE*ab（只看 a*b* 平面）", fs, fill=CURVE, anchor="rm")
    callout(d, (430, 360, 740, 430), "ΔC*：彩度之差，沿径向\nΔH*：色相之差，沿彩度圆的切向，\n换算成与 a*、b* 相同的单位", fs)
    text(d, (W / 2, 24), "把 a*b* 平面上的色差拆成彩度与色相两个方向（模式图）", font(13))
    text(d, (W / 2, H - 22), "ΔL* 沿垂直于纸面的 L* 轴，图中未画出；(ΔE*ab)^2 = (ΔL*)^2 + (ΔC*)^2 + (ΔH*)^2", fs, fill=MUTED)
    finish(im, os.path.join(out, "lch-decomposition.png"))


# ==========================================================================
# 图 3：三个公式的权重函数
# ==========================================================================

PANELS3 = ((70, 90, 335, 380), (390, 90, 655, 380), (710, 90, 975, 380))


def fig_weights(out):
    W, H = 1010, 500
    im, d = canvas(W, H)
    fx, fs, fb = font(13), font(12), font(13, bold=True)
    boxes = PANELS3

    # (a) S_L
    ax = Axes(d, boxes[0], (0, 100), (0, 2.5))
    ax.frame(list(range(0, 101, 20)), [0, 0.5, 1.0, 1.5, 2.0, 2.5], fx, yfmt="%.1f", xlabel="L*")
    text(d, ((boxes[0][0] + boxes[0][2]) / 2, 66), "明度权重 SL", fb)
    Ls = np.linspace(0, 100, 401)
    SLc, _, _ = cmc_weights(Ls, np.zeros_like(Ls), np.zeros_like(Ls))
    ax.plot(Ls, SLc, fill=ORANGE, width=2.4)
    ax.plot(Ls, np.ones_like(Ls), fill=MUTED, width=2.2)
    ax.plot(Ls, ciede2000_SL(Ls), fill=CURVE, width=2.6)

    # (b) S_C
    ax = Axes(d, boxes[1], (0, 100), (0, 6))
    ax.frame(list(range(0, 101, 20)), list(range(0, 7)), fx, xlabel="C*")
    text(d, ((boxes[1][0] + boxes[1][2]) / 2, 66), "彩度权重 SC", fb)
    Cs = np.linspace(0, 100, 401)
    _, SCc, _ = cmc_weights(np.full_like(Cs, 50), Cs, np.zeros_like(Cs))
    ax.plot(Cs, SCc, fill=ORANGE, width=2.4)
    ax.plot(Cs, 1 + 0.045 * Cs, fill=CURVE, width=2.6)
    for k in range(0, 394, 12):
        p0, p1 = ax.px(Cs[k], 1 + 0.045 * Cs[k]), ax.px(Cs[k + 6], 1 + 0.045 * Cs[k + 6])
        line(d, (*p0, *p1), fill=MUTED, width=2.2)

    # (c) S_H，C* = 40
    ax = Axes(d, boxes[2], (0, 360), (0, 3))
    ax.frame(list(range(0, 361, 60)), [0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0], fx, yfmt="%.1f", xlabel="色相角 h（°）")
    text(d, ((boxes[2][0] + boxes[2][2]) / 2, 66), "色相权重 SH（C* = 40）", fb)
    hs = np.linspace(0, 360, 721)
    _, _, SHc = cmc_weights(np.full_like(hs, 50), np.full_like(hs, 40), hs)
    ax.plot(hs, SHc, fill=ORANGE, width=2.4)
    ax.plot(hs, np.full_like(hs, 1 + 0.015 * 40), fill=MUTED, width=2.2)
    ax.plot(hs, 1 + 0.015 * 40 * ciede2000_T(hs), fill=CURVE, width=2.6)

    lx = 260
    for k, (col, lab) in enumerate(((ORANGE, "CMC(l:c)"), (MUTED, "CIE94"), (CURVE, "CIEDE2000"))):
        legend_line(d, lx + 190 * k, 446, col, lab, fx)
    text(d, (W / 2, 24), "三个色差公式的权重函数：权重越大，同样的 ΔL*、ΔC*、ΔH* 折算出的色差越小", fx)
    text(d, (W / 2, H - 18), "中图里 CIE94（虚线）与 CIEDE2000 的 SC 公式相同（CIEDE2000 用 G 修正后的彩度）；CMC 的权重按参考色计算",
         fs, fill=MUTED)
    finish(im, os.path.join(out, "weighting-functions.png"))


# ==========================================================================
# 图 4：CIEDE2000 的等色差轮廓
# ==========================================================================
CT_SCALE = 3.0
CT_CENTERS = [(0, 0)] + [(25, h) for h in range(0, 360, 45)] + [(50, h) for h in range(0, 360, 30)]


def fig_contours(out):
    W, H = 900, 840
    im, d = canvas(W, H)
    fx, fs = font(13), font(12)
    ar, br = (-80, 80), (-80, 80)
    box = (100, 50, 840, 790 - 30)
    ax = ab_panel(d, im, box, ar, br, 20, fx, tint=200)
    for C, h in CT_CENTERS:
        c = lch(50, C, h)
        P = contour(c, de00)
        circ = [ax.px(c[1] + CT_SCALE * math.cos(t), c[2] + CT_SCALE * math.sin(t))
                for t in np.linspace(0, 2 * math.pi, 60, endpoint=False)]
        for k in range(0, 60, 2):
            line(d, (*circ[k], *circ[k + 1]), fill=MUTED, width=1.2)
        pp = [ax.px(c[1] + CT_SCALE * p[1], c[2] + CT_SCALE * p[2]) for p in P]
        closed(d, pp, CURVE, 1.9)
        px, py = ax.px(c[1], c[2])
        ellipse(d, (px - 3, py - 3, px + 3, py + 3), fill=lab_rgb8(c), outline=INK, width=1)
    callout(d, (590, 640, 830, 696), "蓝色区域（h 约 275°）：\n轮廓斜着拉长，这是旋转项 RT", fs,
            tail=ax.px(*lch(50, 50, 270)[1:]))
    callout(d, (120, 640, 360, 696), "中性色：沿 a* 方向被 G 压扁", fs, tail=ax.px(-3, 0))
    callout(d, (590, 80, 830, 136), "彩度越高，轮廓越大，\n径向比切向长", fs, tail=ax.px(*lch(50, 50, 60)[1:]))
    text(d, ((box[0] + box[2]) / 2, box[3] + 40), "a*", ifont(18))
    text(d, (46, box[1]), "b*", ifont(18))
    text(d, (W / 2, 24), "CIEDE2000：L* = 50 的 a*b* 平面上 ΔE00 = 1 的等色差轮廓（放大 3 倍）", fx)
    text(d, (W / 2, H - 18), "实线：ΔE00 = 1；虚线：ΔE*ab = 1 的圆（同样放大 3 倍）。中心点的颜色超出 sRGB 色域时已裁剪，只作示意",
         fs, fill=MUTED)
    finish(im, os.path.join(out, "ciede2000-contours.png"))


# ==========================================================================
# 图 5：RGB 上同样长度的误差，折算成 ΔE00
# ==========================================================================
HUE_C = 25


def loss_series():
    Ls = np.arange(20, 96, 1.0)
    gray = {dom: np.array([np.percentile(rgb_step_de(np.array([L, 0, 0]), dom), (5, 50, 95)) for L in Ls])
            for dom in ("srgb", "linear")}
    chroma = {}
    for h in (140, 305):
        Cs = np.array([C for C in np.arange(0, 61, 2.0) if in_gamut(lch(50, C, h))])
        chroma[h] = (Cs, np.array([np.median(rgb_step_de(lch(50, C, h), "srgb")) for C in Cs]))
    hs = np.arange(0, 361, 5.0)
    hue = {dom: np.array([np.median(rgb_step_de(lch(50, HUE_C, h), dom)) for h in hs]) for dom in ("srgb", "linear")}
    return Ls, gray, chroma, hs, hue


def fig_rgb_loss(out):
    W, H = 1010, 500
    im, d = canvas(W, H)
    fx, fs, fb = font(13), font(12), font(13, bold=True)
    Ls, gray, chroma, hs, hue = loss_series()
    boxes = PANELS3

    ax = Axes(d, boxes[0], (20, 100), (0, 4.5))
    ax.frame(list(range(20, 101, 20)), [0, 1, 2, 3, 4], fx, xlabel="灰色的 L*")
    text(d, ((boxes[0][0] + boxes[0][2]) / 2, 66), "随明度（灰色）", fb)
    band(d, ax, Ls, gray["linear"][:, 0], gray["linear"][:, 2], BAND2)
    band(d, ax, Ls, gray["srgb"][:, 0], gray["srgb"][:, 2], BAND)
    ax.plot(Ls, gray["linear"][:, 1], fill=ACCENT, width=2.4)
    ax.plot(Ls, gray["srgb"][:, 1], fill=CURVE, width=2.6)

    ax = Axes(d, boxes[1], (0, 60), (0, 0.8))
    ax.frame(list(range(0, 61, 10)), [0, 0.2, 0.4, 0.6, 0.8], fx, yfmt="%.1f", xlabel="C*（L* = 50）")
    text(d, ((boxes[1][0] + boxes[1][2]) / 2, 66), "随彩度（sRGB 编码值）", fb)
    for h, col, lab in ((140, GREEN, "绿 h = 140°"), (305, PURPLE, "紫 h = 305°")):
        Cs, v = chroma[h]
        ax.plot(Cs, v, fill=col, width=2.4)
    legend_line(d, boxes[1][2] - 130, boxes[1][1] + 20, GREEN, "绿 h = 140°", fs)
    legend_line(d, boxes[1][2] - 130, boxes[1][1] + 42, PURPLE, "紫 h = 305°", fs)

    ax = Axes(d, boxes[2], (0, 360), (0, 0.8))
    ax.frame(list(range(0, 361, 60)), [0, 0.2, 0.4, 0.6, 0.8], fx, yfmt="%.1f", xlabel="色相角 h（L* = 50，C* = %d）" % HUE_C)
    text(d, ((boxes[2][0] + boxes[2][2]) / 2, 66), "随色相", fb)
    ax.plot(hs, hue["linear"], fill=ACCENT, width=2.4)
    ax.plot(hs, hue["srgb"], fill=CURVE, width=2.6)

    legend_line(d, 300, 448, CURVE, "在 sRGB 编码值上偏移", fx)
    legend_line(d, 560, 448, ACCENT, "在线性 sRGB 上偏移", fx)
    text(d, (W / 2, 24), "RGB 上同样 %.3f 的误差（向量长度），按 CIEDE2000 折算成多大的色差（纵轴均为 ΔE00）" % RGB_STEP, fx)
    text(d, (W / 2, H - 16), "曲线为 4000 个随机方向的中位数；左图色带为 5%～95% 分位，即同一颜色上偏移方向不同造成的差别",
         fs, fill=MUTED)
    finish(im, os.path.join(out, "rgb-error-vs-de2000.png"))


# ==========================================================================
# 正文引用的数值
# ==========================================================================

def check():
    n, err = sharma_check()
    print("CIEDE2000 实现：Sharma (2005) 测试数据 %d 组，最大偏差 %.1e" % (n, err))

    print("\nMacAdam 椭圆：最大 / 最小")
    from generate_uniform_color_space_figures import xy_to_upvp
    R = macadam_ab_stats()
    xy = np.array([(a, b) for _, _, a, b, _ in macadam_ellipses()])
    up = []
    for x0, y0, a, b, th in macadam_ellipses():
        P = []
        for k in range(120):
            t = 2 * math.pi * k / 120
            dx, dy = a * math.cos(t), b * math.sin(t)
            P.append(xy_to_upvp(x0 + dx * math.cos(th) - dy * math.sin(th), y0 + dx * math.sin(th) + dy * math.cos(th)))
        P = np.array(P)
        w, _ = np.linalg.eigh(np.cov(P.T))
        up.append(np.sqrt(2 * w[::-1]))
    up = np.array(up)
    for name, A in (("xy", xy), ("u'v'", up), ("a*b*", R[:, 3:5])):
        area = A[:, 0] * A[:, 1]
        print("  %-5s 面积 %.1f 倍，长半轴 %.1f 倍，长短轴之比 %.1f～%.1f" % (
            name, area.max() / area.min(), A[:, 0].max() / A[:, 0].min(), (A[:, 0] / A[:, 1]).min(), (A[:, 0] / A[:, 1]).max()))
    print("  a*b*：C* 与长半轴的相关系数 %.2f；中性色附近 (C* = %.1f) 长半轴 %.2f；最大长半轴 %.2f (C* = %.0f)" % (
        np.corrcoef(R[:, 2], R[:, 3])[0, 1], R[np.argmin(R[:, 2]), 2], R[np.argmin(R[:, 2]), 3],
        R[:, 3].max(), R[np.argmax(R[:, 3]), 2]))

    print("\nCMC 的不对称：")
    P, Q = lch(50, 20, 40), lch(50, 50, 40)
    print("  P = L*C*h (50, 20, 40°)，Q = (50, 50, 40°)：ΔE*ab = %.1f，CMC(2:1) P 为参考 %.2f，Q 为参考 %.2f；"
          "CIE94 %.2f / %.2f；CIEDE2000 %.2f / %.2f" % (
              de76(P, Q), de_cmc(P, Q), de_cmc(Q, P), de94(P, Q), de94(Q, P), de00(P, Q), de00(Q, P)))

    print("\nCIEDE2000 等色差轮廓（L* = 50，ΔE00 = 1）：长半轴、短半轴、长轴偏离径向")
    for C, h in ((0, 0), (25, 90), (50, 0), (50, 60), (50, 140), (50, 270), (50, 305)):
        a, b, ang = contour_axes(contour(lch(50, C, h), de00, n=360))
        dev = abs((ang - h + 90) % 180 - 90) if C else float("nan")
        print("  C* = %2d h = %3d°：%.2f / %.2f（%.1f 倍），偏离 %.0f°" % (C, h, a, b, a / b, dev))
    a0, b0, _ = contour_axes(contour(lch(50, 50, 270), lambda x, y: de00(x, y, no_rt=True), n=360))
    a1, b1, _ = contour_axes(contour(lch(50, 50, 270), de00, n=360))
    print("  R_T 的作用（C* = 50，h = 270°）：去掉 R_T %.2f / %.2f（%.1f 倍），带上 %.2f / %.2f（%.1f 倍）" % (
        a0, b0, a0 / b0, a1, b1, a1 / b1))
    _, t = de00(lch(50, 0, 0), lch(50, 0, 0), terms=True)
    print("  G(C* = 0) = %.2f；SL(L* = 0, 50, 100) = %.2f, %.2f, %.2f；T(h) 范围 %.2f～%.2f" % (
        t["G"], ciede2000_SL(0), ciede2000_SL(50), ciede2000_SL(100),
        ciede2000_T(np.arange(360)).min(), ciede2000_T(np.arange(360)).max()))
    print("  T 的极小在 h = %d°，极大在 h = %d°" % (np.argmin(ciede2000_T(np.arange(360))), np.argmax(ciede2000_T(np.arange(360)))))

    print("\nΔE*ab = 1 折算成 ΔE00（L* = 50 的 a*b* 平面，各中心、各方向）：")
    vals = []
    for C, h in CT_CENTERS:
        c = lch(50, C, h)
        for k in range(72):
            th = 2 * math.pi * k / 72
            vals.append(float(de00(c, c + np.array([0, math.cos(th), math.sin(th)]))))
    print("  %.2f～%.2f（%.1f 倍）" % (min(vals), max(vals), max(vals) / min(vals)))

    print("\nRGB 上偏移 %.3f（4000 个随机方向）折算成 ΔE00：" % RGB_STEP)
    Ls, gray, chroma, hs, hue = loss_series()
    for dom, nm in (("srgb", "sRGB 编码值"), ("linear", "线性 sRGB")):
        g = gray[dom]
        row = lambda r: (r[1], r[0], r[2])
        print("  灰色 %s：L* = 20 中位 %.2f（5%%～95%%：%.2f～%.2f）；L* = 50 中位 %.2f（%.2f～%.2f）；"
              "L* = 95 中位 %.2f（%.2f～%.2f）" % (nm, *row(g[0]), *row(g[30]), *row(g[-1])))
    for h in (140, 305):
        Cs, v = chroma[h]
        print("  彩度 h = %d°：C* = 0 → %.2f，C* = %d → %.2f" % (h, v[0], Cs[-1], v[-1]))
    for dom, nm in (("srgb", "sRGB 编码值"), ("linear", "线性 sRGB")):
        v = hue[dom]
        print("  色相 %s（C* = %d）：%.2f（h = %d°）～%.2f（h = %d°），%.2f 倍；h = 140° %.2f，h = 305° %.2f" % (
            nm, HUE_C, v.min(), hs[np.argmin(v)], v.max(), hs[np.argmax(v)], v.max() / v.min(),
            v[list(hs).index(140)], v[list(hs).index(305)]))
    for C, h in ((0, 0), (60, 140)):
        e = rgb_step_de(lch(50, C, h), "srgb")
        print("  方向：L*C*h (50, %d, %d°) 的 sRGB 编码值上，最小 %.2f，最大 %.2f，%.1f 倍；5%%～95%%：%.2f～%.2f" % (
            C, h, e.min(), e.max(), e.max() / e.min(), *np.percentile(e, (5, 95))))


    print("\n误差方向的前提（sRGB 编码值，灰色 vs C* = 60）：")
    lum = np.array([1.0, 1.0, 1.0]) / math.sqrt(3)
    def along(lab0, v):
        s0 = _encode(np.clip(lab_to_linear(lab0), 0, 1))
        return float(de00(srgb_to_lab(s0), srgb_to_lab(s0 + RGB_STEP * v)))
    def iso_ab(lab0):
        s0 = _encode(np.clip(lab_to_linear(lab0), 0, 1))
        l0, l1 = srgb_to_lab(s0), srgb_to_lab(s0 + RGB_STEP * DIRS)
        return float(np.median(de76(np.broadcast_to(l0, l1.shape), l1)))
    g = lch(50, 0, 0)
    for h in (140, 305):
        c = lch(50, 60, h)
        print("  h = %d°：各向同性 ΔE00 %.2f 倍；沿 (1,1,1) ΔE00 %.2f 倍；各向同性但用 ΔE*ab 量 %.2f 倍" % (
            h, np.median(rgb_step_de(g, "srgb")) / np.median(rgb_step_de(c, "srgb")),
            along(g, lum) / along(c, lum), iso_ab(g) / iso_ab(c)))
    print("\n各基准色上 ΔE00 中位数的最大 / 最小（L* 30～90、C* 0～60、h 每 30°，限 sRGB 色域内）：")
    bases = [lch(L, C, h) for L in (30, 50, 70, 90) for C in (0, 20, 40, 60) for h in (range(0, 360, 30) if C else (0,))
             if in_gamut(lch(L, C, h))]
    lab_step = lambda c: de00(np.broadcast_to(c, (len(DIRS), 3)), c + 1.0 * DIRS)
    for nm, fn in (("线性 sRGB（偏移 RGB_STEP）", lambda c: rgb_step_de(c, "linear")),
                   ("sRGB 编码值（偏移 RGB_STEP）", lambda c: rgb_step_de(c, "srgb")),
                   ("CIELAB（偏移 1）", lab_step)):
        m = np.array([np.median(fn(c)) for c in bases])
        print("  %d 个基准色，%s：%.2f～%.2f，%.1f 倍" % (len(bases), nm, m.min(), m.max(), m.max() / m.min()))


FIGURES = {
    "macadam": fig_macadam_ab,
    "lch": fig_lch,
    "weights": fig_weights,
    "contours": fig_contours,
    "rgb": fig_rgb_loss,
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", nargs="*", help="只生成这些图")
    ap.add_argument("--out", default="assets/resource/Color-Difference-Formulas")
    ap.add_argument("--check", action="store_true", help="打印正文引用的数值")
    args = ap.parse_args()
    if args.check:
        check()
        return
    os.makedirs(args.out, exist_ok=True)
    for n in (args.only or list(FIGURES)):
        FIGURES[n](args.out)


if __name__ == "__main__":
    main()
