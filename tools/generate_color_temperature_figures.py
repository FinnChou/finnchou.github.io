#!/usr/bin/env python3
"""生成《照明光的色味：色温与相关色温》一文的插图。

依赖 Pillow 与 numpy；绘图工具与 CIE 1931 数据从同目录的
generate_cie_xyz_figures.py 导入，uv 变换与色度图填色从
generate_uniform_color_space_figures.py 导入。

用法：
    python3 tools/generate_color_temperature_figures.py            # 全部
    python3 tools/generate_color_temperature_figures.py --only locus-xy

图里的数据：
    - 黑体辐射：普朗克公式，常数取 2019 年 SI 定义值
          h = 6.62607015e-34 J·s, c = 299792458 m/s, k = 1.380649e-23 J/K
    - 黑体轨迹、各温度的色度：普朗克光谱对 CIE 1931 2° 等色函数（1 nm）积分
      校验：2856 K 算得 (0.4475, 0.4074)，与标准照明体 A 的 (0.4476, 0.4074) 一致
    - CIE 1960 uv 色度图与等色温线：u = 4X/(X+15Y+3Z), v = 6Y/(X+15Y+3Z)，
      等色温线为 uv 图上与黑体轨迹正交的直线（JIS Z 8725 / CIE 15 的定义）
    - 荧光灯光谱：CIE 照明体 FL10（5000 K 三波长域荧光灯，CIE 15:2004 表），
      经 colour-science 内置数据表导出后原样嵌入
    - D55 / D65 / D75 / C 的色度：CIE 15:2004 表值
    - 三张实物照片取自 Wikimedia Commons（放在输出目录里，由脚本拼图）：
          candle.jpg    File:Candle flame (1).jpg，Jon Sullivan，公有领域
          embers.jpg    File:Hot embers 2.jpg，MUuslimabonu，CC0
          filament.jpg  File:Close up picture of a filament bulb.jpg，BhavyaTarun1708，CC0
"""

import argparse
import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from generate_cie_xyz_figures import (  # noqa: E402
    SS, WHITE, PANEL, GRID, BORDER, INK, MUTED, CURVE, ACCENT, RED, GREEN, BLUE,
    WL_CMF, CMF, M_XYZ2RGB, _encode, cmf_at, spectral_locus, draw_chromaticity,
    font, ifont, canvas, finish, text, rect, line, polyline, poly, ellipse, arc,
    arrow, dashed, callout, Axes, spectrum_strip,
)
from generate_uniform_color_space_figures import (  # noqa: E402
    xy_to_uv, uv_to_xy, diagram_image, lighten,
)

# ---------------------------------------------------------------- 物理常数（SI 2019）
H_PLANCK = 6.62607015e-34
C_LIGHT = 299792458.0
K_BOLTZ = 1.380649e-23

# CIE 照明体 FL10（5000 K，三波长域荧光灯），相对光谱功率，5 nm，380–780 nm，CIE 15:2004
SPD_FL10 = """
380 1.11
385 0.8
390 0.62
395 0.57
400 1.48
405 12.16
410 2.12
415 2.7
420 3.74
425 5.14
430 6.75
435 34.39
440 14.86
445 10.4
450 10.76
455 10.67
460 10.11
465 9.27
470 8.29
475 7.29
480 7.91
485 16.64
490 16.73
495 10.44
500 5.94
505 3.34
510 2.35
515 1.88
520 1.59
525 1.47
530 1.8
535 5.71
540 40.98
545 73.69
550 33.61
555 8.24
560 3.38
565 2.47
570 2.14
575 4.86
580 11.45
585 14.79
590 12.16
595 8.97
600 6.52
605 8.31
610 44.12
615 34.55
620 12.09
625 12.15
630 10.52
635 4.43
640 1.95
645 2.19
650 3.19
655 2.77
660 2.29
665 2.0
670 1.52
675 1.35
680 1.47
685 1.79
690 1.74
695 1.02
700 1.14
705 3.32
710 4.49
715 2.05
720 0.49
725 0.24
730 0.21
735 0.21
740 0.24
745 0.24
750 0.21
755 0.17
760 0.21
765 0.22
770 0.17
775 0.12
780 0.09
"""

# CIE 15:2004 给出的几个照明体的色度（2° 观察者）
ILLUM_XY = {"D55": (0.3324, 0.3474), "D65": (0.3127, 0.3290), "D75": (0.2990, 0.3149), "C": (0.3101, 0.3162)}

_WL = np.array(WL_CMF)
_CMF = np.array(CMF)


def planck(wl_nm, T):
    """黑体的光谱辐射亮度（W·m⁻³·sr⁻¹），wl_nm 可为数组。"""
    lam = np.asarray(wl_nm, dtype=float) * 1e-9
    return 2 * H_PLANCK * C_LIGHT ** 2 / lam ** 5 / (np.exp(H_PLANCK * C_LIGHT / (lam * K_BOLTZ * T)) - 1.0)


def bb_xy(T):
    L = planck(_WL, T)
    XYZ = (_CMF * L[:, None]).sum(axis=0)
    return XYZ[0] / XYZ.sum(), XYZ[1] / XYZ.sum()


def bb_uv(T):
    return xy_to_uv(*bb_xy(T))


def bb_rgb8(T):
    """黑体色度对应的『尽可能亮』的 sRGB 显示色。"""
    x, y = bb_xy(T)
    xyz = np.array([x / y, 1.0, (1 - x - y) / y])
    rgb = M_XYZ2RGB @ xyz
    rgb = rgb - min(0.0, rgb.min())
    rgb = rgb / rgb.max()
    return tuple(int(round(v * 255)) for v in _encode(rgb))


def _parse_spd(block):
    rows = [ln.split() for ln in block.strip().splitlines()]
    return np.array([float(r[0]) for r in rows]), np.array([float(r[1]) for r in rows])


WL_FL10, FL10 = _parse_spd(SPD_FL10)


def spd_xy(wl, spd):
    XYZ = np.zeros(3)
    for w, p in zip(wl, spd):
        XYZ += np.array(cmf_at(w)) * p
    return XYZ[0] / XYZ.sum(), XYZ[1] / XYZ.sum()


def isotherm_normal(T, dT=None):
    """uv 图上黑体轨迹在 T 处的单位法向量（朝 v 增大、即绿色一侧为正）。"""
    dT = dT or T * 0.005
    u1, v1 = bb_uv(T - dT)
    u2, v2 = bb_uv(T + dT)
    tx, ty = u2 - u1, v2 - v1
    n = math.hypot(tx, ty)
    nx, ny = -ty / n, tx / n
    if ny < 0:
        nx, ny = -nx, -ny
    return nx, ny


def cct_duv(u, v):
    """粗略求相关色温：在黑体轨迹上找 uv 距离最近的点（先粗扫再细扫）。"""
    Ts = np.exp(np.linspace(math.log(1000), math.log(100000), 400))
    best = min(Ts, key=lambda T: math.hypot(*(np.array(bb_uv(T)) - (u, v))))
    lo, hi = best / 1.02, best * 1.02
    for _ in range(40):
        m1, m2 = lo + (hi - lo) / 3, hi - (hi - lo) / 3
        d1 = math.hypot(*(np.array(bb_uv(m1)) - (u, v)))
        d2 = math.hypot(*(np.array(bb_uv(m2)) - (u, v)))
        if d1 < d2:
            hi = m2
        else:
            lo = m1
    T = (lo + hi) / 2
    u0, v0 = bb_uv(T)
    nx, ny = isotherm_normal(T)
    duv = (u - u0) * nx + (v - v0) * ny
    return T, duv


LOCUS_T = np.exp(np.linspace(math.log(1000), math.log(1e6), 300))


def clip_segment(p0, p1, xr, yr):
    """把数据坐标下的线段裁到 xr × yr 的矩形内；完全在外时返回 None。"""
    x0, y0 = p0
    x1, y1 = p1
    dx, dy = x1 - x0, y1 - y0
    t0, t1 = 0.0, 1.0
    for p, q in ((-dx, x0 - xr[0]), (dx, xr[1] - x0), (-dy, y0 - yr[0]), (dy, yr[1] - y0)):
        if p == 0:
            if q < 0:
                return None
            continue
        t = q / p
        if p < 0:
            t0 = max(t0, t)
        else:
            t1 = min(t1, t)
        if t0 > t1:
            return None
    return (x0 + t0 * dx, y0 + t0 * dy), (x0 + t1 * dx, y0 + t1 * dy)


def clipped_polyline(d, ax, pts, fill, width, dash=None):
    """按数据坐标逐段裁剪后再画折线；dash 为 (dash, gap) 时画虚线。"""
    for a, b in zip(pts[:-1], pts[1:]):
        seg = clip_segment(a, b, ax.xr, ax.yr)
        if seg is None:
            continue
        pa, pb = ax.px(*seg[0]), ax.px(*seg[1])
        if dash:
            dashed(d, pa, pb, fill=fill, width=width, dash=dash[0], gap=dash[1])
        else:
            line(d, (pa[0], pa[1], pb[0], pb[1]), fill=fill, width=width)


# ==========================================================================
# 图 0：身边接近黑体的东西（三张 Commons 照片拼图）
# ==========================================================================

def _cover(im, w, h):
    """按 cover 方式裁剪缩放到 w×h。"""
    r = max(w / im.width, h / im.height)
    im = im.resize((int(im.width * r + 0.5), int(im.height * r + 0.5)), Image.LANCZOS)
    x0 = (im.width - w) // 2
    y0 = (im.height - h) // 2
    return im.crop((x0, y0, x0 + w, y0 + h))


def fig_photos(out):
    W, H = 940, 400
    im, d = canvas(W, H)
    f = font(13)
    fb = font(14, bold=True)
    fs = font(11)
    panels = (("candle.jpg", "烛焰", "约 1900 K", "Jon Sullivan，公有领域"),
              ("embers.jpg", "炭火", "约 1000～1500 K", "MUuslimabonu，CC0"),
              ("filament.jpg", "白炽灯的钨丝", "约 2800 K", "BhavyaTarun1708，CC0"))
    pw, ph, gap, x0, y0 = 280, 280, 30, 35, 50
    for i, (name, lab, temp, credit) in enumerate(panels):
        x = x0 + i * (pw + gap)
        path = os.path.join(out, name)
        if not os.path.exists(path):
            rect(d, (x, y0, x + pw, y0 + ph), fill=PANEL, outline=BORDER)
            text(d, (x + pw / 2, y0 + ph / 2), "缺少 " + name, f, fill=MUTED)
        else:
            photo = _cover(Image.open(path).convert("RGB"), pw * SS, ph * SS)
            im.paste(photo, (x * SS, y0 * SS))
            rect(d, (x, y0, x + pw, y0 + ph), outline=BORDER, width=1.2)
        text(d, (x + pw / 2, y0 + ph + 20), lab, fb)
        text(d, (x + pw / 2, y0 + ph + 40), temp, f, fill=MUTED)
        text(d, (x + pw / 2, y0 + ph + 58), credit, fs, fill=MUTED)
    text(d, (W / 2, 24), "身边接近黑体的东西：都是靠加热发光的热辐射光源", f)
    finish(im, os.path.join(out, "near-blackbody-photos.png"))


# ==========================================================================
# 图 1：黑体的温度与颜色（色标）
# ==========================================================================

def fig_color_scale(out):
    W, H = 940, 300
    im, d = canvas(W, H)
    f = font(13)
    fb = font(14, bold=True)
    fs = font(12)
    x0, x1, y0, y1 = 80, 860, 90, 170
    T0, T1 = 1000.0, 15000.0
    n = int((x1 - x0) * SS)
    strip = Image.new("RGB", (n, int((y1 - y0) * SS)))
    sd = ImageDraw.Draw(strip)
    for i in range(n):
        T = T0 * (T1 / T0) ** (i / (n - 1))
        sd.line([(i, 0), (i, strip.height)], fill=bb_rgb8(T))
    im.paste(strip, (int(x0 * SS), int(y0 * SS)))
    rect(d, (x0, y0, x1, y1), outline=BORDER, width=1.2)
    for T in (1000, 1500, 2000, 3000, 4000, 5000, 6500, 8000, 10000, 15000):
        px = x0 + (x1 - x0) * math.log(T / T0) / math.log(T1 / T0)
        line(d, (px, y1, px, y1 + 6), fill=INK, width=1.2)
        text(d, (px, y1 + 16), "%d" % T, fs, fill=INK)
    text(d, ((x0 + x1) / 2, y1 + 40), "黑体的绝对温度 T（K，对数刻度）", f)
    arrow(d, (x0, 62), (x1, 62), fill=MUTED, width=2, head=10)
    text(d, (x0 + 4, 46), "低温", fs, fill=MUTED, anchor="lm")
    text(d, (x1 - 4, 46), "高温", fs, fill=MUTED, anchor="rm")
    for T, lab in ((1200, "红黑"), (2000, "橙"), (3000, "黄橙"), (4200, "黄白"), (6000, "白"), (11000, "蓝白")):
        px = x0 + (x1 - x0) * math.log(T / T0) / math.log(T1 / T0)
        text(d, (px, (y0 + y1) / 2), lab, fb, fill=WHITE if T < 5000 else INK)
    text(d, (W / 2, 22), "黑体的温度与颜色有确定的对应关系：每个温度对应一个色度", f)
    text(d, (W / 2, 262), "颜色由普朗克光谱经 CIE 1931 等色函数算出色度，再取 sRGB 中最亮的显示色；只表示色度，不表示亮度", fs, fill=MUTED)
    text(d, (W / 2, 282), "（白炽灯灯丝约 2800 K，蜡烛火焰约 1900 K，炭火约 1000～1500 K，都可近似看作黑体）", fs, fill=MUTED)
    finish(im, os.path.join(out, "blackbody-color-scale.png"))


# ==========================================================================
# 图 2：普朗克辐射式：不同温度的光谱分布
# ==========================================================================

TEMPS = (2000, 3000, 4000, 5000, 6000, 8000, 10000)
TEMP_COLS = {2000: (200, 60, 60), 3000: (215, 120, 40), 4000: (190, 160, 30), 5000: (90, 160, 90),
             6000: (60, 150, 170), 8000: (80, 110, 200), 10000: (120, 70, 170)}


def fig_planck_spectra(out):
    W, H = 940, 560
    im, d = canvas(W, H)
    fx = font(13)
    fs = font(12)
    ax = Axes(d, (90, 60, 900, 440), (100, 1000), (0, 1.05))
    xt = list(range(100, 1001, 100))
    yt = [0, 0.2, 0.4, 0.6, 0.8, 1.0]
    ax.frame(xt, yt, fx, yfmt="%.1f", xlabel="波长（nm）")
    text(d, (92, 48), "光谱辐射亮度（相对值）", fx, anchor="lm")
    # 可见光范围铺底色，再把网格重画在上面
    vx0, _ = ax.px(380, 0)
    vx1, _ = ax.px(780, 0)
    rect(d, (vx0, 60, vx1, 440), fill=(246, 247, 252))
    ax.grid(xt, yt)
    wl = np.linspace(100, 1000, 901)
    ref = planck(wl, 10000).max()
    for T in TEMPS:
        ax.plot(wl, planck(wl, T) / ref, fill=TEMP_COLS[T], width=2.4)
    # 图例
    lx, ly = 740, 120
    for i, T in enumerate(reversed(TEMPS)):
        yy = ly + i * 22
        line(d, (lx, yy, lx + 26, yy), fill=TEMP_COLS[T], width=3)
        text(d, (lx + 34, yy), "%d K" % T, fs, anchor="lm")
    text(d, ((vx0 + vx1) / 2, 74), "可见光", fs, fill=INK)
    text(d, ((ax.px(100, 0)[0] + vx0) / 2, 74), "紫外", fs, fill=MUTED)
    text(d, ((vx1 + ax.px(1000, 0)[0]) / 2, 74), "红外", fs, fill=MUTED)
    dashed(d, (vx0, 60), (vx0, 440), fill=MUTED, width=1.2)
    dashed(d, (vx1, 60), (vx1, 440), fill=MUTED, width=1.2)
    spectrum_strip(d, (vx0, 444, vx1, 456))
    text(d, (W / 2, 30), "黑体的光谱分布（普朗克辐射式，以 10000 K 的峰值为 1）", fx)
    text(d, (W / 2, 520), "温度越高辐射越强、峰值波长越短；2000 K 的曲线在这个刻度下几乎贴着横轴", fs, fill=MUTED)
    finish(im, os.path.join(out, "planck-spectra.png"))


# ==========================================================================
# 图 3：可见光范围内、555 nm 处归一的相对光谱分布
# ==========================================================================

def fig_planck_normalized(out):
    W, H = 940, 560
    im, d = canvas(W, H)
    fx = font(13)
    fs = font(12)
    ax = Axes(d, (90, 60, 900, 440), (380, 780), (0, 2.0))
    xt = list(range(380, 781, 40))
    yt = [i * 0.2 for i in range(11)]
    ax.frame(xt, yt, fx, yfmt="%.1f", xlabel="波长（nm）")
    text(d, (92, 48), "相对光谱辐射亮度", fx, anchor="lm")
    wl = np.linspace(380, 780, 401)
    for T in TEMPS:
        s = planck(wl, T) / planck(555.0, T)
        clipped_polyline(d, ax, list(zip(wl, s)), TEMP_COLS[T], 2.4)
        if T <= 5000:
            if s[-1] <= 2.0:
                px, py = ax.px(780, s[-1])
                text(d, (px - 6, py - 10), "%d K" % T, fs, fill=TEMP_COLS[T], anchor="rb")
            else:       # 曲线从上边框离开：标在离开处的右下
                k = int(np.argmax(s > 2.0))
                px, py = ax.px(wl[k], 2.0)
                text(d, (px + 6, py + 6), "%d K" % T, fs, fill=TEMP_COLS[T], anchor="lt")
        else:
            px, py = ax.px(380, s[0])
            text(d, (px + 6, py - 10), "%d K" % T, fs, fill=TEMP_COLS[T], anchor="lb")
    px, py = ax.px(555, 1.0)
    ellipse(d, (px - 4, py - 4, px + 4, py + 4), fill=INK)
    text(d, (px + 8, py + 14), "555 nm 处取 1", fs, anchor="lm")
    spectrum_strip(d, (90, 444, 900, 456))
    text(d, (W / 2, 30), "可见光范围内黑体的相对光谱分布（每条曲线在 555 nm 处归一为 1）", fx)
    text(d, (W / 2, 520), "低温：长波强、偏红；6000 K 前后接近平坦、显白；更高温则短波强、偏蓝", fs, fill=MUTED)
    finish(im, os.path.join(out, "planck-normalized.png"))


# ==========================================================================
# 图 4：xy 色度图上的黑体轨迹
# ==========================================================================

LOCUS_TICKS = ((1500, "1500 K"), (2000, "2000 K"), (3000, "3000 K"), (4000, "4000 K"), (5000, "5000 K"),
               (6500, "6500 K"), (10000, "10000 K"), (20000, "20000 K"), (100000, "100000 K"))


def _draw_locus(d, ax, to_ij=None, width=2.4, ticks=True, label_font=None, side=1):
    pts = []
    for T in LOCUS_T:
        x, y = bb_xy(T)
        pts.append(to_ij(x, y) if to_ij else (x, y))
    pp = [ax.px(*p) for p in pts]
    polyline(d, pp, fill=INK, width=width)
    if ticks:
        for T, lab in LOCUS_TICKS:
            x, y = bb_xy(T)
            p = to_ij(x, y) if to_ij else (x, y)
            px, py = ax.px(*p)
            ellipse(d, (px - 3.5, py - 3.5, px + 3.5, py + 3.5), fill=WHITE, outline=INK, width=1.5)
            if label_font:
                if T == 2000:
                    text(d, (px - 2, py - 10), lab, label_font, fill=INK, anchor="rb")
                elif T == 1500:
                    text(d, (px - 4, py + 10), lab, label_font, fill=INK, anchor="rt")
                else:
                    text(d, (px + 8 * side, py + 10), lab, label_font, fill=INK, anchor="lt" if side > 0 else "rt")
    return pp


def fig_locus_xy(out):
    W, H = 900, 800
    im, d = canvas(W, H)
    box = (80, 40, 720, 760)
    ax = draw_chromaticity(d, im, box)
    lighten(im, box, 70)
    locus = spectral_locus(1)
    pts = [ax.px(x, y) for _, x, y in locus]
    polyline(d, pts + [pts[0]], fill=INK, width=1.4)
    _draw_locus(d, ax, label_font=font(12), side=1)
    text(d, ((box[0] + box[2]) / 2, 786), "x", ifont(18))
    text(d, (30, 40), "y", ifont(18))
    f = font(13)
    fs = font(12)
    px, py = ax.px(*bb_xy(1e6))
    text(d, (px - 8, py - 12), "T → ∞", fs, anchor="rm")
    callout(d, (430, 90, 715, 176), "黑体轨迹：温度升高时，色度从右下的红\n经橙、黄、黄白、白走向蓝白。\n黑体的色度由温度唯一决定，\n所以可以用「色温」一个数来指代颜色", fs, tail=ax.px(*bb_xy(4000)))
    text(d, (W / 2 - 40, 24), "xy 色度图上的黑体轨迹（Planckian locus）", f)
    finish(im, os.path.join(out, "planckian-locus-xy.png"))


# ==========================================================================
# 图 5：黑体轨迹附近的各种「白色」光源
# ==========================================================================

def fig_locus_zoom(out):
    W, H = 900, 700
    im, d = canvas(W, H)
    fx = font(13)
    fs = font(12)
    fb = font(13, bold=True)
    xr, yr = (0.28, 0.37), (0.30, 0.37)
    ax = Axes(d, (90, 50, 860, 640), xr, yr)
    xt = [0.28, 0.29, 0.30, 0.31, 0.32, 0.33, 0.34, 0.35, 0.36, 0.37]
    yt = [0.30, 0.31, 0.32, 0.33, 0.34, 0.35, 0.36, 0.37]
    ax.frame(xt, yt, fx, xfmt="%.2f", yfmt="%.2f")
    # 黑体轨迹（这一段，裁到框内）
    Ts = np.exp(np.linspace(math.log(3500), math.log(20000), 300))
    clipped_polyline(d, ax, [bb_xy(T) for T in Ts], INK, 2.4)
    for T in (4500, 5000, 5500, 6000, 6500, 7000, 8000, 10000):
        px, py = ax.px(*bb_xy(T))
        ellipse(d, (px - 3.5, py - 3.5, px + 3.5, py + 3.5), fill=WHITE, outline=INK, width=1.5)
        text(d, (px + 9, py - 4), "%d K" % T, fs, fill=INK, anchor="lb")
    text(d, ax.px(0.312, 0.305), "黑体轨迹", fb, anchor="lm")
    # CIE 照明体
    for name, (x, y) in ILLUM_XY.items():
        px, py = ax.px(x, y)
        ellipse(d, (px - 5, py - 5, px + 5, py + 5), fill=CURVE)
        if name == "C":
            text(d, (px + 9, py + 2), name, fb, fill=CURVE, anchor="lm")
        else:
            text(d, (px - 9, py + 2), name, fb, fill=CURVE, anchor="rm")
    # 5000 K 黑体与荧光灯
    px, py = ax.px(*bb_xy(5000))
    rect(d, (px - 6, py - 6, px + 6, py + 6), fill=(230, 170, 40))
    callout(d, (560, 300, 850, 330), "黑体（Tc = 5000 K）", fs, tail=(px, py))
    fx_, fy_ = spd_xy(WL_FL10, FL10)
    px, py = ax.px(fx_, fy_)
    poly(d, [(px, py - 8), (px + 8, py), (px, py + 8), (px - 8, py)], fill=ACCENT)
    callout(d, (560, 390, 850, 446), "CIE 照明体 FL10\n（5000 K 三波长域荧光灯）", fs, text_fill=ACCENT, tail=(px, py))
    px, py = ax.px(0.344, 0.349)
    ellipse(d, (px - 5, py - 5, px + 5, py + 5), fill=WHITE, outline=ACCENT, width=2)
    callout(d, (560, 470, 850, 526), "原文所举的昼白色荧光灯\n(0.344, 0.349)，Tcp = 5000 K", fs, text_fill=ACCENT, tail=(px, py))
    text(d, ((90 + 860) / 2, 672), "x", ifont(18))
    text(d, (36, 50), "y", ifont(18))
    text(d, (W / 2, 24), "各种「白色」光源的色度与黑体轨迹（xy 色度图局部）", fx)
    finish(im, os.path.join(out, "locus-zoom-white.png"))


# ==========================================================================
# 图 6：荧光灯与 5000 K 黑体的光谱分布
# ==========================================================================

def fig_fl_vs_blackbody(out):
    W, H = 940, 420
    im, d = canvas(W, H)
    fx = font(13)
    fs = font(12)
    # 左：FL10
    ax = Axes(d, (70, 60, 470, 330), (380, 780), (0, 1.05))
    xt = list(range(400, 781, 100))
    yt = [0, 0.2, 0.4, 0.6, 0.8, 1.0]
    ax.frame(xt, yt, fx, yfmt="%.1f", xlabel="波长（nm）")
    text(d, (72, 50), "相对光谱功率", fs, anchor="lm")
    ax.plot(WL_FL10, FL10 / FL10.max(), fill=CURVE, width=2.2)
    spectrum_strip(d, (70, 334, 470, 344))
    text(d, (270, 30), "昼白色荧光灯（CIE FL10，Tcp = 5000 K）", fx)
    # 右：黑体 5000 K
    ax = Axes(d, (520, 60, 900, 330), (380, 780), (0, 1.05))
    ax.frame(xt, yt, fx, yfmt="%.1f", xlabel="波长（nm）")
    wl = np.linspace(380, 780, 401)
    s = planck(wl, 5000)
    ax.plot(wl, s / s.max(), fill=(215, 140, 40), width=2.4)
    spectrum_strip(d, (520, 334, 900, 344))
    text(d, (710, 30), "黑体（Tc = 5000 K）", fx)
    text(d, (W / 2, 392), "两者看起来都是「白」，光谱却完全不同（各自以峰值为 1）", fs, fill=MUTED)
    finish(im, os.path.join(out, "fl10-vs-blackbody.png"))


# ==========================================================================
# 图 7：uv 色度图上的黑体轨迹与等色温线
# ==========================================================================

ISO_T = (2000, 2500, 3000, 4000, 5000, 6000, 8000, 10000, 20000)


def fig_uv_isotherms(out):
    W, H = 900, 640
    im, d = canvas(W, H)
    fx = font(13)
    fs = font(12)
    ir, jr = (0.0, 0.65), (0.0, 0.45)
    box = (80, 40, 720, 600)
    ax = Axes(d, box, ir, jr)
    xt = [i / 10 for i in range(7)]
    yt = [i / 10 for i in range(5)]
    ax.frame(xt, yt, fx, xfmt="%.1f", yfmt="%.1f")
    locus = spectral_locus(1)
    loc_ij = [xy_to_uv(x, y) for _, x, y in locus]
    w, h = int((box[2] - box[0]) * SS), int((box[3] - box[1]) * SS)
    img = diagram_image(w, h, ir, jr, uv_to_xy, loc_ij)
    im.paste(img, (int(box[0] * SS), int(box[1] * SS)), img)
    lighten(im, box, 140)
    ax.grid(xt, yt)
    pts = [ax.px(*p) for p in loc_ij]
    polyline(d, pts + [pts[0]], fill=INK, width=1.4)
    _draw_locus(d, ax, to_ij=xy_to_uv, ticks=False)
    for T in ISO_T:
        u0, v0 = bb_uv(T)
        nx, ny = isotherm_normal(T)
        L = 0.05
        p0 = ax.px(u0 - nx * L, v0 - ny * L)
        p1 = ax.px(u0 + nx * L, v0 + ny * L)
        line(d, (p0[0], p0[1], p1[0], p1[1]), fill=ACCENT, width=1.8)
        px, py = ax.px(u0, v0)
        ellipse(d, (px - 3, py - 3, px + 3, py + 3), fill=WHITE, outline=INK, width=1.4)
        text(d, (p1[0] + nx * 4, p1[1] - 10), "%d K" % T if T < 10000 else "%dK" % T, fs, fill=ACCENT,
             anchor="lb" if nx >= 0 else "rb")
    text(d, ax.px(0.37, 0.30), "黑体轨迹", font(13, bold=True), anchor="lm")
    callout(d, (430, 470, 715, 540), "等色温线：uv 图上与黑体轨迹正交的直线。\n线上各点的相关色温，都等于交点处\n黑体的色温", fs)
    text(d, ((box[0] + box[2]) / 2, 626), "u", ifont(18))
    text(d, (30, 40), "v", ifont(18))
    text(d, (W / 2 - 40, 24), "CIE 1960 UCS 色度图上的黑体轨迹与等色温线", fx)
    finish(im, os.path.join(out, "uv-isotherms.png"))


# ==========================================================================
# 图 8：xy 色度图上的黑体轨迹、等色温线与等偏差线
# ==========================================================================

def fig_xy_isotherms_duv(out):
    W, H = 900, 760
    im, d = canvas(W, H)
    fx = font(13)
    fs = font(12)
    fb = font(13, bold=True)
    xr, yr = (0.20, 0.55), (0.20, 0.50)
    box = (80, 40, 780, 700)
    ax = Axes(d, box, xr, yr)
    xt = [0.20, 0.25, 0.30, 0.35, 0.40, 0.45, 0.50, 0.55]
    yt = [0.20, 0.25, 0.30, 0.35, 0.40, 0.45, 0.50]
    ax.frame(xt, yt, fx, xfmt="%.2f", yfmt="%.2f")
    locus = spectral_locus(1)
    loc_xy = [(x, y) for _, x, y in locus]
    w, h = int((box[2] - box[0]) * SS), int((box[3] - box[1]) * SS)
    img = diagram_image(w, h, xr, yr, lambda x, y: (x, y), loc_xy)
    im.paste(img, (int(box[0] * SS), int(box[1] * SS)), img)
    lighten(im, box, 150)
    ax.grid(xt, yt)
    # 等偏差线 duv = ±0.01, ±0.02
    Ts = np.exp(np.linspace(math.log(1800), math.log(60000), 240))
    for duv, col in ((0.02, (60, 140, 90)), (0.01, (60, 140, 90)), (-0.01, (170, 80, 150)), (-0.02, (170, 80, 150))):
        pts = []
        for T in Ts:
            u0, v0 = bb_uv(T)
            nx, ny = isotherm_normal(T)
            pts.append(uv_to_xy(u0 + nx * duv, v0 + ny * duv))
        clipped_polyline(d, ax, pts, col, 1.8, dash=(7, 5))
        k = int(np.argmin(np.abs(Ts - 2200)))
        px, py = ax.px(*pts[k])
        text(d, (px + 6, py + (-8 if duv > 0 else 8)), "duv = %+.2f" % duv, fs, fill=col, anchor="lb" if duv > 0 else "lt")
    # 黑体轨迹
    clipped_polyline(d, ax, [bb_xy(T) for T in Ts], ACCENT, 2.6)
    px, py = ax.px(*bb_xy(2000))
    text(d, (px - 4, py + 22), "黑体轨迹", fb, fill=ACCENT, anchor="rm")
    # 等色温线
    for T in (2000, 2500, 3000, 4000, 5000, 6000, 8000, 10000, 20000):
        u0, v0 = bb_uv(T)
        nx, ny = isotherm_normal(T)
        L = 0.035
        a = uv_to_xy(u0 - nx * L, v0 - ny * L)
        b = uv_to_xy(u0 + nx * L, v0 + ny * L)
        seg = clip_segment(a, b, xr, yr)
        if seg is None:
            continue
        p0, p1 = ax.px(*seg[0]), ax.px(*seg[1])
        line(d, (p0[0], p0[1], p1[0], p1[1]), fill=INK, width=1.4)
        if T <= 2500:          # 右上角留给等偏差线的标签，这两条标在下端
            text(d, (p0[0] + 4, p0[1] + 4), "%d K" % T, fs, fill=INK, anchor="lt")
        else:
            text(d, (p1[0] - 4, p1[1] + (16 if seg[1][1] >= yr[1] - 1e-9 else -6)), "%d K" % T, fs, fill=INK,
                 anchor="rt" if seg[1][1] >= yr[1] - 1e-9 else "rb")
    callout(d, (470, 590, 770, 660), "等色温线在 uv 图上与轨迹正交，\n回到 xy 图上就变成斜交。\n轨迹上方（绿色方向）duv > 0，\n下方（红紫方向）duv < 0", fs)
    text(d, ((box[0] + box[2]) / 2, 726), "x", ifont(18))
    text(d, (30, 40), "y", ifont(18))
    text(d, (W / 2 - 40, 24), "xy 色度图上的黑体轨迹、等色温线与等偏差线", fx)
    finish(im, os.path.join(out, "xy-isotherms-duv.png"))


FIGURES = {
    "photos": fig_photos,
    "color-scale": fig_color_scale,
    "planck-spectra": fig_planck_spectra,
    "planck-normalized": fig_planck_normalized,
    "locus-xy": fig_locus_xy,
    "locus-zoom": fig_locus_zoom,
    "fl-vs-bb": fig_fl_vs_blackbody,
    "uv-isotherms": fig_uv_isotherms,
    "xy-isotherms": fig_xy_isotherms_duv,
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", nargs="*", help="只生成这些图")
    ap.add_argument("--out", default="assets/resource/Color-Temperature")
    ap.add_argument("--check", action="store_true", help="打印校验用的数值")
    args = ap.parse_args()
    if args.check:
        for T in (2856, 5000, 6500):
            print("blackbody %5d K  xy = (%.4f, %.4f)" % (T, *bb_xy(T)))
        x, y = spd_xy(WL_FL10, FL10)
        T, duv = cct_duv(*xy_to_uv(x, y))
        print("FL10 xy = (%.4f, %.4f)  Tcp = %.0f K  duv = %+.4f" % (x, y, T, duv))
        T, duv = cct_duv(*xy_to_uv(0.344, 0.349))
        print("(0.344, 0.349)  Tcp = %.0f K  duv = %+.4f" % (T, duv))
        return
    os.makedirs(args.out, exist_ok=True)
    for n in (args.only or list(FIGURES)):
        FIGURES[n](args.out)


if __name__ == "__main__":
    main()
