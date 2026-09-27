#!/usr/bin/env python3
"""生成《三原色能表示的颜色》一文的插图。

依赖 Pillow 与 numpy；绘图工具与 CIE 1931 数据从同目录的
generate_cie_xyz_figures.py 导入。

用法：
    python3 tools/generate_three_primaries_figures.py            # 全部
    python3 tools/generate_three_primaries_figures.py --only gamut linearity

图里的数据：
    - xy 色度图、光谱轨迹：CIE 1931 2° 标准观察者（同前几篇）
    - 实线三角形的三原色：ITU-R BT.709 / sRGB 的原色色度
          R (0.640, 0.330)  G (0.300, 0.600)  B (0.150, 0.060)
    - 虚线三角形的三原色：CIE RGB 表色系的单色光原刺激
          700.0 / 546.1 / 435.8 nm，色度由 CIE 1931 等色函数算出
    - 线性示意图与混色向量图为模式图，不承载数据
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
    cmf_at, spectral_locus, horseshoe, draw_chromaticity, _proj3,
    font, ifont, canvas, finish, text, rect, line, polyline, poly, ellipse,
    arrow, dashed, callout, Axes,
)

# ITU-R BT.709（sRGB）三原色的色度坐标
SRGB_PRIMARIES = {"R": (0.640, 0.330), "G": (0.300, 0.600), "B": (0.150, 0.060)}
# CIE RGB 表色系的单色光原刺激（nm）
MONO_PRIMARIES = {"R": 700.0, "G": 546.1, "B": 435.8}
COLS = {"R": RED, "G": GREEN, "B": BLUE}


def mono_xy(wl):
    X, Y, Z = cmf_at(wl)
    s = X + Y + Z
    return X / s, Y / s


# ==========================================================================
# 图 1：三原色围成的色域（xy 色度图上的 △RGB）
# ==========================================================================

def fig_gamut(out):
    W, H = 900, 800
    im, d = canvas(W, H)
    box = (80, 40, 720, 760)
    ax = draw_chromaticity(d, im, box)
    text(d, ((box[0] + box[2]) / 2, 786), "x", ifont(18))
    text(d, (30, 40), "y", ifont(18))
    f = font(13)
    fb = font(15, bold=True)
    fs = font(12)

    tri = [ax.px(*SRGB_PRIMARIES[k]) for k in "RGB"]
    # 三角形以外、马蹄形以内的区域蒙一层半透明白，表示「做不出来」
    x0, y0, x1, y1 = box
    w, h = int((x1 - x0) * SS), int((y1 - y0) * SS)
    inside = np.array(horseshoe(w, h, 0.8, 0.9).getchannel("A")) > 0
    tmask = Image.new("L", (w, h), 0)
    ImageDraw.Draw(tmask).polygon([((px - x0) * SS, (py - y0) * SS) for px, py in tri], fill=255)
    tri_in = np.array(tmask) > 0
    layer = np.zeros((h, w, 4), dtype=np.uint8)
    layer[..., :3] = 255
    layer[..., 3] = np.where(inside & ~tri_in, 165, 0)
    im.paste(Image.fromarray(layer, "RGBA"), (int(x0 * SS), int(y0 * SS)), Image.fromarray(layer, "RGBA"))
    # 光谱轨迹在蒙层之上再描一遍
    locus = spectral_locus(1)
    pts = [ax.px(x, y) for _, x, y in locus]
    polyline(d, pts + [pts[0]], fill=INK, width=1.6)

    # 单色光原刺激的三角形（虚线）
    mono = [ax.px(*mono_xy(MONO_PRIMARIES[k])) for k in "RGB"]
    for k in range(3):
        dashed(d, mono[k], mono[(k + 1) % 3], fill=(120, 60, 140), width=1.6, dash=8, gap=5)
    # 实际三原色的三角形（实线）
    poly(d, tri, outline=INK, width=2.2)
    for k, p in zip("RGB", tri):
        rect(d, (p[0] - 5, p[1] - 5, p[0] + 5, p[1] + 5), fill=COLS[k])
    for k, p in zip("RGB", mono):
        ellipse(d, (p[0] - 4, p[1] - 4, p[0] + 4, p[1] + 4), fill=(120, 60, 140))
    # 标注
    for k, off in (("R", (10, 24)), ("G", (-4, -26)), ("B", (28, 14))):
        px, py = tri["RGB".index(k)]
        text(d, (px + off[0], py + off[1]), "[%s]" % k, fb, fill=COLS[k])
    # 三角形之外的一个点：520 nm 的单色光
    fx_, fy_ = ax.px(*mono_xy(505))
    ellipse(d, (fx_ - 5, fy_ - 5, fx_ + 5, fy_ + 5), fill=ACCENT)
    callout(d, (96, 296, 318, 346), "505 nm 的单色光在 △RGB 之外，\n三原色混不出来", fs,
            tail=(fx_, fy_))
    callout(d, (430, 560, 720, 630), "实线：sRGB (BT.709) 的三原色\n虚线：700 / 546.1 / 435.8 nm 的单色光\n光谱轨迹向外凸，两种都留有空白", fs,
            fill=(246, 246, 250), outline=BORDER)
    text(d, (W / 2 - 40, 26), "三原色的加法混色只能做出 △RGB 内部的颜色（外部已淡化）", f)
    finish(im, os.path.join(out, "xy-rgb-gamut.png"))


# ==========================================================================
# 图 2：什么是「线性」（模式图）
# ==========================================================================

def _mini_axes(d, o, w, h, xl, yl, fi, nx=60, ny=50):
    """一对坐标轴；nx、ny 为负半轴的长度。"""
    ox, oy = o
    arrow(d, (ox - nx, oy), (ox + w, oy), fill=INK, width=1.4, head=8)
    arrow(d, (ox, oy + ny), (ox, oy - h), fill=INK, width=1.4, head=8)
    text(d, (ox + w + 12, oy), xl, fi)
    text(d, (ox - 4, oy - h - 12), yl, fi)


def fig_linearity(out):
    W, H = 1000, 520
    im, d = canvas(W, H)
    f = font(13)
    fb = font(14, bold=True)
    fi = ifont(18)
    fs = font(12)
    A = 0.55

    # 左：y = A x
    o = (130, 290)
    rect(d, (40, 120, 330, 470), fill=PANEL, outline=BORDER, radius=10)
    _mini_axes(d, o, 170, 110, "x", "y", fi, nx=70, ny=70)
    xs = np.linspace(-80, 160, 2)
    polyline(d, [(o[0] + x, o[1] - A * x) for x in xs], fill=CURVE, width=2.4)
    text(d, (o[0] + 110, o[1] - A * 110 - 22), "y = A·x", fb, fill=CURVE)
    text(d, (185, 138), "正比例：过原点的直线", f)

    # 右上：y' = B y + C = AB x + C  （线性变换，仍是直线）
    o = (660, 200)
    rect(d, (560, 30, 960, 250), fill=PANEL, outline=BORDER, radius=10)
    _mini_axes(d, o, 250, 115, "x", "y'", fi, nx=85, ny=40)
    B, C = 0.8, 45
    xs = np.linspace(-80, 230, 2)
    polyline(d, [(o[0] + x, o[1] - (A * B * x + C)) for x in xs], fill=GREEN, width=2.4)
    dashed(d, (o[0] - 60, o[1] - A * B * (-60)), (o[0] + 200, o[1] - A * B * 200), fill=MUTED, width=1.2)
    ellipse(d, (o[0] - 4, o[1] - C - 4, o[0] + 4, o[1] - C + 4), fill=GREEN)
    text(d, (o[0] + 14, o[1] - C - 2), "C", fi, fill=GREEN, anchor="lm")
    text(d, (o[0] + 150, o[1] - A * B * 150 + 24), "y' = AB·x + C", fb, fill=GREEN)
    text(d, (760, 44), "线性变换：斜率、截距变了，仍是直线", f)

    # 右下：y'' = x·y = A x²  （非线性变换，直线变成抛物线）
    o = (760, 440)
    rect(d, (560, 280, 960, 500), fill=PANEL, outline=BORDER, radius=10)
    _mini_axes(d, o, 160, 110, "x", "y''", fi, nx=180, ny=45)
    xs = np.linspace(-150, 150, 60)
    polyline(d, [(o[0] + x, o[1] - 0.0052 * x * x) for x in xs], fill=ACCENT, width=2.4)
    lbl = "y'' = x·y = A·x"
    text(d, (o[0] + 20, o[1] + 30), lbl, fb, fill=ACCENT, anchor="lm")
    text(d, (o[0] + 20 + fb.getlength(lbl) / SS + 1, o[1] + 20), "2", font(10, bold=True), fill=ACCENT, anchor="lm")   # 上标 2
    text(d, (760, 294), "非线性变换：直线变成了抛物线", f)

    # 箭头
    arrow(d, (340, 250), (550, 130), fill=CURVE, width=6, head=16)
    text(d, (420, 165), "y' = B·y + C", fs, fill=CURVE)
    text(d, (420, 183), "（一次式）", fs, fill=CURVE)
    arrow(d, (340, 330), (550, 400), fill=ACCENT, width=6, head=16)
    text(d, (420, 392), "y'' = x·y", fs, fill=ACCENT)
    text(d, (420, 410), "（二次式）", fs, fill=ACCENT)
    text(d, (W / 2, 20), "「线性」：用一次式变换，直线仍是直线（模式图）", f)
    finish(im, os.path.join(out, "linearity.png"))


# ==========================================================================
# 图 3：两色混合的向量关系与色度点（模式图）
# ==========================================================================

def fig_mixing_vectors(out):
    W, H = 1000, 740
    im, d = canvas(W, H)
    f = font(13)
    fb = font(14, bold=True)
    fs = font(12)
    fi = ifont(18)
    o = (330, 520)
    P = dict(sx=300, sy=250, sz=(-140, 150))

    def pj(v):
        return _proj3(v[0], v[1], v[2], o, **P)

    F1 = np.array([0.95, 0.25, 0.12])
    F2 = np.array([0.35, 0.75, 0.25])
    FM = F1 + F2
    alpha = 1.6
    F2a = alpha * F2
    FMa = F1 + F2a

    def chrom(v):
        return v / v.sum()

    # 坐标轴
    for vec, lab, off in (((1.4, 0, 0), "R", (14, 0)), ((0, 1.65, 0), "G", (0, -14)), ((0, 0, 1.1), "B", (-14, 8))):
        arrow(d, pj((0, 0, 0)), pj(vec), fill=INK, width=1.6, head=9)
        p = pj(vec)
        text(d, (p[0] + off[0], p[1] + off[1]), lab, fi)
    # 平面 R + G + B = 1
    tri = [pj((1, 0, 0)), pj((0, 1, 0)), pj((0, 0, 1))]
    lay = Image.new("RGBA", im.size, (0, 0, 0, 0))
    ImageDraw.Draw(lay).polygon([(x * SS, y * SS) for x, y in tri], fill=(120, 150, 220, 60))
    im.paste(lay, (0, 0), lay)
    poly(d, tri, outline=(90, 110, 190), width=1.4)
    for v, off in (((1, 0, 0), (0, 14)), ((0, 1, 0), (14, 0)), ((0, 0, 1), (14, 6))):
        p = pj(v)
        text(d, (p[0] + off[0], p[1] + off[1]), "1", fs, fill=MUTED)
    text(d, (tri[2][0] + 6, tri[2][1] + 26), "平面 R + G + B = 1", fs, fill=(90, 110, 190), anchor="lm")
    text(d, (tri[2][0] + 6, tri[2][1] + 42), "（rgb 色度图所在的平面）", fs, fill=(90, 110, 190), anchor="lm")

    # 平行四边形（虚线）
    dashed(d, pj(F1), pj(FM), fill=MUTED, width=1.2, dash=6, gap=4)
    dashed(d, pj(F2), pj(FM), fill=MUTED, width=1.2, dash=6, gap=4)
    dashed(d, pj(F2a), pj(FMa), fill=MUTED, width=1.2, dash=6, gap=4)
    dashed(d, pj(F1), pj(FMa), fill=MUTED, width=1.2, dash=6, gap=4)
    # 向量
    for v, col, w in ((F1, RED, 3), (F2, GREEN, 3), (F2a, GREEN, 1.8), (FM, (215, 140, 40), 3), (FMa, (215, 140, 40), 1.8)):
        arrow(d, pj((0, 0, 0)), pj(v), fill=col, width=w, head=10)
    # 色度点（向量与平面的交点）
    line_pts = []
    for v, col in ((F1, RED), (F2, GREEN), (FM, (215, 140, 40)), (FMa, (215, 140, 40))):
        c = chrom(v)
        p = pj(c)
        line_pts.append(p)
        ellipse(d, (p[0] - 4.5, p[1] - 4.5, p[0] + 4.5, p[1] + 4.5), fill=WHITE, outline=col, width=2)
    # f1 与 f2 的连线（两个平面的交线）
    c1, c2 = chrom(F1), chrom(F2)
    ext = 0.25
    a = c1 + (c1 - c2) * ext
    b = c2 + (c2 - c1) * ext
    line(d, (*pj(a), *pj(b)), fill=INK, width=1.4)

    # 文字标注
    lab = font(13, bold=True)
    OR = (215, 140, 40)
    p = pj(F1); text(d, (p[0] + 8, p[1] + 2), "F1 (R1, G1, B1)", lab, fill=RED, anchor="lm")
    p = pj(F2); text(d, (p[0] - 8, p[1] - 2), "F2 (R2, G2, B2)", lab, fill=GREEN, anchor="rb")
    p = pj(F2a); text(d, (p[0] - 8, p[1] - 2), "αF2", lab, fill=GREEN, anchor="rb")
    p = pj(FM); text(d, (p[0] + 8, p[1] + 2), "FM = F1 + F2", lab, fill=OR, anchor="lm")
    p = pj(FMa); text(d, (p[0] + 8, p[1] - 2), "FM' = F1 + αF2", lab, fill=OR, anchor="lb")
    p = pj(c1); text(d, (p[0] + 6, p[1] + 10), "f1", fb, fill=RED, anchor="lt")
    p = pj(c2); text(d, (p[0] - 8, p[1] + 6), "f2", fb, fill=GREEN, anchor="rt")
    p = pj(chrom(FM)); text(d, (p[0] + 4, p[1] + 12), "fM", fb, fill=OR, anchor="lt")
    p = pj(chrom(FMa)); text(d, (p[0] - 4, p[1] - 12), "fM'", fb, fill=OR, anchor="rb")

    callout(d, (640, 60, 970, 130), "FM 是 F1、F2 张成的平行四边形的对角线，\n三个向量共面；该平面与 R+G+B=1 的交线\n是一条直线，f1、fM、f2 都在这条线上", fs)
    callout(d, (640, 150, 970, 206), "改变混合比（F2 → αF2），\nfM 只沿这条直线移动（内分点）", fs)
    text(d, (W / 2, 24), "两色混合：刺激值相加就是向量相加，色度点落在 f1、f2 的连线上（模式图）", f)
    text(d, (W / 2, 44), "空心圆点为向量与平面 R + G + B = 1 的交点，即色度坐标 f (r, g, b)", fs, fill=MUTED)
    finish(im, os.path.join(out, "mixing-vectors.png"))


FIGURES = {
    "gamut": fig_gamut,
    "linearity": fig_linearity,
    "vectors": fig_mixing_vectors,
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", nargs="*", help="只生成这些图")
    ap.add_argument("--out", default="assets/resource/Three-Primaries")
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)
    for n in (args.only or list(FIGURES)):
        FIGURES[n](args.out)


if __name__ == "__main__":
    main()
