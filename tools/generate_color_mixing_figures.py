#!/usr/bin/env python3
"""重绘《混色：加法、减法与中间混色》的全部插图。

原文（CCS「光と色の話」第 16/17/18 回）的插图是 2000 年代的日文 GIF/PNG，
这里按 What-is-Color 那批图的配色与版式重画一遍，文字全部换成中文。

用法:
    python3 tools/generate_color_mixing_figures.py                # 全部
    python3 tools/generate_color_mixing_figures.py --only spinning-disc
    python3 tools/generate_color_mixing_figures.py --out DIR
"""

import argparse
import math
import os
import random

import numpy as np
from PIL import Image, ImageDraw, ImageFont

# 先按 2 倍画再缩回去：PIL 的直线没有抗锯齿，降采样是最省事的补救
SS = 2

WHITE = (255, 255, 255)
PANEL = (238, 240, 247)
GRID = (222, 226, 240)
BORDER = (198, 204, 220)
INK = (45, 48, 62)
MUTED = (135, 140, 155)
CURVE = (74, 79, 158)

# 色光 / 色料
R = (224, 62, 56)
G = (46, 168, 84)
B = (48, 96, 214)
Y = (245, 200, 35)
M = (226, 70, 178)
C = (40, 190, 204)
K = (32, 34, 42)

# 浅色底（画在白底上的填充）
R_L = (250, 224, 222)
G_L = (219, 243, 227)
B_L = (219, 231, 250)
Y_L = (253, 243, 205)
M_L = (251, 223, 243)
C_L = (214, 244, 247)

# --------------------------------------------------------------------------
# CIE 标准 LED 照明体的相对光谱分布，380-780 nm / 5 nm 步长，各自以峰值归一化。
# 取自开源库 colour-science (BSD-3-Clause) 内置的标准照明体数据集，
# 原始定义见 CIE 15:2018 Colorimetry。
#   LED-B3   蓝光芯片 + 荧光粉   -> 补色荧光方式
#   LED-RGB1 三色芯片            -> 三原色 RGB 方式
#   LED-V2   紫光芯片 + 荧光粉   -> 三原色荧光方式
# 「补色方式」（两颗芯片、无荧光体）没有对应的 CIE 标准照明体，故不收录。
# --------------------------------------------------------------------------
CIE_LED_SPD = {
    "LED-B3": [
        0.0000, 0.0000, 0.0005, 0.0011, 0.0026, 0.0058, 0.0132, 0.0297, 0.0636, 0.1256,
        0.2247, 0.3800, 0.6418, 0.9380, 1.0000, 0.7727, 0.5246, 0.3990, 0.3190, 0.2708,
        0.2740, 0.3084, 0.3588, 0.4176, 0.4738, 0.5204, 0.5575, 0.5861, 0.6100, 0.6322,
        0.6555, 0.6799, 0.7054, 0.7308, 0.7557, 0.7780, 0.7992, 0.8172, 0.8331, 0.8463,
        0.8574, 0.8675, 0.8744, 0.8771, 0.8744, 0.8649, 0.8479, 0.8235, 0.7928, 0.7562,
        0.7144, 0.6688, 0.6206, 0.5713, 0.5220, 0.4732, 0.4261, 0.3816, 0.3402, 0.3015,
        0.2660, 0.2342, 0.2056, 0.1797, 0.1563, 0.1357, 0.1176, 0.1017, 0.0874, 0.0758,
        0.0652, 0.0562, 0.0482, 0.0413, 0.0360, 0.0307, 0.0265, 0.0228, 0.0196, 0.0170, 0.0148
    ],
    "LED-RGB1": [
        0.0000, 0.0000, 0.0000, 0.0002, 0.0003, 0.0008, 0.0018, 0.0038, 0.0080, 0.0150,
        0.0255, 0.0388, 0.0539, 0.0732, 0.0932, 0.0887, 0.0638, 0.0501, 0.0447, 0.0428,
        0.0483, 0.0635, 0.0882, 0.1251, 0.1748, 0.2331, 0.2873, 0.3229, 0.3281, 0.3066,
        0.2701, 0.2326, 0.2011, 0.1769, 0.1584, 0.1453, 0.1372, 0.1326, 0.1310, 0.1314,
        0.1343, 0.1394, 0.1476, 0.1595, 0.1771, 0.2032, 0.2449, 0.3099, 0.4149, 0.5818,
        0.8151, 1.0000, 0.8306, 0.4565, 0.2472, 0.1528, 0.1043, 0.0790, 0.0640, 0.0538,
        0.0461, 0.0400, 0.0348, 0.0306, 0.0266, 0.0230, 0.0199, 0.0174, 0.0148, 0.0131,
        0.0113, 0.0097, 0.0085, 0.0072, 0.0064, 0.0056, 0.0048, 0.0043, 0.0038, 0.0033, 0.0027
    ],
    "LED-V2": [
        0.0005, 0.0030, 0.0128, 0.0568, 0.2208, 0.5919, 0.9827, 1.0000, 0.7110, 0.4422,
        0.2856, 0.2297, 0.2401, 0.2856, 0.3444, 0.4002, 0.4471, 0.4852, 0.5198, 0.5539,
        0.5865, 0.6176, 0.6413, 0.6537, 0.6571, 0.6527, 0.6448, 0.6364, 0.6294, 0.6265,
        0.6275, 0.6309, 0.6378, 0.6443, 0.6502, 0.6551, 0.6596, 0.6630, 0.6680, 0.6739,
        0.6833, 0.6952, 0.7125, 0.7322, 0.7540, 0.7727, 0.7920, 0.8103, 0.8236, 0.8340,
        0.8365, 0.8325, 0.8211, 0.8019, 0.7767, 0.7446, 0.7070, 0.6645, 0.6210, 0.5751,
        0.5282, 0.4832, 0.4382, 0.3953, 0.3542, 0.3147, 0.2792, 0.2475, 0.2184, 0.1917,
        0.1675, 0.1458, 0.1275, 0.1107, 0.0963, 0.0840, 0.0726, 0.0642, 0.0543, 0.0474, 0.0415
    ],
}

FONT_PATH = "/System/Library/Fonts/Hiragino Sans GB.ttc"
FONT_FALLBACK = "/System/Library/Fonts/STHeiti Medium.ttc"
FONT_ITALIC = "/Library/Fonts/Times New Roman Italic.ttf"


def font(size, bold=False):
    path = FONT_PATH if os.path.exists(FONT_PATH) else FONT_FALLBACK
    try:
        # Hiragino Sans GB.ttc 的 face 顺序：0 = W3, 2 = W6(粗)
        return ImageFont.truetype(path, int(size * SS), index=2 if bold else 0)
    except OSError:
        return ImageFont.truetype(path, int(size * SS))


def ifont(size):
    if os.path.exists(FONT_ITALIC):
        return ImageFont.truetype(FONT_ITALIC, int(size * SS))
    return font(size)


def canvas(w, h, bg=WHITE):
    im = Image.new("RGB", (int(w * SS), int(h * SS)), bg)
    return im, ImageDraw.Draw(im)


def finish(im, path):
    out = im.resize((im.width // SS, im.height // SS), Image.LANCZOS)
    out.save(path)
    print("  %-42s %dx%d" % (os.path.basename(path), out.width, out.height))


def text(d, xy, s, f, fill=INK, anchor="mm"):
    d.text((xy[0] * SS, xy[1] * SS), s, font=f, fill=fill, anchor=anchor)


def rect(d, box, outline=None, fill=None, width=1, radius=0):
    box = [v * SS for v in box]
    if radius:
        d.rounded_rectangle(box, radius=radius * SS, outline=outline, fill=fill,
                            width=int(width * SS))
    else:
        d.rectangle(box, outline=outline, fill=fill, width=int(width * SS))


def line(d, xy, fill=BORDER, width=1):
    d.line([v * SS for v in xy], fill=fill, width=max(1, int(width * SS)))


def poly(d, pts, fill=None, outline=None, width=1):
    p = [(x * SS, y * SS) for x, y in pts]
    d.polygon(p, fill=fill, outline=outline, width=max(1, int(width * SS)))


def ellipse(d, box, fill=None, outline=None, width=1):
    d.ellipse([v * SS for v in box], fill=fill, outline=outline,
              width=max(1, int(width * SS)))


def arrow(d, p0, p1, fill=INK, width=3, head=11):
    """带箭头的直线。"""
    x0, y0 = p0
    x1, y1 = p1
    ang = math.atan2(y1 - y0, x1 - x0)
    bx, by = x1 - head * math.cos(ang), y1 - head * math.sin(ang)
    line(d, (x0, y0, bx, by), fill=fill, width=width)
    w = head * 0.46
    poly(d, [(x1, y1),
             (bx - w * math.sin(ang), by + w * math.cos(ang)),
             (bx + w * math.sin(ang), by - w * math.cos(ang))], fill=fill)


def block_arrow(d, p0, p1, body=16, head=30, fill=(206, 211, 226), outline=None):
    """粗的空心块状箭头，用来表示流程。"""
    x0, y0 = p0
    x1, y1 = p1
    ang = math.atan2(y1 - y0, x1 - x0)
    ux, uy = math.cos(ang), math.sin(ang)
    nx, ny = -uy, ux
    bx, by = x1 - head * ux, y1 - head * uy
    h = body / 2.0
    w = head * 0.52
    poly(d, [(x0 + nx * h, y0 + ny * h),
             (bx + nx * h, by + ny * h),
             (bx + nx * w, by + ny * w),
             (x1, y1),
             (bx - nx * w, by - ny * w),
             (bx - nx * h, by - ny * h),
             (x0 - nx * h, y0 - ny * h)], fill=fill, outline=outline, width=1)


def dashed(d, p0, p1, fill=MUTED, width=1, dash=7, gap=5):
    x0, y0 = p0
    x1, y1 = p1
    total = math.hypot(x1 - x0, y1 - y0)
    if total == 0:
        return
    ux, uy = (x1 - x0) / total, (y1 - y0) / total
    t = 0.0
    while t < total:
        e = min(t + dash, total)
        line(d, (x0 + ux * t, y0 + uy * t, x0 + ux * e, y0 + uy * e),
             fill=fill, width=width)
        t = e + gap


# --------------------------------------------------------------------------
# 混色运算：加法在黑底上相加，减法在白底上相乘
# --------------------------------------------------------------------------
def disc_mask(w, h, cx, cy, r):
    yy, xx = np.mgrid[0:h, 0:w]
    d = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2)
    # 边缘 1px 过渡，缩小锯齿
    return np.clip(r - d, 0.0, 1.0)


def additive_discs(w, h, discs, bg=(0, 0, 0)):
    """discs: [(cx, cy, r, color)]，通道相加。"""
    out = np.zeros((h, w, 3), dtype=np.float64)
    out[:] = bg
    for cx, cy, r, col in discs:
        m = disc_mask(w, h, cx, cy, r)[..., None]
        out = out + m * np.array(col, dtype=np.float64)
    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8))


def subtractive_discs(w, h, discs, bg=(255, 255, 255)):
    """discs: [(cx, cy, r, color)]，通道相乘（每片当成一块滤光片）。"""
    out = np.zeros((h, w, 3), dtype=np.float64)
    out[:] = bg
    for cx, cy, r, col in discs:
        m = disc_mask(w, h, cx, cy, r)[..., None]
        f = np.array(col, dtype=np.float64) / 255.0
        out = out * (1.0 - m) + out * m * f
    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8))


# --------------------------------------------------------------------------
# 小图表：三波段柱状图 / 连续光谱曲线
# --------------------------------------------------------------------------
def band_chart(d, box, bars, ylabel=None, xlabel=True, label=None,
               bg=None, axis=True, bar_labels=("B", "G", "R"), scale=0.70):
    """在 box 内画一个 B/G/R 三槽的柱状图。bars: [h_B, h_G, h_R]，0~1，None 为空。

    scale 把柱子压到图框高度的一定比例，给顶部的 P(λ)/T(λ) 标签留出净空。
    """
    x0, y0, x1, y1 = box
    if bg:
        rect(d, box, fill=bg)
    ox, oy = x0 + 20, y1 - 16
    if axis:
        arrow(d, (ox, oy), (x1 - 4, oy), fill=INK, width=1.4, head=6)
        arrow(d, (ox, oy), (ox, y0 + 4), fill=INK, width=1.4, head=6)
    slot = (x1 - 12 - ox) / 3.6
    cols = (B, G, R)
    f_s = font(12)
    for i, hv in enumerate(bars):
        bx = ox + 6 + i * slot
        if hv:
            bh = (oy - y0 - 12) * hv * scale
            rect(d, (bx, oy - bh, bx + slot * 0.82, oy), fill=cols[i])
        if xlabel:
            text(d, (bx + slot * 0.41, oy + 10), bar_labels[i], f_s, fill=cols[i])
    if ylabel:
        text(d, (x0 + 10, (y0 + y1) / 2 - 6), ylabel, ifont(15), fill=INK,
             anchor="mm")
    if label:
        text(d, ((x0 + x1) / 2, y0 - 10), label, font(13), fill=MUTED)


def gauss(x, mu, sigma, amp):
    return amp * np.exp(-0.5 * ((x - mu) / sigma) ** 2)


def spd_plot(im, d, box, peaks=None, title=None, sub=None, fill_curve=True,
             ymax=1.08, xr=(380, 780), samples=None):
    """在 box 内画一条相对光谱分布曲线。

    samples 给定时按等间隔采样数据绘制（实测数据）；
    否则由 peaks=[(中心, 宽, 高)] 合成（仅用于模式图）。
    """
    x0, y0, x1, y1 = box
    rect(d, box, fill=PANEL)
    for i in range(1, 5):
        yy = y0 + (y1 - y0) * i / 5.0
        line(d, (x0, yy, x1, yy), fill=GRID, width=1)
    for i in range(1, 5):
        xx = x0 + (x1 - x0) * i / 5.0
        line(d, (xx, y0, xx, y1), fill=GRID, width=1)

    if samples is not None:
        ys = np.asarray(samples, dtype=float)
        xs = np.linspace(xr[0], xr[1], len(ys))
    else:
        xs = np.linspace(xr[0], xr[1], 900)
        ys = np.zeros_like(xs)
        for mu, sg, amp in peaks:
            ys += gauss(xs, mu, sg, amp)
    ys = ys / max(ys.max(), 1e-9)

    px = x0 + (xs - xr[0]) / (xr[1] - xr[0]) * (x1 - x0)
    py = y1 - ys / ymax * (y1 - y0)
    pts = list(zip(px, py))
    if fill_curve:
        d.polygon([(x * SS, y * SS) for x, y in pts] +
                  [(x1 * SS, y1 * SS), (x0 * SS, y1 * SS)],
                  fill=(226, 229, 243))
    d.line([(x * SS, y * SS) for x, y in pts], fill=CURVE,
           width=int(2 * SS), joint="curve")
    rect(d, box, outline=BORDER, width=1)

    # 底部可见光色带
    cb_h = 9
    strip = np.zeros((1, int((x1 - x0) * SS), 3), dtype=np.uint8)
    for i in range(strip.shape[1]):
        wl = xr[0] + (xr[1] - xr[0]) * i / strip.shape[1]
        strip[0, i] = wavelength_rgb(wl)
    band = Image.fromarray(strip).resize(
        (int((x1 - x0) * SS), int(cb_h * SS)), Image.NEAREST)
    im.paste(band, (int(x0 * SS), int((y1 + 5) * SS)))

    f_s = font(11)
    for k in range(6):
        val = k / 5.0
        yy = y1 - val / ymax * (y1 - y0)
        text(d, (x0 - 12, yy), "%.1f" % val, font(10), fill=MUTED, anchor="rm")
    for wl in (400, 500, 600, 700):
        xx = x0 + (wl - xr[0]) / (xr[1] - xr[0]) * (x1 - x0)
        text(d, (xx, y1 + cb_h + 14), str(wl), f_s, fill=MUTED)
    text(d, ((x0 + x1) / 2, y1 + cb_h + 30), "波长 [ nm ]", font(12), fill=MUTED)
    if title:
        text(d, ((x0 + x1) / 2, y0 - 34), title, font(16, True), fill=INK)
    if sub:
        text(d, ((x0 + x1) / 2, y0 - 14), sub, font(12), fill=MUTED)


def wavelength_rgb(wl):
    """可见光波长到近似 sRGB，只用于底部色带。"""
    if wl < 380 or wl > 780:
        return (16, 16, 20)
    if wl < 440:
        r, g, b = -(wl - 440) / 60.0, 0.0, 1.0
    elif wl < 490:
        r, g, b = 0.0, (wl - 440) / 50.0, 1.0
    elif wl < 510:
        r, g, b = 0.0, 1.0, -(wl - 510) / 20.0
    elif wl < 580:
        r, g, b = (wl - 510) / 70.0, 1.0, 0.0
    elif wl < 645:
        r, g, b = 1.0, -(wl - 645) / 65.0, 0.0
    else:
        r, g, b = 1.0, 0.0, 0.0
    if wl > 700:
        s = 0.3 + 0.7 * (780 - wl) / 80.0
    elif wl < 420:
        s = 0.3 + 0.7 * (wl - 380) / 40.0
    else:
        s = 1.0
    return tuple(int(255 * ((v * s) ** 0.8)) for v in (r, g, b))


def curve_panel(d, box, curves, title=None, xlabels=("B", "G", "R"),
                ylabel=None, bg=PANEL):
    """在 box 内画若干条以 0~1 为定义域的曲线。curves: [(ys, color)]。"""
    x0, y0, x1, y1 = box
    rect(d, box, fill=bg, outline=BORDER, width=1)
    for ys, col in curves:
        n = len(ys)
        pts = [(x0 + (x1 - x0) * i / (n - 1), y1 - (y1 - y0 - 10) * ys[i] - 6)
               for i in range(n)]
        d.line([(x * SS, y * SS) for x, y in pts], fill=col,
               width=int(2.2 * SS), joint="curve")
    f_s = font(13)
    cols = (B, G, R)
    for i, lb in enumerate(xlabels):
        xx = x0 + (x1 - x0) * (i + 0.5) / len(xlabels)
        text(d, (xx, y1 + 13), lb, f_s, fill=cols[i % 3])
    if title:
        text(d, ((x0 + x1) / 2, y0 - 13), title, font(14, True), fill=INK)
    if ylabel:
        text(d, (x0 - 16, (y0 + y1) / 2), ylabel, ifont(15), fill=INK)


def bump(n, mu, sg, amp=1.0):
    x = np.linspace(0, 1, n)
    return gauss(x, mu, sg, amp)


# ==========================================================================
# 图 1  混色的分类
# ==========================================================================
def fig_taxonomy(out):
    W, H = 1020, 470
    im, d = canvas(W, H)
    f_b = font(19, True)
    f_n = font(15)

    def node(cx, cy, w, h, label, fill, edge):
        rect(d, (cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2),
             fill=fill, outline=edge, width=2, radius=8)
        text(d, (cx, cy), label, f_b, fill=INK)

    def elbow(x0, y0, x1, y1):
        xm = x0 + 26
        line(d, (x0, y0, xm, y0), fill=BORDER, width=2)
        line(d, (xm, y0, xm, y1), fill=BORDER, width=2)
        line(d, (xm, y1, x1, y1), fill=BORDER, width=2)

    node(92, 210, 120, 52, "混色", (247, 248, 252), BORDER)

    elbow(152, 210, 222, 104)
    elbow(152, 210, 222, 292)
    node(292, 104, 140, 52, "减法混色", M_L, (214, 170, 204))
    node(292, 292, 140, 52, "加法混色", B_L, (168, 190, 232))

    elbow(362, 292, 442, 216)
    elbow(362, 292, 442, 348)
    node(536, 216, 188, 52, "同时加法混色", B_L, (168, 190, 232))
    node(536, 348, 188, 52, "中间混色", G_L, (172, 214, 190))

    elbow(630, 348, 712, 314)
    elbow(630, 348, 712, 384)
    node(786, 314, 148, 46, "旋转混色", G_L, (172, 214, 190))
    node(786, 384, 148, 46, "并列混色", G_L, (172, 214, 190))

    text(d, (376, 104), "水粉、墨水、滤光片的叠加", f_n, fill=MUTED, anchor="lm")
    text(d, (642, 216), "色光投射到同一区域", f_n, fill=MUTED, anchor="lm")
    text(d, (536, 392), "又称平均混色", f_n, fill=MUTED)

    text(d, (W / 2, H - 26),
         "减法混色与同时加法混色在眼外完成，中间混色在眼内完成",
         font(15), fill=MUTED)
    finish(im, os.path.join(out, "mixing-taxonomy.png"))


# ==========================================================================
# 图 2  三投影机的同时加法混色
# ==========================================================================
def fig_projectors(out):
    W, H = 720, 806
    im, d = canvas(W, H)

    sw, sh = 640, 508
    sx, sy = (W - sw) // 2, 34
    r = 152
    cx, cy = sw / 2, 210
    discs = [(cx - r * 0.60, cy - r * 0.30, r, R),
             (cx + r * 0.60, cy - r * 0.30, r, B),
             (cx, cy + r * 0.62, r, G)]
    screen = additive_discs(int(sw * SS), int(sh * SS),
                            [(x * SS, y * SS, rr * SS, c) for x, y, rr, c in discs])
    im.paste(screen, (int(sx * SS), int(sy * SS)))

    f_l = font(24, True)
    text(d, (sx + cx - r * 1.28, sy + cy - r * 0.86), "R", f_l, fill=(255, 150, 146))
    text(d, (sx + cx + r * 1.28, sy + cy - r * 0.86), "B", f_l, fill=(150, 180, 255))
    text(d, (sx + cx, sy + cy + r * 1.62), "G", f_l, fill=(150, 235, 178))

    f_s = font(15, True)
    text(d, (sx + cx, sy + cy - r * 0.32), "W", f_s, fill=(70, 70, 80))
    text(d, (sx + cx - r * 0.72, sy + cy + r * 0.30), "Y", f_s, fill=(90, 80, 20))
    text(d, (sx + cx + r * 0.72, sy + cy + r * 0.30), "C", f_s, fill=(20, 80, 86))
    text(d, (sx + cx, sy + cy - r * 0.92), "M", f_s, fill=(90, 26, 74))

    # 三台投影机
    py = 706
    for px, col in ((150, R), (360, G), (570, B)):
        poly(d, [(px - 58, py + 34), (px + 58, py + 34),
                 (px + 46, py - 16), (px - 46, py - 16)],
             fill=(214, 218, 228), outline=(176, 182, 198), width=2)
        ellipse(d, (px - 22, py - 30, px + 22, py - 4),
                fill=(248, 249, 252), outline=(176, 182, 198), width=2)
    y_screen = sy + sh
    for px, col, tgt in ((150, R, (sx + cx - r * 0.60, sy + cy)),
                         (360, G, (sx + cx, sy + cy + r * 0.62)),
                         (570, B, (sx + cx + r * 0.60, sy + cy))):
        # 光束只画到黑屏下沿，不要压在画面上
        t = (y_screen - (py - 26)) / (tgt[1] - (py - 26))
        ex = px + (tgt[0] - px) * t
        line(d, (px, py - 26, ex, y_screen), fill=col, width=2)

    text(d, (W / 2, H - 22), "三色光重叠的区域，能量是相加的", font(15), fill=MUTED)
    finish(im, os.path.join(out, "additive-rgb-projectors.png"))


# ==========================================================================
# 图 3  加法混色的光谱解释
# ==========================================================================
def fig_additive_spectra(out):
    W, H = 1000, 780
    im, d = canvas(W, H)
    bw, bh = 250, 150

    def cell(cx, cy, bars, caption, tint):
        box = (cx - bw / 2, cy - bh / 2, cx + bw / 2, cy + bh / 2)
        rect(d, box, fill=tint, outline=BORDER, width=1, radius=6)
        band_chart(d, (box[0] + 6, box[1] + 8, box[2] - 6, box[3] - 6),
                   bars, ylabel=None, bg=None)
        text(d, (cx - bw / 2 + 46, cy - bh / 2 + 22), "P (λ)", ifont(15), fill=INK,
             anchor="lm")
        text(d, (cx, cy + bh / 2 + 18), caption, font(15, True), fill=INK)

    cell(176, 86, [None, None, 1.0], "R", R_L)
    cell(500, 86, [None, 1.0, None], "G", G_L)
    cell(824, 86, [1.0, None, None], "B", B_L)

    cell(176, 340, [None, 1.0, 1.0], "R + G = Y", Y_L)
    cell(500, 340, [1.0, 1.0, None], "G + B = C", C_L)
    cell(824, 340, [1.0, None, 1.0], "B + R = M", M_L)

    cell(500, 594, [1.0, 1.0, 1.0], "R + G + B = W", (244, 245, 249))

    for x in (176, 500, 824):
        arrow(d, (x, 188), (x, 244), fill=(190, 196, 212), width=3, head=12)
    arrow(d, (500, 442), (500, 498), fill=(190, 196, 212), width=3, head=12)

    text(d, (W / 2, H - 24),
         "两束光叠加，就是两条光谱分布相加；能量落在哪几个波段，决定了看到的颜色",
         font(15), fill=MUTED)
    finish(im, os.path.join(out, "additive-spectra.png"))


# ==========================================================================
# 图 4  减法混色三圆
# ==========================================================================
def fig_subtractive_circles(out):
    W, H = 760, 730
    im, d = canvas(W, H)

    pw, ph = 700, 600
    px, py = (W - pw) // 2, 30
    r = 172
    cx, cy = pw / 2, 240
    discs = [(cx - r * 0.60, cy - r * 0.30, r, Y),
             (cx + r * 0.60, cy - r * 0.30, r, C),
             (cx, cy + r * 0.62, r, M)]
    panel = subtractive_discs(int(pw * SS), int(ph * SS),
                              [(x * SS, y * SS, rr * SS, c) for x, y, rr, c in discs])
    im.paste(panel, (int(px * SS), int(py * SS)))

    f_l = font(19, True)
    text(d, (px + cx - r * 1.34, py + cy - r * 0.92), "黄 (Y)", f_l, fill=INK)
    text(d, (px + cx + r * 1.34, py + cy - r * 0.92), "青 (C)", f_l, fill=INK)
    text(d, (px + cx, py + cy + r * 1.70), "品红 (M)", f_l, fill=INK)

    f_s = font(16, True)
    text(d, (px + cx, py + cy - r * 0.30), "K", f_s, fill=(228, 228, 234))
    text(d, (px + cx - r * 0.70, py + cy + r * 0.30), "R", f_s, fill=(255, 226, 224))
    text(d, (px + cx + r * 0.70, py + cy + r * 0.30), "B", f_s, fill=(224, 234, 255))
    text(d, (px + cx, py + cy - r * 0.94), "G", f_s, fill=(232, 250, 238))

    text(d, (W / 2, H - 28),
         "Y + C = G　　C + M = B　　M + Y = R　　Y + M + C = K",
         font(16), fill=INK)
    finish(im, os.path.join(out, "subtractive-ymc-circles.png"))


# ==========================================================================
# 图 5  YMC 滤光片的吸收与透过率
# ==========================================================================
def fig_filter_transmission(out):
    W, H = 1000, 640
    im, d = canvas(W, H)

    cols = [
        ("黄滤光片 (Y)", Y, [1, 1, 1], 0, Y_L),
        ("品红滤光片 (M)", M, [1, 1, 1], 1, M_L),
        ("青滤光片 (C)", C, [1, 1, 1], 2, C_L),
    ]
    for i, (name, col, _, absorb, tint) in enumerate(cols):
        cx = 172 + i * 328
        text(d, (cx, 40), name, font(19, True), fill=INK)

        text(d, (cx, 84), "白光 W", font(14), fill=MUTED)
        block_arrow(d, (cx, 98), (cx, 140), body=18, head=22,
                    fill=(236, 238, 245), outline=BORDER)

        # 三路入射箭头
        chans = (B, G, R)
        names = ("B", "G", "R")
        for j in range(3):
            ax = cx - 62 + j * 62
            text(d, (ax, 158), names[j], font(15, True), fill=chans[j])
            arrow(d, (ax, 172), (ax, 214), fill=chans[j], width=4, head=11)

        # 滤光片薄板（平行四边形）
        poly(d, [(cx - 128, 236), (cx + 96, 236), (cx + 128, 268), (cx - 96, 268)],
             fill=col, outline=(150, 152, 165), width=1)

        # 出射：被吸收的那一路停在板上
        for j in range(3):
            ax = cx - 62 + j * 62
            if j == absorb:
                text(d, (ax + 2, 296), "吸收", font(13, True), fill=chans[j])
            else:
                arrow(d, (ax, 276), (ax, 336), fill=chans[j], width=4, head=11)

        box = (cx - 116, 386, cx + 116, 496)
        bars = [1.0, 1.0, 1.0]
        bars[absorb] = None
        band_chart(d, box, bars, bg=tint)
        rect(d, box, outline=BORDER, width=1)
        text(d, (cx - 80, 402), "T (λ)", ifont(15), fill=INK, anchor="lm")
        text(d, (cx, 528), ["吸收短波 (B)", "吸收中波 (G)", "吸收长波 (R)"][absorb],
             font(15), fill=MUTED)

    text(d, (W / 2, H - 34),
         "每一片滤光片都只拿走一个波段，剩下的两个波段透过去",
         font(15), fill=MUTED)
    finish(im, os.path.join(out, "ymc-filter-transmission.png"))


# ==========================================================================
# 图 6  两片滤光片叠加
# ==========================================================================
def fig_two_filters(out):
    W, H = 1100, 430
    im, d = canvas(W, H)

    combos = [
        ("青 (C)", C, "黄 (Y)", Y, "绿 G", G, [None, 1.0, None]),
        ("青 (C)", C, "品红 (M)", M, "蓝 B", B, [1.0, None, None]),
        ("品红 (M)", M, "黄 (Y)", Y, "红 R", R, [None, None, 1.0]),
    ]
    for i, (n1, c1, n2, c2, rname, rc, bars) in enumerate(combos):
        x0 = 28 + i * 358
        cy = 168
        rect(d, (x0, 44, x0 + 330, 292), fill=(250, 251, 253),
             outline=BORDER, width=1, radius=8)

        text(d, (x0 + 38, cy - 26), "W", font(16, True), fill=(120, 124, 138))
        arrow(d, (x0 + 22, cy), (x0 + 86, cy), fill=(196, 200, 214), width=6, head=13)

        poly(d, [(x0 + 104, cy - 58), (x0 + 124, cy - 72),
                 (x0 + 124, cy + 44), (x0 + 104, cy + 58)],
             fill=c1, outline=(150, 152, 165), width=1)
        poly(d, [(x0 + 150, cy - 58), (x0 + 170, cy - 72),
                 (x0 + 170, cy + 44), (x0 + 150, cy + 58)],
             fill=c2, outline=(150, 152, 165), width=1)
        text(d, (x0 + 100, cy + 84), n1, font(13), fill=INK)
        text(d, (x0 + 178, cy + 84), n2, font(13), fill=INK)

        arrow(d, (x0 + 186, cy), (x0 + 248, cy), fill=rc, width=6, head=13)
        text(d, (x0 + 286, cy), rname, font(20, True), fill=rc)

        box = (x0 + 214, 200, x0 + 318, 276)
        band_chart(d, box, bars, bg=(245, 246, 250))
        rect(d, box, outline=BORDER, width=1)

    text(d, (W / 2, H - 42),
         "两片叠加之后能通过的，只有两者透过波段的公共部分",
         font(16), fill=MUTED)
    finish(im, os.path.join(out, "subtractive-two-filters.png"))


# ==========================================================================
# 图 7  三片叠加，能量逐级减小
# ==========================================================================
def fig_subtractive_stack(out):
    W, H = 1000, 570
    im, d = canvas(W, H)

    stages = [
        ("白光 W", [1.0, 1.0, 1.0], None, None),
        ("透过 Y", [None, 1.0, 1.0], Y, "黄 (Y)"),
        ("透过 Y·M", [None, None, 1.0], M, "品红 (M)"),
        ("透过 Y·M·C", [None, None, None], C, "青 (C)"),
    ]
    cy = 300
    widths = (26, 20, 13, 6)
    for i, (cap, bars, col, fname) in enumerate(stages):
        cx = 128 + i * 248
        box = (cx - 104, 60, cx + 104, 190)
        band_chart(d, box, bars, bg=(246, 247, 251))
        rect(d, box, outline=BORDER, width=1)
        text(d, (cx - 68, 78), "P (λ)", ifont(15), fill=INK, anchor="lm")
        text(d, (cx, 210), cap, font(15, True), fill=INK)
        if i == 3:
            text(d, (cx + 10, 132), "几乎为 0", font(14), fill=MUTED)

        if i < 3:
            # 下一片滤光片的位置，箭头要停在它前面，不能穿过去
            plate_x = (cx + 248) - 92
            block_arrow(d, (cx + 34, cy), (plate_x - 16, cy),
                        body=widths[i], head=26,
                        fill=(232, 234, 242), outline=BORDER)
        if col:
            px = cx - 92
            poly(d, [(px - 12, cy - 74), (px + 10, cy - 88),
                     (px + 10, cy + 58), (px - 12, cy + 72)],
                 fill=col, outline=(150, 152, 165), width=1)
            text(d, (px, cy + 96), fname, font(15, True), fill=INK)

    text(d, (W / 2, H - 40),
         "每通过一片滤光片，就被拿走一个波段；三片过后，白光所剩无几",
         font(16), fill=MUTED)
    finish(im, os.path.join(out, "subtractive-stack.png"))


# ==========================================================================
# 图 8a  四种白色 LED 的封装结构（模式图）
# ==========================================================================
LED_ROWS = [
    ("补色方式", "蓝 + 黄 两颗芯片", [B, Y], None, None),
    ("三原色 RGB 方式", "蓝 + 绿 + 红 三颗芯片", [R, G, B], None, "LED-RGB1"),
    ("补色荧光方式", "蓝光芯片 + 黄色荧光体", [B], Y, "LED-B3"),
    ("三原色荧光方式", "紫光芯片 + RGB 三种荧光体", [(146, 92, 214)],
     (236, 210, 170), "LED-V2"),
]


def _led_package(im, d, bx, top, name, sub, chips, phosphor, seed):
    """画一颗 LED 的封装剖面：反射杯 + 芯片 (+ 荧光体) + 出射光线。"""
    W_, H_ = 430, 210
    cy = top + 118
    rect(d, (bx, top + 30, bx + W_, top + H_), fill=(233, 236, 243),
         outline=BORDER, width=1, radius=6)
    cupx = bx + W_ / 2
    poly(d, [(cupx - 158, top + 48), (cupx + 158, top + 48),
             (cupx + 66, cy + 58), (cupx - 66, cy + 58)],
         fill=(250, 250, 252), outline=(176, 182, 198), width=2)

    n = len(chips)
    for j, col in enumerate(chips):
        w = 42 if n <= 2 else 32
        gx = cupx - (n - 1) * (w + 10) / 2 + j * (w + 10)
        rect(d, (gx - w / 2, cy + 40, gx + w / 2, cy + 56), fill=col)

    if phosphor:
        for j in range(13):
            dx = cupx - 138 + j * 23
            ellipse(d, (dx - 9, top + 66, dx + 9, top + 82), fill=phosphor,
                    outline=(180, 170, 140), width=1)

    for j in range(11):
        ang = math.radians(-142 + j * 10.4)
        sx0, sy0 = cupx + (j - 5) * 4.0, cy + 40
        ln = 56 if phosphor else 84
        col = phosphor if phosphor else chips[j % n]
        arrow(d, (sx0, sy0), (sx0 + ln * math.cos(ang), sy0 + ln * math.sin(ang)),
              fill=col, width=1.6, head=7)

    text(d, (cupx, top + 8), name, font(19, True), fill=INK)
    text(d, (cupx, top + H_ + 22), sub, font(15), fill=MUTED)


def fig_white_led(out):
    W, H = 1000, 596
    im, d = canvas(W, H)
    for i, (name, sub, chips, phosphor, _) in enumerate(LED_ROWS):
        bx = 50 + (i % 2) * 470
        top = 28 + (i // 2) * 262
        _led_package(im, d, bx, top, name, sub, chips, phosphor, i)
    text(d, (W / 2, H - 22),
         "模式图：只表示芯片与荧光体的配置关系，不代表真实封装尺寸与出光分布",
         font(15), fill=MUTED)
    finish(im, os.path.join(out, "white-led-methods.png"))


# ==========================================================================
# 图 8b  三种白色 LED 的实测光谱（CIE 标准 LED 照明体）
# ==========================================================================
def fig_white_led_spectra(out):
    W, H = 1160, 420
    im, d = canvas(W, H)
    panels = [
        ("LED-B3", "补色荧光方式", "蓝光芯片 + 荧光粉"),
        ("LED-RGB1", "三原色 RGB 方式", "蓝 · 绿 · 红 三色芯片"),
        ("LED-V2", "三原色荧光方式", "紫光芯片 + RGB 荧光粉"),
    ]
    for i, (key, title, sub) in enumerate(panels):
        x0 = 86 + i * 364
        spd_plot(im, d, (x0, 96, x0 + 296, 300), title=title, sub=sub,
                 samples=CIE_LED_SPD[key])
        text(d, (x0 - 58, 198), "相\n对\n能\n量", font(12), fill=MUTED)

    text(d, (W / 2, H - 26),
         "数据：CIE 标准 LED 照明体 LED-B3 / LED-RGB1 / LED-V2"
         "（380-780 nm，5 nm 间隔，各自以峰值归一化）",
         font(14), fill=MUTED)
    finish(im, os.path.join(out, "white-led-spectra.png"))


# ==========================================================================
# 图 9  负片胶片的分层
# ==========================================================================
def fig_film_layers(out):
    W, H = 800, 420
    im, d = canvas(W, H)

    fx0, fx1 = 300, 730
    rect(d, (fx0, 96, fx1, 340), fill=(238, 239, 244), outline=(176, 182, 198),
         width=2)
    text(d, ((fx0 + fx1) / 2, 268), "片基（Film Base）", font(18), fill=INK)

    layers = [("保护膜", (246, 247, 250), 100, 116, MUTED),
              ("B 感光层", B_L, 116, 142, B),
              ("G 感光层", G_L, 142, 168, G),
              ("R 感光层", R_L, 168, 194, R)]
    for name, fill, y0, y1, col in layers:
        rect(d, (fx0, y0, fx1, y1), fill=fill, outline=(196, 202, 216), width=1)

    for i, (name, fill, y0, y1, col) in enumerate(layers):
        ly = 92 + i * 56
        rect(d, (62, ly - 20, 232, ly + 20), fill=fill,
             outline=(196, 202, 216), width=1, radius=6)
        text(d, (147, ly), name, font(17, True), fill=col if i else MUTED)
        line(d, (232, ly, 272, ly), fill=(196, 202, 216), width=1)
        arrow(d, (272, ly), (fx0 + 22, (y0 + y1) / 2), fill=(176, 182, 198),
              width=1.4, head=8)

    text(d, (W / 2, H - 32),
         "片基之上依次覆盖 R、G、B 三层感光材料",
         font(16), fill=MUTED)
    finish(im, os.path.join(out, "film-layers.png"))


# ==========================================================================
# 图 10  感光特性与发色特性互为补色
# ==========================================================================
def fig_film_curves(out):
    W, H = 1000, 480
    im, d = canvas(W, H)
    n = 200

    left = (86, 96, 430, 300)
    right = (570, 96, 914, 300)
    curve_panel(d, left,
                [(bump(n, 0.16, 0.085), B),
                 (bump(n, 0.47, 0.095), G),
                 (bump(n, 0.80, 0.090), R)],
                title="感光特性（负片胶片）")
    curve_panel(d, right,
                [(1 - bump(n, 0.16, 0.085, 0.92), (208, 158, 20)),
                 (1 - bump(n, 0.47, 0.095, 0.92), M),
                 (1 - bump(n, 0.80, 0.090, 0.92), C)],
                title="发色特性（显影之后）")

    text(d, (left[0] - 30, (left[1] + left[3]) / 2), "感\n光\n量", font(14),
         fill=MUTED)
    text(d, (right[2] + 34, (right[1] + right[3]) / 2), "透\n过\n率", font(14),
         fill=MUTED)

    # 两块面板之间放三枚对应关系的色片
    for k, (ca, cb, nm) in enumerate(
            ((B, (232, 186, 40), "B → Y"), (G, M, "G → M"), (R, C, "R → C"))):
        cy_ = 148 + k * 56
        rect(d, (462, cy_ - 15, 486, cy_ + 9), fill=ca)
        text(d, (500, cy_ - 3), "→", font(16), fill=MUTED)
        rect(d, (514, cy_ - 15, 538, cy_ + 9), fill=cb)
        text(d, (500, cy_ + 24), nm, font(13, True), fill=INK)

    text(d, (W / 2, H - 26),
         "每一层的着色，都是它自己感光波段的补色",
         font(16), fill=MUTED)
    finish(im, os.path.join(out, "film-sensitivity-vs-dye.png"))


# ==========================================================================
# 图 11  冲印光路
# ==========================================================================
def fig_film_printing(out):
    W, H = 1240, 560
    im, d = canvas(W, H)
    cy = 320

    def chip_box(x0, y0, label, items, textcol=INK):
        w = 44 * len(items) + 116
        rect(d, (x0, y0, x0 + w, y0 + 62), fill=(250, 251, 253),
             outline=BORDER, width=1, radius=6)
        text(d, (x0 + 52, y0 + 31), label, font(14), fill=MUTED)
        for j, (col, nm) in enumerate(items):
            cx = x0 + 106 + j * 44
            rect(d, (cx - 17, y0 + 11, cx + 17, y0 + 51), fill=col)
            text(d, (cx, y0 + 31), nm, font(15, True), fill=textcol)
        return x0 + w

    # 光源
    ellipse(d, (54, cy - 34, 114, cy + 26), fill=(253, 246, 214),
            outline=(214, 198, 130), width=2)
    rect(d, (74, cy + 22, 94, cy + 40), fill=(206, 210, 222),
         outline=(176, 182, 198), width=1)
    text(d, (84, cy + 66), "白色光源", font(15), fill=INK)
    for j in range(3):
        arrow(d, (124, cy - 22 + j * 22), (172, cy - 22 + j * 22),
              fill=(200, 204, 218), width=2, head=9)

    # 负片
    nx = 206
    rect(d, (nx, cy - 108, nx + 46, cy + 108), fill=(240, 241, 246),
         outline=(176, 182, 198), width=2)
    for j, col in enumerate((Y, M, C)):
        rect(d, (nx + 6 + j * 12, cy - 108, nx + 16 + j * 12, cy + 108), fill=col)
    text(d, (nx + 24, cy + 132), "负片", font(16, True), fill=INK)

    chip_box(96, 58, "发色层", ((Y, "Y"), (M, "M"), (C, "C")))
    line(d, (206, 120, nx + 24, cy - 112), fill=(200, 205, 220), width=1)

    # 镜头
    lx = 540
    ellipse(d, (lx - 22, cy - 92, lx + 22, cy + 92), fill=(226, 238, 246),
            outline=(160, 190, 206), width=2)
    text(d, (lx, cy + 120), "镜头", font(15), fill=MUTED)

    # 光路
    px = 852
    for off in (-84, -42, 42, 84):
        line(d, (nx + 46, cy + off, lx - 8, cy + off * 0.45),
             fill=(190, 196, 212), width=1)
        line(d, (lx + 8, cy - off * 0.45, px, cy - off),
             fill=(190, 196, 212), width=1)
    dashed(d, (124, cy), (px + 60, cy), fill=(212, 216, 228))

    # 相纸
    rect(d, (px, cy - 108, px + 46, cy + 108), fill=(248, 248, 250),
         outline=(176, 182, 198), width=2)
    for j, col in enumerate((R, G, B)):
        rect(d, (px + 6 + j * 12, cy - 108, px + 16 + j * 12, cy + 108), fill=col)
    text(d, (px + 24, cy + 132), "相纸", font(16, True), fill=INK)

    # 右侧两个说明框：整体放在相纸右边，引线不穿过任何色块
    bx = 940
    chip_box(bx, 58, "发色", ((C, "C"), (M, "M"), (Y, "Y")))
    chip_box(bx, 186, "感光层", ((R, "R"), (G, "G"), (B, "B")), textcol=WHITE)
    for j in range(3):
        ax = bx + 106 + j * 44
        arrow(d, (ax, 182), (ax, 124), fill=(176, 182, 198), width=2, head=9)
    line(d, (bx, 218, px + 50, cy - 60), fill=(200, 205, 220), width=1)

    text(d, (W / 2, H - 26),
         "负片显 YMC，相纸再取一次补色，于是回到原来的颜色",
         font(16), fill=MUTED)
    finish(im, os.path.join(out, "film-printing.png"))


# ==========================================================================
# 图 12  柠檬黄的一次往返
# ==========================================================================
def fig_lemon(out):
    W, H = 1060, 660
    im, d = canvas(W, H)

    def strip(x, cy, layers, h=88, w=42):
        rect(d, (x, cy - h, x + w, cy + h), fill=(244, 245, 249),
             outline=(176, 182, 198), width=2)
        k = len(layers)
        for j, col in enumerate(layers):
            if col is None:
                continue
            rect(d, (x + 5 + j * (w - 10) / k, cy - h,
                     x + 5 + (j + 1) * (w - 10) / k, cy + h), fill=col)

    # ---- 上排：拍摄 ----
    rect(d, (34, 44, 1026, 300), fill=(250, 251, 253), outline=BORDER,
         width=1, radius=10)
    text(d, (70, 68), "拍摄", font(18, True), fill=INK, anchor="lm")

    cy = 180
    ellipse(d, (78, cy - 46, 190, cy + 46), fill=(250, 222, 92),
            outline=(214, 180, 50), width=2)
    text(d, (134, cy + 74), "Y = G + R", font(16, True), fill=INK)

    block_arrow(d, (208, cy), (300, cy), body=26, head=32, fill=Y,
                outline=(214, 180, 50))

    strip(330, cy, [B_L, G_L, R_L])
    text(d, (351, cy + 112), "胶片", font(15), fill=MUTED)
    text(d, (351, cy - 112), "G、R 层曝光", font(14), fill=MUTED)

    block_arrow(d, (398, cy), (498, cy), body=22, head=30,
                fill=(232, 234, 242), outline=BORDER)
    text(d, (448, cy - 32), "显影", font(15, True), fill=INK)

    strip(528, cy, [None, M, C])
    text(d, (549, cy + 112), "负片", font(15), fill=MUTED)

    for j, (col, nm, yy) in enumerate(((M, "品红 M", 110), (C, "青 C", 218))):
        box = (682, yy - 44, 838, yy + 44)
        bars = [1.0, None, 1.0] if nm.startswith("品红") else [1.0, 1.0, None]
        band_chart(d, box, bars, bg=(246, 247, 251))
        rect(d, box, outline=BORDER, width=1)
        rect(d, (656, yy - 14, 678, yy + 10), fill=col)
        text(d, (862, yy), nm, font(15, True), fill=INK, anchor="lm")
    dashed(d, (570, 140), (648, 110), fill=(200, 205, 220))
    dashed(d, (570, 200), (648, 218), fill=(200, 205, 220))

    # ---- 下排：冲印 ----
    rect(d, (34, 340, 1026, 596), fill=(250, 251, 253), outline=BORDER,
         width=1, radius=10)
    text(d, (70, 364), "冲印", font(18, True), fill=INK, anchor="lm")

    cy2 = 474
    text(d, (96, cy2), "W", font(22, True), fill=(120, 124, 138))
    block_arrow(d, (124, cy2), (216, cy2), body=26, head=30,
                fill=(236, 238, 245), outline=BORDER)

    strip(240, cy2, [None, M, C])
    text(d, (261, cy2 + 112), "负片（M + C）", font(15), fill=MUTED)

    block_arrow(d, (306, cy2), (400, cy2), body=16, head=28, fill=B,
                outline=None)
    text(d, (353, cy2 - 34), "只剩 B", font(15, True), fill=B)

    strip(424, cy2, [B_L, G_L, R_L])
    text(d, (445, cy2 + 112), "相纸（B 层曝光）", font(15), fill=MUTED)

    block_arrow(d, (494, cy2), (606, cy2), body=22, head=30,
                fill=(232, 234, 242), outline=BORDER)
    text(d, (550, cy2 - 34), "显影 · 定影", font(15, True), fill=INK)

    ellipse(d, (648, cy2 - 46, 760, cy2 + 46), fill=(250, 222, 92),
            outline=(214, 180, 50), width=2)
    text(d, (704, cy2 + 74), "还原为 Y", font(16, True), fill=INK)

    text(d, (900, cy2), "Y → M + C → B → Y", font(19, True), fill=INK)

    text(d, (W / 2, H - 28),
         "两次取补色，柠檬的黄色就回来了",
         font(16), fill=MUTED)
    finish(im, os.path.join(out, "lemon-workflow.png"))


# ==========================================================================
# 图 13  理想颜料与实际颜料的分光透过率（模式图）
# ==========================================================================
def fig_black_ink(out):
    W, H = 1000, 680
    im, d = canvas(W, H)
    n = 240
    x = np.linspace(0, 1, n)

    def step(lo, hi, edges):
        """理想特性：在 edges 指定的区间取 hi，其余取 lo，边沿是突变。"""
        y = np.full(n, lo)
        for a, b in edges:
            y[(x >= a) & (x < b)] = hi
        return y

    def ramp(lo, hi, edges, k=26):
        """实际特性：阻带不为 0、通带不到 1，边沿带斜坡。"""
        y = np.full(n, lo)
        for a, b in edges:
            up = 1.0 / (1.0 + np.exp(-k * (x - a)))
            dn = 1.0 / (1.0 + np.exp(k * (x - b)))
            y = np.maximum(y, lo + (hi - lo) * up * dn)
        return y

    inks = [("黄 (Y)", Y_L, [(0.335, 1.02)]),
            ("品红 (M)", M_L, [(-0.02, 0.335), (0.665, 1.02)]),
            ("青 (C)", C_L, [(-0.02, 0.665)])]

    text(d, (250, 48), "理想的颜料", font(20, True), fill=INK)
    text(d, (740, 48), "实际的颜料", font(20, True), fill=INK)

    for i, (name, tint, edges) in enumerate(inks):
        top = 96 + i * 164
        for j, (ys, cx0) in enumerate(((step(0.0, 1.0, edges), 104),
                                       (ramp(0.10, 0.90, edges), 594))):
            box = (cx0, top, cx0 + 292, top + 116)
            curve_panel(d, box, [(ys, (58, 60, 74))], bg=tint)
            text(d, (box[0] + 14, box[1] + 58), "T (λ)", ifont(16), fill=INK,
                 anchor="lm")
        text(d, (466, top + 58), name, font(17, True), fill=INK)

    # 两处差别的标注
    text(d, (740, 614), "阻带不为 0 · 通带不到 1 · 边沿是斜坡",
         font(16, True), fill=(212, 118, 56))

    text(d, (W / 2, H - 42),
         "所以用实际颜料做减法混色，叠出来的并不是全波段截止的理想特性，",
         font(15), fill=MUTED)
    text(d, (W / 2, H - 18),
         "可见光波段内总有残留——混出来的黑不够黑，于是单独备一支 K",
         font(15), fill=MUTED)
    finish(im, os.path.join(out, "why-black-ink.png"))


# ==========================================================================
# 图 14  旋转的色陀螺
# ==========================================================================
def _disc_sectors(size, sectors, blur=0):
    """按 [(起始角, 终止角, 颜色)] 画一个圆盘，返回 RGBA。"""
    s = size * SS
    im = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    dd = ImageDraw.Draw(im)
    for a0, a1, col in sectors:
        dd.pieslice([0, 0, s - 1, s - 1], a0, a1, fill=col + (255,))
    return im


def fig_spinning_disc(out):
    W, H = 800, 340
    im, d = canvas(W, H)

    # 静止：能看清红绿两半
    disc = _disc_sectors(150, [(180, 360, R), (0, 180, G)])
    disc = disc.resize((150 * SS, 78 * SS), Image.LANCZOS).rotate(
        -18, expand=True, resample=Image.BICUBIC)
    im.paste(disc, (140 * SS, 96 * SS), disc)
    line(d, (238, 84, 196, 218), fill=(52, 54, 66), width=4)
    ellipse(d, (212, 140, 226, 154), fill=(52, 54, 66))
    text(d, (216, 268), "静止", font(17, True), fill=INK)

    # 旋转：混成橙黄
    disc2 = _disc_sectors(150, [(0, 360, (238, 176, 48))])
    disc2 = disc2.resize((150 * SS, 78 * SS), Image.LANCZOS)
    im.paste(disc2, (500 * SS, 118 * SS), disc2)
    line(d, (575, 86, 575, 218), fill=(52, 54, 66), width=4)
    ellipse(d, (568, 150, 582, 164), fill=(52, 54, 66))
    for j, r in enumerate((104, 118)):
        for a0, a1 in ((150, 210), (330, 30)):
            d.arc([(575 - r) * SS, (157 - r * 0.52) * SS,
                   (575 + r) * SS, (157 + r * 0.52) * SS],
                  a0, a1, fill=(178, 184, 200), width=int(2 * SS))
    text(d, (575, 268), "旋转", font(17, True), fill=INK)

    arrow(d, (330, 157), (430, 157), fill=(196, 200, 214), width=4, head=14)

    line(d, (60, 228, 740, 228), fill=(216, 220, 232), width=2)
    text(d, (W / 2, H - 20), "转起来之后，红与绿并成了一个橙黄", font(15),
         fill=MUTED)
    finish(im, os.path.join(out, "spinning-disc.png"))


# ==========================================================================
# 图 15  面积比决定混色结果
# ==========================================================================
def fig_spinning_results(out):
    W, H = 980, 510
    im, d = canvas(W, H)

    def avg(sectors):
        """按扇区圆心角加权平均——旋转混色的结果就是这个值。"""
        tot = np.zeros(3)
        wsum = 0.0
        for a0, a1, col in sectors:
            w = (a1 - a0) % 360 or 360
            tot += np.array(col, dtype=float) * w
            wsum += w
        return tuple(int(round(v)) for v in tot / wsum)

    GREY = (150, 152, 160)
    NAVY = (46, 62, 152)
    cases = [
        ([(0, 180, K), (180, 360, (252, 252, 252))], "黑白各半 → 灰"),
        ([(270, 90, R), (90, 270, Y)], "红黄各半 → 橙"),
        ([(270, 360, R), (0, 270, Y)], "黄 3 红 1 → 黄橙"),
        ([(240, 360, GREY), (0, 120, NAVY), (120, 240, Y)], "黄 · 灰 · 蓝 → 浊橄榄"),
    ]
    cases = [(sec, avg(sec), nm) for sec, nm in cases]

    text(d, (62, 130), "混色前", font(18, True), fill=INK)
    text(d, (62, 250), "旋转", font(16), fill=MUTED)
    text(d, (62, 366), "混色后", font(18, True), fill=INK)

    for i, (sectors, result, name) in enumerate(cases):
        cx = 236 + i * 182
        disc = _disc_sectors(124, sectors)
        im.paste(disc, (int((cx - 62) * SS), int(68 * SS)), disc)
        ellipse(d, (cx - 62, 68, cx + 62, 192), outline=(196, 202, 216), width=1)
        ellipse(d, (cx - 6, 124, cx + 6, 136), fill=(52, 54, 66))

        block_arrow(d, (cx, 218), (cx, 282), body=18, head=24,
                    fill=(226, 229, 240), outline=BORDER)

        ellipse(d, (cx - 62, 304, cx + 62, 428), fill=result,
                outline=(196, 202, 216), width=1)
        ellipse(d, (cx - 6, 360, cx + 6, 372), fill=(52, 54, 66))
        text(d, (cx, 452), name, font(15, True), fill=INK)

    text(d, (W / 2, H - 22),
         "混色后的色块由各扇区按面积比加权平均算出——所以旋转混色又叫平均混色",
         font(15), fill=MUTED)
    finish(im, os.path.join(out, "spinning-disc-results.png"))


# ==========================================================================
# 图 16  视锥细胞的时间响应
# ==========================================================================
def fig_cone_response(out):
    W, H = 940, 580
    im, d = canvas(W, H)

    x0, x1 = 160, 890
    period = (x1 - x0) / 5.0

    # 上：交替的阶跃光刺激
    ty = 92
    rect(d, (x0, ty - 22, x1, ty + 154), fill=(250, 251, 253),
         outline=BORDER, width=1)
    text(d, (96, ty + 66), "网膜上的\n光刺激", font(16, True), fill=INK)

    for idx, (col, base, phase) in enumerate(((R, ty + 34, 0), (G, ty + 120, 1))):
        pts = []
        for k in range(6):
            xa = x0 + k * period
            hi = (k % 2) == phase
            pts.append((xa, base - (34 if hi else 0)))
            pts.append((min(xa + period, x1), base - (34 if hi else 0)))
        d.line([(px * SS, py * SS) for px, py in pts], fill=col,
               width=int(2.2 * SS))
        for k in range(1, 6):
            xa = x0 + k * period
            line(d, (xa, base - 34, xa, base), fill=col, width=2.2)
        text(d, (x0 - 26, base - 17), ["红", "绿"][idx], font(15, True), fill=col)
    arrow(d, (x0, ty + 154), (x1 + 20, ty + 154), fill=INK, width=1.6, head=8)
    text(d, (x1 + 34, ty + 154), "t", ifont(17), fill=INK)

    # 下：带延迟与拖尾的生理响应
    by = 328
    rect(d, (x0, by - 22, x1, by + 186), fill=(250, 251, 253),
         outline=BORDER, width=1)
    text(d, (96, by + 82), "视锥细胞\n的响应", font(16, True), fill=INK)

    for idx, (col, base, phase, nm) in enumerate(
            ((R, by + 76, 0, "L"), (G, by + 172, 1, "M"))):
        xs = np.linspace(x0, x1, 1400)
        ys = np.zeros_like(xs)
        for k in range(6):
            if (k % 2) != phase:
                continue
            xa = x0 + k * period
            seg = (xs >= xa) & (xs < xa + period * 1.55)
            t = (xs[seg] - xa) / period
            ys[seg] = np.maximum(
                ys[seg], (1 - np.exp(-t / 0.20)) * np.exp(-t / 0.95))
        ys = ys / max(ys.max(), 1e-9)
        pts = [(xs[i], base - 56 * ys[i]) for i in range(len(xs))]
        d.line([(px * SS, py * SS) for px, py in pts], fill=col,
               width=int(2.2 * SS), joint="curve")
        text(d, (x0 - 26, base - 28), nm, font(16, True), fill=col)
    arrow(d, (x0, by + 186), (x1 + 20, by + 186), fill=INK, width=1.6, head=8)
    text(d, (x1 + 34, by + 186), "t", ifont(17), fill=INK)

    for k in range(1, 6):
        xa = x0 + k * period
        dashed(d, (xa, ty + 154), (xa, by - 22), fill=(212, 216, 228))

    text(d, (W / 2, H - 22),
         "刺激是方波，响应却有上升与拖尾——切换够快时，两条响应就在时间上重叠了",
         font(15), fill=MUTED)
    finish(im, os.path.join(out, "cone-temporal-response.png"))


# ==========================================================================
# 图 17  并列混色：棋盘由粗到细
# ==========================================================================
def fig_checker(out):
    W, H = 900, 476
    im, d = canvas(W, H)

    pw, ph = 236, 320
    for i, cell in enumerate((26, 7, 1)):
        px = 74 + i * 268
        n = int(math.ceil(pw * SS / (cell * SS)))
        m = int(math.ceil(ph * SS / (cell * SS)))
        arr = np.zeros((m, n, 3), dtype=np.uint8)
        for r_ in range(m):
            for c_ in range(n):
                arr[r_, c_] = R if (r_ + c_) % 2 else Y
        tile = Image.fromarray(arr).resize(
            (int(pw * SS), int(ph * SS)), Image.NEAREST)
        im.paste(tile, (int(px * SS), int(52 * SS)))
        rect(d, (px, 52, px + pw, 52 + ph), outline=(196, 202, 216), width=1)
        text(d, (px + pw / 2, 52 + ph + 28),
             ["颗粒较粗", "颗粒变细", "细到分辨不出"][i], font(17, True), fill=INK)

    text(d, (W / 2, H - 26),
         "超出视锥细胞的空间分辨能力之后，红与黄就并成了橙",
         font(16), fill=MUTED)
    finish(im, os.path.join(out, "juxtaposition-checker.png"))


# ==========================================================================
# 图 18  显示器的子像素
# ==========================================================================
def _subpixel_patch(size, lit):
    """画一小块 RGB 条状子像素，lit 指定哪几路发光。"""
    s = size * SS
    im = Image.new("RGB", (s, s), (24, 24, 28))
    dd = ImageDraw.Draw(im)
    cols = (R, G, B)
    cw = s / 9.0
    rh = s / 6.0
    for row in range(6):
        for col in range(9):
            ch = col % 3
            c = cols[ch] if ch in lit else (48, 48, 56)
            dd.rectangle([col * cw + cw * 0.14, row * rh + rh * 0.12,
                          (col + 1) * cw - cw * 0.14, (row + 1) * rh - rh * 0.16],
                         fill=c)
    return im


def fig_subpixels(out):
    W, H = 1060, 720
    im, d = canvas(W, H)

    # 显示器
    mx, my, mw, mh = 356, 200, 348, 268
    rect(d, (mx - 14, my - 14, mx + mw + 14, my + mh + 14), fill=(236, 240, 244),
         outline=(196, 202, 216), width=2, radius=10)
    rect(d, (mx + mw / 2 - 30, my + mh + 14, mx + mw / 2 + 30, my + mh + 52),
         fill=(222, 226, 236), outline=(196, 202, 216), width=2)
    rect(d, (mx + mw / 2 - 78, my + mh + 52, mx + mw / 2 + 78, my + mh + 70),
         fill=(222, 226, 236), outline=(196, 202, 216), width=2, radius=4)

    r = 86
    cx, cy = mw / 2, mh / 2 - 8
    scr = additive_discs(
        int(mw * SS), int(mh * SS),
        [((cx - r * 0.58) * SS, (cy - r * 0.30) * SS, r * SS, R),
         ((cx + r * 0.58) * SS, (cy - r * 0.30) * SS, r * SS, B),
         (cx * SS, (cy + r * 0.60) * SS, r * SS, G)])
    im.paste(scr, (int(mx * SS), int(my * SS)))

    f_s = font(15, True)
    spots = [
        ("W", (cx, cy - r * 0.30), (70, 70, 80), (0, 1, 2), (150, 96), "W = R + G + B"),
        ("M", (cx, cy - r * 0.92), (96, 30, 78), (0, 2), (906, 96), "M = R + B"),
        ("Y", (cx - r * 0.70, cy + r * 0.32), (92, 82, 20), (0, 1), (150, 580), "Y = R + G"),
        ("C", (cx + r * 0.70, cy + r * 0.32), (20, 82, 88), (1, 2), (906, 580), "C = G + B"),
    ]
    for nm, (sx, sy), tcol, lit, (gx, gy), cap in spots:
        px, py = mx + sx, my + sy
        ellipse(d, (px - 13, py - 13, px + 13, py + 13), outline=(250, 250, 250),
                width=2)
        text(d, (px + 26, py), nm, f_s, fill=tcol)

        patch = _subpixel_patch(112, lit)
        mask = Image.new("L", patch.size, 0)
        ImageDraw.Draw(mask).ellipse([0, 0, patch.size[0] - 1, patch.size[1] - 1],
                                     fill=255)
        im.paste(patch, (int((gx - 56) * SS), int((gy - 56) * SS)), mask)
        ellipse(d, (gx - 56, gy - 56, gx + 56, gy + 56), outline=(120, 126, 140),
                width=3)
        ang = math.atan2(py - gy, px - gx)
        dashed(d, (gx + 58 * math.cos(ang), gy + 58 * math.sin(ang)), (px, py),
               fill=(186, 192, 208))
        text(d, (gx, gy + 78), cap, font(16, True), fill=INK)

    text(d, (mx + mw / 2, my + mh + 106),
         "R、G、B 三色子像素规则排列，远看即为并列混色",
         font(16), fill=MUTED)
    finish(im, os.path.join(out, "display-subpixels.png"))


# ==========================================================================
# 图 19  纺织品的经纬交织
# ==========================================================================
def _weave(size_px, cell, c_warp, c_weft, bg):
    a = np.zeros((size_px, size_px, 3), dtype=np.uint8)
    a[:] = bg
    for y in range(size_px):
        for x in range(size_px):
            i, j = x // cell, y // cell
            over_warp = (i + j) % 2 == 0
            # 经线竖条，纬线横条，交替压盖
            in_warp = (x % cell) < cell * 0.94
            in_weft = (y % cell) < cell * 0.94
            if over_warp:
                a[y, x] = c_warp if in_warp else (c_weft if in_weft else bg)
            else:
                a[y, x] = c_weft if in_weft else (c_warp if in_warp else bg)
    return Image.fromarray(a)


def fig_textile(out):
    W, H = 900, 400
    im, d = canvas(W, H)

    NAVY = (44, 58, 104)
    CREAM = (236, 228, 208)
    BG = (198, 192, 180)

    big = _weave(260 * SS, 26 * SS, NAVY, CREAM, BG)
    im.paste(big, (int(70 * SS), int(56 * SS)))
    rect(d, (70, 56, 330, 316), outline=(176, 182, 198), width=2)
    text(d, (200, 344), "放大后：两色细线经纬交织", font(17, True), fill=INK)

    small = _weave(260 * SS, 1 * SS, NAVY, CREAM, BG)
    im.paste(small, (int(570 * SS), int(56 * SS)))
    rect(d, (570, 56, 830, 316), outline=(176, 182, 198), width=2)
    text(d, (700, 344), "远看：并成一种中间色", font(17, True), fill=INK)

    arrow(d, (368, 186), (532, 186), fill=(196, 200, 214), width=5, head=16)
    text(d, (450, 160), "退远", font(16), fill=MUTED)

    text(d, (W / 2, H - 18), "纺织品也是并列混色", font(15), fill=MUTED)
    finish(im, os.path.join(out, "textile-weave.png"))


# ==========================================================================
# 图 20  放大镜下的印刷网点
# ==========================================================================
def fig_halftone(out):
    W, H = 540, 480
    im, d = canvas(W, H)

    size = 376
    px, py = (W - size) // 2, 16
    arr = np.ones((size * SS, size * SS, 3), dtype=np.float64) * 255.0

    random.seed(20160623)
    inks = [C, M, Y, K]
    for _ in range(420):
        col = inks[random.randrange(4)]
        cx = random.uniform(0, size * SS)
        cy = random.uniform(0, size * SS)
        r = random.uniform(9, 16) * SS
        m = disc_mask(size * SS, size * SS, cx, cy, r)[..., None]
        f = np.array(col, dtype=np.float64) / 255.0
        arr = arr * (1 - m) + arr * m * f

    dots = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
    mask = Image.new("L", dots.size, 0)
    ImageDraw.Draw(mask).ellipse([0, 0, dots.size[0] - 1, dots.size[1] - 1],
                                 fill=255)
    im.paste(dots, (px * SS, py * SS), mask)
    ellipse(d, (px, py, px + size, py + size), outline=(120, 126, 140), width=4)

    text(d, (W / 2, H - 50), "Y、M、C、K 四色网点", font(17, True), fill=INK)
    text(d, (W / 2, H - 24), "重叠处减法混色，退远了又是并列混色", font(13),
         fill=MUTED)
    finish(im, os.path.join(out, "halftone-dots.png"))


# ==========================================================================
# 图 21  点彩画：整幅 + 局部放大
#
# 素材为公有领域画作的忠实复制品，非本脚本绘制：
#   Georges Seurat (1859-1891)《大碗岛的星期天下午》1884-1886
#   来源 Wikimedia Commons，File:A Sunday on La Grande Jatte, Georges
#   Seurat, 1884.jpg，许可 Public domain（作者逝世逾百年，著作权已过期）。
#   本脚本只做缩放与裁切，不改变画面内容。
# ==========================================================================
def fig_pointillism(out):
    src = os.path.join(out, "pointillism-source.jpg")
    if not os.path.exists(src):
        print("  !! 缺少 %s，跳过点彩画图" % src)
        return
    art = Image.open(src).convert("RGB")

    W, H = 1060, 580
    im, d = canvas(W, H)

    # 左：整幅
    fw = 580
    fh = int(art.height * fw / art.width)
    full = art.resize((fw * SS, fh * SS), Image.LANCZOS)
    fy = 74
    im.paste(full, (40 * SS, fy * SS))
    rect(d, (40, fy, 40 + fw, fy + fh), outline=(176, 182, 198), width=2)
    text(d, (40 + fw / 2, fy + fh + 30), "整幅：远看是连贯的景物与色调",
         font(16, True), fill=INK)

    # 右：局部放大
    # 裁切比例不能太小：源图只有 1280 px 宽，裁太小放大就糊了
    cw = 336
    side = int(art.width * 0.21)
    cx0 = int(art.width * 0.24)
    cy0 = int(art.height * 0.46)
    crop = art.crop((cx0, cy0, cx0 + side, cy0 + side))
    crop = crop.resize((cw * SS, cw * SS), Image.LANCZOS)
    gx = 676
    im.paste(crop, (gx * SS, fy * SS))
    rect(d, (gx, fy, gx + cw, fy + cw), outline=(176, 182, 198), width=2)
    text(d, (gx + cw / 2, fy + cw + 30), "放大：画面全由细小色点铺成",
         font(16, True), fill=INK)

    # 左图上标出取景框，并连到右图
    bx = 40 + fw * (cx0 / art.width)
    by = fy + fh * (cy0 / art.height)
    bw_ = fw * (side / art.width)
    bh_ = fh * (side / art.height)
    rect(d, (bx, by, bx + bw_, by + bh_), outline=(252, 252, 252), width=2)
    dashed(d, (bx + bw_, by), (gx, fy), fill=(196, 202, 216))
    dashed(d, (bx + bw_, by + bh_), (gx, fy + cw), fill=(196, 202, 216))

    text(d, (W / 2, 32),
         "乔治·修拉《大碗岛的星期天下午》（1884-1886）",
         font(18, True), fill=INK)
    text(d, (W / 2, H - 20),
         "图片来源：Wikimedia Commons，公有领域",
         font(14), fill=MUTED)
    finish(im, os.path.join(out, "pointillism-seurat.png"))


FIGURES = {
    "mixing-taxonomy": fig_taxonomy,
    "additive-rgb-projectors": fig_projectors,
    "additive-spectra": fig_additive_spectra,
    "subtractive-ymc-circles": fig_subtractive_circles,
    "ymc-filter-transmission": fig_filter_transmission,
    "subtractive-two-filters": fig_two_filters,
    "subtractive-stack": fig_subtractive_stack,
    "white-led-methods": fig_white_led,
    "white-led-spectra": fig_white_led_spectra,
    "film-layers": fig_film_layers,
    "film-sensitivity-vs-dye": fig_film_curves,
    "film-printing": fig_film_printing,
    "lemon-workflow": fig_lemon,
    "why-black-ink": fig_black_ink,
    "spinning-disc": fig_spinning_disc,
    "spinning-disc-results": fig_spinning_results,
    "cone-temporal-response": fig_cone_response,
    "juxtaposition-checker": fig_checker,
    "display-subpixels": fig_subpixels,
    "textile-weave": fig_textile,
    "halftone-dots": fig_halftone,
    "pointillism-seurat": fig_pointillism,
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="assets/resource/Color-Mixing")
    ap.add_argument("--only", action="append", default=None)
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)
    names = args.only or list(FIGURES)
    for n in names:
        if n not in FIGURES:
            raise SystemExit("unknown figure: %s" % n)
        FIGURES[n](args.out)


if __name__ == "__main__":
    main()
