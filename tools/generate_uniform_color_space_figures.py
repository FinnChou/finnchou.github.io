#!/usr/bin/env python3
"""生成《色差与均匀色空间》一文的插图。

依赖 Pillow 与 numpy；绘图工具与 CIE 1931 数据从同目录的
generate_cie_xyz_figures.py 导入。

用法：
    python3 tools/generate_uniform_color_space_figures.py            # 全部
    python3 tools/generate_uniform_color_space_figures.py --only macadam-xy

图里的数据：
    - xy 色度图、光谱轨迹：CIE 1931 2° 标准观察者（同前几篇）
    - MacAdam (1942) 颜色辨别椭圆：Wyszecki & Stiles《Color Science》第 2 版
      表 2(5.4.1)，25 个色中心（观察者 PGN），经 colour-science 内置数据表导出。
      表中半轴 a、b 的单位是 1e-3，图上按惯例放大 10 倍；取表中「Calculated」
      一组（对 MacAdam 观测数据拟合所得，colour-science 亦推荐用这一组）
    - uv、u'v' 色度图上的椭圆：把 xy 上的椭圆边界逐点经坐标变换得到
    - CIELAB 色环的颜色：由 L*a*b* 经 D65 白点换算到 sRGB，超出色域的分量裁剪，
      只作示意
    - 其余为模式图，不承载数据
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
    M_XYZ2RGB, _encode, cmf_at, spectral_locus, horseshoe, draw_chromaticity, _proj3,
    font, ifont, canvas, finish, text, rect, line, polyline, poly, ellipse, arc,
    arrow, dashed, callout, Axes,
)

# ==========================================================================
# MacAdam (1942) 颜色辨别椭圆，Wyszecki & Stiles (2000) 表 2(5.4.1)
# 列：x0 y0 | 观测 10^3·a 10^3·b θ | 拟合 10^3·a 10^3·b θ   （θ 为长轴与 x 轴夹角，度）
# ==========================================================================
MACADAM_1942 = """
0.160 0.057 0.85 0.35 62.5 0.94 0.3 62.3
0.187 0.118 2.2 0.55 77 2.31 0.44 74.8
0.253 0.125 2.5 0.5 55.5 2.49 0.49 54.8
0.150 0.680 9.6 2.3 105 9.09 2.21 102.9
0.131 0.521 4.7 2 112.5 4.67 2.1 110.5
0.212 0.550 5.8 2.3 100 5.63 2.3 100
0.258 0.450 5 2 92 4.54 2.08 88.5
0.152 0.365 3.8 1.9 110 3.81 1.86 111
0.280 0.385 4 1.5 75.5 4.26 1.46 74.6
0.380 0.498 4.4 1.2 70 4.23 1.32 69.4
0.160 0.200 2.1 0.95 104 2.08 0.94 95.4
0.228 0.250 3.1 0.9 72 3.09 0.82 70.9
0.305 0.323 2.3 0.9 58 2.55 0.68 57.2
0.385 0.393 3.8 1.6 65.5 3.7 1.48 65.5
0.472 0.399 3.2 1.4 51 3.21 1.3 54
0.527 0.350 2.6 1.3 20 2.56 1.27 22.8
0.475 0.300 2.9 1.1 28.5 2.89 0.99 29.1
0.510 0.236 2.4 1.2 29.5 2.4 1.15 30.7
0.596 0.283 2.6 1.3 13 2.49 1.15 11.1
0.344 0.284 2.3 0.9 60 2.24 0.97 65.7
0.390 0.237 2.5 1 47 2.43 0.98 44.2
0.441 0.198 2.8 0.95 34.5 2.73 0.9 33.7
0.278 0.223 2.4 0.55 57.5 2.34 0.61 60.3
0.300 0.163 2.9 0.6 54 3.01 0.6 53.4
0.365 0.153 3.6 0.95 40 4.12 0.9 38.6
"""

SCALE = 10.0     # 图上把椭圆放大 10 倍（惯例）


def macadam_ellipses():
    rows = [[float(v) for v in ln.split()] for ln in MACADAM_1942.strip().splitlines()]
    assert len(rows) == 25
    out = []
    for x0, y0, _a, _b, _t, a, b, t in rows:
        out.append((x0, y0, a * 1e-3, b * 1e-3, math.radians(t)))
    return out


def ellipse_points(x0, y0, a, b, th, n=90, scale=SCALE):
    pts = []
    for k in range(n):
        t = 2 * math.pi * k / n
        dx, dy = a * scale * math.cos(t), b * scale * math.sin(t)
        pts.append((x0 + dx * math.cos(th) - dy * math.sin(th),
                    y0 + dx * math.sin(th) + dy * math.cos(th)))
    return pts


def ellipse_axes(x0, y0, a, b, th, scale=SCALE):
    """长轴、短轴两条线段的端点。"""
    ca, sa = math.cos(th), math.sin(th)
    A = ((x0 - a * scale * ca, y0 - a * scale * sa), (x0 + a * scale * ca, y0 + a * scale * sa))
    B = ((x0 + b * scale * sa, y0 - b * scale * ca), (x0 - b * scale * sa, y0 + b * scale * ca))
    return A, B


# ---------------------------------------------------------------- 坐标变换
def xy_to_uv(x, y):
    den = -2 * x + 12 * y + 3
    return 4 * x / den, 6 * y / den


def xy_to_upvp(x, y):
    u, v = xy_to_uv(x, y)
    return u, 1.5 * v


def uv_to_xy(u, v):
    den = 2 * u - 8 * v + 4
    return 3 * u / den, 2 * v / den


def upvp_to_xy(up, vp):
    return uv_to_xy(up, vp / 1.5)


def diagram_image(w, h, ir, jr, ij_to_xy, locus_ij):
    """任意色度图的填色位图：像素 -> (i, j) -> (x, y) -> 最亮的 sRGB 显示色。"""
    mask = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mask).polygon(
        [((i - ir[0]) / (ir[1] - ir[0]) * w, h - (j - jr[0]) / (jr[1] - jr[0]) * h) for i, j in locus_ij], fill=255)
    m = np.array(mask) > 0
    iv = ir[0] + (np.arange(w) + 0.5) / w * (ir[1] - ir[0])
    jv = jr[1] - (np.arange(h) + 0.5) / h * (jr[1] - jr[0])
    I, J = np.meshgrid(iv, jv)
    x, y = ij_to_xy(I, J)
    y = np.maximum(y, 1e-4)
    xyz = np.stack([x / y, np.ones_like(x), (1 - x - y) / y], axis=-1)
    rgb = xyz @ M_XYZ2RGB.T
    rgb = rgb - np.minimum(0.0, rgb.min(axis=-1, keepdims=True))
    rgb = rgb / rgb.max(axis=-1, keepdims=True)
    out = np.zeros((h, w, 4), dtype=np.uint8)
    out[..., :3] = (_encode(np.clip(rgb, 0, 1)) * 255 + 0.5).astype(np.uint8)
    out[..., 3] = np.where(m, 255, 0)
    return Image.fromarray(out, "RGBA")


def lighten(im, box, alpha=110):
    """在 box 内蒙一层半透明白，让底色退后、线条突出。"""
    x0, y0, x1, y1 = [int(v * SS) for v in box]
    lay = Image.new("RGBA", (x1 - x0, y1 - y0), (255, 255, 255, alpha))
    im.paste(lay, (x0, y0), lay)


def draw_ellipses(d, ax, to_ij=None, col=INK, width=1.3):
    for e in macadam_ellipses():
        pts = ellipse_points(*e)
        if to_ij:
            pts = [to_ij(x, y) for x, y in pts]
        pp = [ax.px(*p) for p in pts]
        polyline(d, pp + [pp[0]], fill=col, width=width)
        for seg in ellipse_axes(*e):
            s = [to_ij(*p) for p in seg] if to_ij else list(seg)
            p0, p1 = ax.px(*s[0]), ax.px(*s[1])
            line(d, (p0[0], p0[1], p1[0], p1[1]), fill=col, width=1.1)


# ==========================================================================
# 图 1：xy 色度图上的 MacAdam 椭圆
# ==========================================================================

def fig_macadam_xy(out):
    W, H = 900, 800
    im, d = canvas(W, H)
    box = (80, 40, 720, 760)
    ax = draw_chromaticity(d, im, box)
    lighten(im, box, 120)
    locus = spectral_locus(1)
    pts = [ax.px(x, y) for _, x, y in locus]
    polyline(d, pts + [pts[0]], fill=INK, width=1.4)
    draw_ellipses(d, ax)
    text(d, ((box[0] + box[2]) / 2, 786), "x", ifont(18))
    text(d, (30, 40), "y", ifont(18))
    f = font(13)
    fs = font(12)
    callout(d, (430, 120, 715, 176), "绿色区域：椭圆很大，两点离得\n这么远仍分辨不出色差", fs, tail=ax.px(0.212, 0.55))
    callout(d, (480, 668, 715, 724), "蓝～蓝紫区域：椭圆很小，\n离开一点点就能分辨", fs, tail=ax.px(0.160, 0.057))
    text(d, (W / 2 - 40, 24), "MacAdam 的颜色辨别椭圆（25 个色中心，椭圆已放大 10 倍）", f)
    finish(im, os.path.join(out, "macadam-xy.png"))


# ==========================================================================
# 图 2：一个椭圆与基准色 A、比较色 B1、B2（模式图）
# ==========================================================================

def fig_ellipse_ab(out):
    W, H = 720, 420
    im, d = canvas(W, H)
    f = font(13)
    fb = font(14, bold=True)
    fi = ifont(18)
    # 坐标轴
    o = (90, 350)
    arrow(d, (o[0], o[1]), (o[0] + 300, o[1]), fill=INK, width=1.4, head=8)
    arrow(d, (o[0], o[1]), (o[0], o[1] - 300), fill=INK, width=1.4, head=8)
    text(d, (o[0] + 312, o[1]), "x", fi)
    text(d, (o[0], o[1] - 312), "y", fi)
    # 椭圆：中心 A，长轴倾斜
    cx, cy, a, b, th = 240, 150, 95, 40, math.radians(-60)
    pts = []
    for k in range(120):
        t = 2 * math.pi * k / 120
        dx, dy = a * math.cos(t), b * math.sin(t)
        pts.append((cx + dx * math.cos(th) - dy * math.sin(th), cy + dx * math.sin(th) + dy * math.cos(th)))
    poly(d, pts, fill=(238, 240, 250), outline=INK, width=1.6)
    for L, ang in ((a, th), (b, th + math.pi / 2)):
        line(d, (cx - L * math.cos(ang), cy - L * math.sin(ang), cx + L * math.cos(ang), cy + L * math.sin(ang)),
             fill=MUTED, width=1.2)
    # B1 在远处，B2 在椭圆边界上（沿同一方向）
    ang = math.radians(35)
    # 求该方向与椭圆边界的交点
    best = min(pts, key=lambda p: abs(math.atan2(p[1] - cy, p[0] - cx) - ang))
    b2 = best
    b1 = (cx + 240 * math.cos(ang), cy + 240 * math.sin(ang))
    line(d, (cx, cy, b1[0], b1[1]), fill=ACCENT, width=2)
    for p, col, lab in ((b1, (120, 180, 90), "B1 (x1, y1)"), (b2, (60, 160, 70), "B2 (x2, y2)"), ((cx, cy), CURVE, "A (xA, yA)")):
        ellipse(d, (p[0] - 5, p[1] - 5, p[0] + 5, p[1] + 5), fill=col, outline=WHITE, width=1)
    callout(d, (360, 90, 520, 120), "A (xA, yA)", fb, text_fill=CURVE, tail=(cx, cy))
    callout(d, (470, 160, 640, 190), "B2 (x2, y2)", fb, text_fill=(60, 160, 70), tail=b2)
    callout(d, (530, 300, 700, 330), "B1 (x1, y1)", fb, text_fill=(120, 180, 90), tail=b1)
    text(d, (cx - 120, cy - 100), "椭圆内：与 A 分辨不出色差", f, anchor="lm")
    text(d, (cx - 120, cy - 80), "椭圆外：能分辨出色差", f, anchor="lm")
    text(d, (W / 2, 400), "B 由 B1 向 A 靠近，越过椭圆边界（B2）后就再也分辨不出与 A 的差别（模式图）", font(12), fill=MUTED)
    finish(im, os.path.join(out, "ellipse-ab.png"))


# ==========================================================================
# 图 3 / 4：uv 与 u'v' 色度图上的 MacAdam 椭圆
# ==========================================================================

def _uv_diagram(out, name, prime):
    to_ij = xy_to_upvp if prime else xy_to_uv
    ij_to_xy = upvp_to_xy if prime else uv_to_xy
    ir = (0.0, 0.65)
    jr = (0.0, 0.65) if prime else (0.0, 0.45)
    W = 900
    H = 800 if prime else 620
    im, d = canvas(W, H)
    box = (80, 40, 720, H - 40)
    ax = Axes(d, box, ir, jr)
    fx = font(13)
    xt = [i / 10 for i in range(7)]
    yt = [i / 10 for i in range(7 if prime else 5)]
    ax.frame(xt, yt, fx, xfmt="%.1f", yfmt="%.1f")
    locus = spectral_locus(1)
    loc_ij = [to_ij(x, y) for _, x, y in locus]
    w, h = int((box[2] - box[0]) * SS), int((box[3] - box[1]) * SS)
    img = diagram_image(w, h, ir, jr, ij_to_xy, loc_ij)
    im.paste(img, (int(box[0] * SS), int(box[1] * SS)), img)
    lighten(im, box, 120)
    ax.grid(xt, yt)
    pts = [ax.px(*p) for p in loc_ij]
    polyline(d, pts + [pts[0]], fill=INK, width=1.4)
    # 波长刻度
    ft = font(12)
    ci, cj = to_ij(1 / 3, 1 / 3)
    ccx, ccy = ax.px(ci, cj)
    for wl in (380, 450, 470, 480, 490, 500, 510, 520, 540, 560, 580, 600, 620, 700):
        X, Yv, Z = cmf_at(wl)
        s = X + Yv + Z
        i, j = to_ij(X / s, Yv / s)
        px, py = ax.px(i, j)
        ellipse(d, (px - 2.5, py - 2.5, px + 2.5, py + 2.5), fill=INK)
        ang = math.atan2(py - ccy, px - ccx)
        text(d, (px + 17 * math.cos(ang), py + 17 * math.sin(ang)), str(wl), ft, fill=INK)
    draw_ellipses(d, ax, to_ij=to_ij)
    fi = ifont(18)
    text(d, ((box[0] + box[2]) / 2, H - 14), "u'" if prime else "u", fi)
    text(d, (30, 40), "v'" if prime else "v", fi)
    if prime:
        text(d, (W / 2 - 40, 24), "CIE 1976 u'v' 色度图上的 MacAdam 椭圆（放大 10 倍）", fx)
        callout(d, (440, 640, 715, 700), "v' = 1.5 v：纵向拉伸后\n椭圆进一步接近圆、大小更接近", font(12))
    else:
        text(d, (W / 2 - 40, 24), "CIE 1960 UCS（uv 色度图）上的 MacAdam 椭圆（放大 10 倍）", fx)
        callout(d, (440, 470, 715, 530), "与 xy 色度图相比，各椭圆的\n大小差异明显缩小，但仍不是等大的圆", font(12))
    finish(im, os.path.join(out, name))


def fig_macadam_uv(out):
    _uv_diagram(out, "macadam-uv.png", prime=False)


def fig_macadam_upvp(out):
    _uv_diagram(out, "macadam-upvp.png", prime=True)


# ==========================================================================
# 图 5：CIELAB 色空间：L* 轴与 a*b* 平面（示意）
# ==========================================================================

D65_WHITE = (0.95047, 1.0, 1.08883)


def lab_to_srgb8(L, a, b):
    """L*a*b*（D65）-> sRGB 8 bit，向量化；超出色域的分量直接裁剪。"""
    fy = (L + 16) / 116
    fx = fy + a / 500
    fz = fy - b / 200
    d = 6 / 29

    def finv(t):
        return np.where(t > d, t ** 3, 3 * d * d * (t - 4 / 29))
    X = D65_WHITE[0] * finv(fx)
    Y = D65_WHITE[1] * finv(fy)
    Z = D65_WHITE[2] * finv(fz)
    xyz = np.stack([X, Y, Z], axis=-1)
    rgb = np.clip(xyz @ M_XYZ2RGB.T, 0, 1)
    return (_encode(rgb) * 255 + 0.5).astype(np.uint8)


def fig_cielab_space(out):
    W, H = 1000, 560
    im, d = canvas(W, H)
    f = font(13)
    fb = font(14, bold=True)
    fs = font(12)
    fi = ifont(18)

    # 左：球面示意，自转轴 = L*，赤道面 = a*b*
    cx, cy, R = 280, 290, 150
    lay = Image.new("RGBA", im.size, (0, 0, 0, 0))
    ld = ImageDraw.Draw(lay)
    # 球体明暗：上白下黑的竖直渐变，限制在圆内
    n = int(2 * R * SS)
    grad = np.linspace(235, 25, n).astype(np.uint8)
    tile = np.zeros((n, n, 4), dtype=np.uint8)
    tile[..., 0] = grad[:, None]
    tile[..., 1] = grad[:, None]
    tile[..., 2] = grad[:, None]
    yy, xx = np.mgrid[0:n, 0:n]
    inside = (xx - n / 2) ** 2 + (yy - n / 2) ** 2 <= (n / 2) ** 2
    tile[..., 3] = np.where(inside, 255, 0)
    sphere = Image.fromarray(tile, "RGBA")
    im.paste(sphere, (int((cx - R) * SS), int((cy - R) * SS)), sphere)
    ellipse(d, (cx - R, cy - R, cx + R, cy + R), outline=INK, width=1.4)
    # 赤道（椭圆）与几条纬线
    for k, ry in ((0, 0.28), (0.5, 0.2), (-0.5, 0.2), (0.8, 0.1), (-0.8, 0.1)):
        rx = math.sqrt(max(0.0, 1 - k * k)) * R
        yc = cy - k * R
        ellipse(d, (cx - rx, yc - rx * ry, cx + rx, yc + rx * ry), outline=(255, 255, 255) if k < 0 else (90, 90, 110), width=1.2 if k else 1.8)
    # L* 轴
    arrow(d, (cx, cy + R + 10), (cx, cy - R - 30), fill=INK, width=2.4, head=10)
    text(d, (cx + 14, cy - R - 26), "L*", fi, anchor="lm")
    callout(d, (cx - 42, cy - R - 70, cx + 42, cy - R - 44), "100 = 白", fs)
    callout(d, (cx - 42, cy + R + 16, cx + 42, cy + R + 42), "0 = 黑", fs)
    # a*、b* 轴（赤道面内，斜投影）
    arrow(d, (cx, cy), (cx + R + 40, cy), fill=RED, width=2.4, head=10)
    arrow(d, (cx, cy), (cx - R - 40, cy), fill=GREEN, width=2.4, head=10)
    arrow(d, (cx, cy), (cx + 70, cy - 60), fill=(220, 180, 40), width=2.4, head=10)
    arrow(d, (cx, cy), (cx - 70, cy + 60), fill=BLUE, width=2.4, head=10)
    text(d, (cx + R + 44, cy - 16), "+a* 红", fb, fill=RED, anchor="rm")
    text(d, (cx - R - 44, cy - 16), "绿 －a*", fb, fill=GREEN, anchor="lm")
    text(d, (cx + 80, cy - 70), "+b* 黄", fb, fill=(200, 160, 30), anchor="lm")
    text(d, (cx - 80, cy + 72), "蓝 －b*", fb, fill=BLUE, anchor="rm")
    text(d, (cx, cy + R + 66), "把它比作地球仪：自转轴是明度轴 L*，", fs, fill=MUTED)
    text(d, (cx, cy + R + 84), "经度方向是色相，赤道面就是 a*b* 平面", fs, fill=MUTED)

    # 右：a*b* 平面（L* = 70 的一个切面）
    cx2, cy2, R2 = 730, 280, 165
    n = int(2 * R2 * SS)
    yy, xx = np.mgrid[0:n, 0:n]
    a = (xx - n / 2) / (n / 2) * 90
    b = -(yy - n / 2) / (n / 2) * 90
    rgb = lab_to_srgb8(np.full_like(a, 70.0), a, b)
    disc = np.zeros((n, n, 4), dtype=np.uint8)
    disc[..., :3] = rgb
    disc[..., 3] = np.where(a * a + b * b <= 90 * 90, 255, 0)
    disc_im = Image.fromarray(disc, "RGBA")
    im.paste(disc_im, (int((cx2 - R2) * SS), int((cy2 - R2) * SS)), disc_im)
    ellipse(d, (cx2 - R2, cy2 - R2, cx2 + R2, cy2 + R2), outline=INK, width=1.2)
    for r in (30, 60):
        rr = r / 90 * R2
        ellipse(d, (cx2 - rr, cy2 - rr, cx2 + rr, cy2 + rr), outline=(255, 255, 255), width=1.1)
    arrow(d, (cx2 - R2 - 30, cy2), (cx2 + R2 + 30, cy2), fill=INK, width=1.6, head=9)
    arrow(d, (cx2, cy2 + R2 + 30), (cx2, cy2 - R2 - 30), fill=INK, width=1.6, head=9)
    text(d, (cx2 + R2 + 42, cy2), "a*", fi, anchor="lm")
    text(d, (cx2, cy2 - R2 - 44), "b*", fi)
    text(d, (cx2 + R2 - 10, cy2 + 16), "+：红", fs, fill=INK, anchor="rt")
    text(d, (cx2 - R2 + 10, cy2 + 16), "－：绿", fs, fill=INK, anchor="lt")
    text(d, (cx2 + 12, cy2 - R2 + 8), "+：黄", fs, fill=INK, anchor="lt")
    text(d, (cx2 + 12, cy2 + R2 - 8), "－：蓝", fs, fill=INK, anchor="lb")
    # 色相（绕圈）与彩度（向外）
    arc(d, (cx2 - R2 - 14, cy2 - R2 - 14, cx2 + R2 + 14, cy2 + R2 + 14), 200, 250, fill=INK, width=1.6)
    ang = math.radians(250)
    tip = (cx2 + (R2 + 14) * math.cos(ang), cy2 + (R2 + 14) * math.sin(ang))
    arrow(d, (tip[0] - 6 * math.sin(ang), tip[1] + 6 * math.cos(ang)), tip, fill=INK, width=1.6, head=9)
    text(d, (cx2 - R2 - 4, cy2 - R2 + 6), "色相", fs, anchor="rm")
    ang = math.radians(-40)
    arrow(d, (cx2 + 20 * math.cos(ang), cy2 + 20 * math.sin(ang)), (cx2 + (R2 - 8) * math.cos(ang), cy2 + (R2 - 8) * math.sin(ang)), fill=WHITE, width=2.2, head=10)
    text(d, (cx2 + 138, cy2 - 128), "彩度", fs, anchor="lm")
    text(d, (cx2, cy2 + R2 + 48), "a*b* 平面：L* = 70 的切面，离原点越远彩度越高", fs, fill=MUTED)
    text(d, (cx2, cy2 + R2 + 66), "（颜色按 D65 换算为 sRGB，超出显示色域的部分已裁剪，只作示意）", fs, fill=MUTED)
    text(d, (W / 2, 22), "CIELAB：L* 为明度，a*、b* 按红－绿、黄－蓝两对补色配置（模式图）", f)
    finish(im, os.path.join(out, "cielab-space.png"))


# ==========================================================================
# 图 6：色差 ΔE*ab 是色空间里两点的直线距离（模式图）
# ==========================================================================

def fig_delta_e(out):
    W, H = 900, 600
    im, d = canvas(W, H)
    f = font(13)
    fb = font(14, bold=True)
    fs = font(12)
    fi = ifont(18)
    o = (330, 470)
    P3 = dict(sx=300, sy=260, sz=(-130, 115))

    def pj(v):
        return _proj3(v[0], v[1], v[2], o, **P3)

    # 轴：x -> a*，y -> L*，z -> b*
    for vec, lab, off in (((1.45, 0, 0), "a*", (16, 0)), ((0, 1.25, 0), "L*", (0, -16)), ((0, 0, 0.8), "b*", (-16, 8))):
        arrow(d, pj((-0.2 if lab == "a*" else 0, 0, -0.2 if lab == "b*" else 0)), pj(vec), fill=INK, width=1.6, head=9)
        p = pj(vec)
        text(d, (p[0] + off[0], p[1] + off[1]), lab, fi)
    text(d, (pj((0, 1.35, 0))[0] + 40, pj((0, 1.35, 0))[1] - 2), "白 (100)", fs, fill=MUTED, anchor="lm")
    text(d, (o[0] + 10, o[1] + 16), "黑 (0)", fs, fill=MUTED, anchor="lm")
    P = np.array([0.3, 0.3, 0.25])
    Q = np.array([1.1, 1.0, 0.9])
    # 长方体的三条棱：ΔL*、Δa*、Δb*
    c1 = np.array([Q[0], P[1], P[2]])       # 先沿 a*
    c2 = np.array([Q[0], P[1], Q[2]])       # 再沿 b*
    for a_, b_, col, lab, off in ((P, c1, RED, "Δa*", (0, 20)), (c1, c2, BLUE, "Δb*", (38, -14)), (c2, Q, (110, 110, 130), "ΔL*", (32, 0))):
        pa, pb = pj(a_), pj(b_)
        dashed(d, pa, pb, fill=col, width=2.4, dash=8, gap=5)
        mid = ((pa[0] + pb[0]) / 2 + off[0], (pa[1] + pb[1]) / 2 + off[1])
        text(d, mid, lab, fb, fill=col)
    # 其余棱（淡）
    for a_, b_ in ((P, np.array([P[0], P[1], Q[2]])), (np.array([P[0], P[1], Q[2]]), c2),
                   (P, np.array([P[0], Q[1], P[2]])), (np.array([P[0], Q[1], P[2]]), np.array([Q[0], Q[1], P[2]])),
                   (np.array([Q[0], Q[1], P[2]]), Q), (c1, np.array([Q[0], Q[1], P[2]])),
                   (np.array([P[0], Q[1], P[2]]), np.array([P[0], Q[1], Q[2]])), (np.array([P[0], Q[1], Q[2]]), Q),
                   (np.array([P[0], P[1], Q[2]]), np.array([P[0], Q[1], Q[2]]))):
        pa, pb = pj(a_), pj(b_)
        line(d, (pa[0], pa[1], pb[0], pb[1]), fill=(175, 180, 200), width=1.3)
    # ΔE：P 到 Q 的直线
    pp, pq = pj(P), pj(Q)
    line(d, (pp[0], pp[1], pq[0], pq[1]), fill=ACCENT, width=3.5)
    text(d, ((pp[0] + pq[0]) / 2 - 40, (pp[1] + pq[1]) / 2 - 22), "ΔE*ab", font(16, bold=True), fill=ACCENT)
    for p, col, lab, off, anc in ((pp, CURVE, "P", (-14, 0), "rm"), (pq, ACCENT, "Q", (12, -12), "lm")):
        ellipse(d, (p[0] - 7, p[1] - 7, p[0] + 7, p[1] + 7), fill=col, outline=WHITE, width=1.5)
        text(d, (p[0] + off[0], p[1] + off[1]), lab, font(16, bold=True), fill=col, anchor=anc)
    callout(d, (560, 60, 870, 92), "P：基准色 (L*P, a*P, b*P)", fs, text_fill=CURVE)
    callout(d, (560, 104, 870, 136), "Q：试料色 (L*Q, a*Q, b*Q)", fs, text_fill=ACCENT)
    callout(d, (560, 160, 870, 224), "以 ΔL*、Δa*、Δb* 为棱的长方体，\n其对角线的长度就是色差 ΔE*ab（公式见正文）", fs)
    text(d, (W / 2, 22), "色差 ΔE*ab：CIELAB 色空间里 P、Q 两点的直线距离（模式图）", f)
    finish(im, os.path.join(out, "delta-e.png"))


# ==========================================================================
# 图 7：注释 1 —— xy 色度图上加法混色的内分点
# ==========================================================================

def fig_mixing_division(out):
    W, H = 900, 800
    im, d = canvas(W, H)
    box = (80, 40, 720, 760)
    ax = draw_chromaticity(d, im, box)
    text(d, ((box[0] + box[2]) / 2, 786), "x", ifont(18))
    text(d, (30, 40), "y", ifont(18))
    f = font(13)
    fb = font(14, bold=True)
    fs = font(12)
    A = (0.26, 0.56)
    B = (0.50, 0.32)
    a_, b_ = 2.0, 1.0                    # A 与 B 的刺激值总量之比 a : b
    C = ((a_ * A[0] + b_ * B[0]) / (a_ + b_), (a_ * A[1] + b_ * B[1]) / (a_ + b_))
    pa, pb, pc = ax.px(*A), ax.px(*B), ax.px(*C)
    line(d, (pa[0], pa[1], pb[0], pb[1]), fill=INK, width=2)
    for p, lab, off in ((pa, "A (xA, yA)", (-12, -4)), (pb, "B (xB, yB)", (14, 4)), (pc, "C (xC, yC)", (14, -6))):
        ellipse(d, (p[0] - 6, p[1] - 6, p[0] + 6, p[1] + 6), fill=WHITE, outline=INK, width=2)
        text(d, (p[0] + off[0], p[1] + off[1]), lab, fb, anchor="rb" if lab.startswith("A") else "lb")
    # 线段 AC、CB 的长度标注：|AC| : |CB| = b : a
    mid1 = ((pa[0] + pc[0]) / 2, (pa[1] + pc[1]) / 2)
    mid2 = ((pc[0] + pb[0]) / 2, (pc[1] + pb[1]) / 2)
    text(d, (mid1[0] - 16, mid1[1] + 14), "b", ifont(18), fill=ACCENT)
    text(d, (mid2[0] - 16, mid2[1] + 14), "a", ifont(18), fill=ACCENT)
    callout(d, (400, 90, 715, 160), "A、B 以刺激值总量 a : b 混合，\n结果 C 落在线段 AB 上，\n且 AC : CB = b : a（靠近量多的一方）", fs, tail=pc)
    text(d, (W / 2 - 40, 24), "xy 色度图是线性空间：混色结果是两点连线上的内分点", f)
    finish(im, os.path.join(out, "mixing-division.png"))


FIGURES = {
    "macadam-xy": fig_macadam_xy,
    "ellipse-ab": fig_ellipse_ab,
    "macadam-uv": fig_macadam_uv,
    "macadam-upvp": fig_macadam_upvp,
    "cielab-space": fig_cielab_space,
    "delta-e": fig_delta_e,
    "mixing-division": fig_mixing_division,
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", nargs="*", help="只生成这些图")
    ap.add_argument("--out", default="assets/resource/Uniform-Color-Space")
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)
    for n in (args.only or list(FIGURES)):
        FIGURES[n](args.out)


if __name__ == "__main__":
    main()
