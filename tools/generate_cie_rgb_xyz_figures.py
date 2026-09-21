#!/usr/bin/env python3
"""重绘《颜色的客观表达（三）：从 CIE-RGB 到 CIE-XYZ》的插图。

原文（CCS「光と色の話」第 30 回）的插图是日文 PNG，这里按同系列前几篇的配色
与版式重画一遍，文字全部换成中文。

绘图工具与 CIE 1931 等色函数、标准照明体 D65 等数据直接复用同目录下的
generate_cie_xyz_figures.py（第 29 回的脚本），本脚本只另外嵌入本篇新用到的
两组数据：Wright & Guild 的 RGB 等色函数与 CIE 1964 10° 观察者。

除三张等色实验的模式图之外，其余各图全部由公开数据算出：
  - RGB 等色函数、rg 色度图、XYZ 虚拟三原色在 rg 图上的位置
  - 2° 与 10° 观察者的等色函数对比
  - 物体色在各反射率下可达的色度范围（MacAdam 极限）及其三维形状：
    按最优颜色（光谱反射率只取 0/1、至多两次跳变）在标准照明体 D65 下逐一
    积分求得，没有任何一处是凭手感画的。

文中另有三张图（xy 色度图、CIE 1931 等色函数、明度分层）直接引用第 29 回的
文件，不在此重复生成。

用法:
    python3 tools/generate_cie_rgb_xyz_figures.py                 # 全部
    python3 tools/generate_cie_rgb_xyz_figures.py --only rg-chromaticity
    python3 tools/generate_cie_rgb_xyz_figures.py --out DIR
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
    WL_CMF, CMF, WL_D65, D65, _parse, cmf_at, chroma_rgb, wavelength_rgb,
    xyz_to_srgb8, xyY_to_XYZ, spectral_locus,
    font, ifont, canvas, finish, text, rect, line, polyline, poly, ellipse, arc,
    arrow, dashed, callout, Axes, bar_label, spectrum_strip,
)

# ==========================================================================
# 本篇新用到的数据（取自 colour-science 内置数据表，脚本导出后原样嵌入）
#   - Wright & Guild 1931 2° RGB 等色函数：CIE 1931 RGB 表色系的 r̄ ḡ b̄，
#     原刺激为 700.0 / 546.1 / 435.8 nm 的单色光，以等能白归一
#   - CIE 1964 10° 标准观察者等色函数（CIE 15:2004 / ISO 11664-1）
# ==========================================================================

# Wright & Guild 1931 2° RGB 等色函数 r̄ ḡ b̄（CIE 1931 RGB 表色系，原刺激 700.0 / 546.1 / 435.8 nm），5 nm，380–780 nm
CMF_RGB_1931 = """
380 3e-05 -1e-05 0.00117
385 5e-05 -2e-05 0.00189
390 0.0001 -4e-05 0.00359
395 0.00017 -7e-05 0.00647
400 0.0003 -0.00014 0.01214
405 0.00047 -0.00022 0.01969
410 0.00084 -0.00041 0.03707
415 0.00139 -0.0007 0.06637
420 0.00211 -0.0011 0.11541
425 0.00266 -0.00143 0.18575
430 0.00218 -0.00119 0.24769
435 0.00036 -0.00021 0.29012
440 -0.00261 0.00149 0.31228
445 -0.00673 0.00379 0.3186
450 -0.01213 0.00678 0.3167
455 -0.01874 0.01046 0.31166
460 -0.02608 0.01485 0.29821
465 -0.03324 0.01977 0.27295
470 -0.03933 0.02538 0.22991
475 -0.04471 0.03183 0.18592
480 -0.04939 0.03914 0.14494
485 -0.05364 0.04713 0.10968
490 -0.05814 0.05689 0.08257
495 -0.06414 0.06948 0.06246
500 -0.07137 0.08536 0.04776
505 -0.0812 0.10593 0.03688
510 -0.08901 0.1286 0.02698
515 -0.09356 0.15262 0.01842
520 -0.09264 0.17468 0.01221
525 -0.08473 0.19113 0.0083
530 -0.07101 0.20317 0.00549
535 -0.05316 0.21083 0.0032
540 -0.03152 0.21466 0.00146
545 -0.00613 0.21487 0.00023
550 0.02279 0.21178 -0.00058
555 0.05514 0.20588 -0.00105
560 0.0906 0.19702 -0.0013
565 0.1284 0.18522 -0.00138
570 0.16768 0.17087 -0.00135
575 0.20715 0.15429 -0.00123
580 0.24562 0.1361 -0.00108
585 0.27989 0.11686 -0.00093
590 0.30928 0.09754 -0.00079
595 0.33184 0.07909 -0.00063
600 0.34429 0.06246 -0.00049
605 0.34756 0.04776 -0.00038
610 0.33971 0.03557 -0.0003
615 0.32265 0.02583 -0.00022
620 0.29708 0.01828 -0.00015
625 0.26348 0.01253 -0.00011
630 0.22677 0.00833 -8e-05
635 0.19233 0.00537 -5e-05
640 0.15968 0.00334 -3e-05
645 0.12905 0.00199 -2e-05
650 0.10167 0.00116 -1e-05
655 0.07857 0.00066 -1e-05
660 0.05932 0.00037 0
665 0.04366 0.00021 0
670 0.03149 0.00011 0
675 0.02294 6e-05 0
680 0.01687 3e-05 0
685 0.01187 1e-05 0
690 0.00819 0 0
695 0.00572 0 0
700 0.0041 0 0
705 0.00291 0 0
710 0.0021 0 0
715 0.00148 0 0
720 0.00105 0 0
725 0.00074 0 0
730 0.00052 0 0
735 0.00036 0 0
740 0.00025 0 0
745 0.00017 0 0
750 0.00012 0 0
755 8e-05 0 0
760 6e-05 0 0
765 4e-05 0 0
770 3e-05 0 0
775 1e-05 0 0
780 0 0 0
"""

# CIE 1964 10° 标准观察者等色函数 x̄10 ȳ10 z̄10，5 nm，380–780 nm
CMF_1964 = """
380 0.000159952 1.7364e-05 0.000704776
385 0.00066244 7.156e-05 0.0029278
390 0.0023616 0.0002534 0.0104822
395 0.0072423 0.0007685 0.032344
400 0.0191097 0.0020044 0.0860109
405 0.0434 0.004509 0.19712
410 0.084736 0.008756 0.389366
415 0.140638 0.014456 0.65676
420 0.204492 0.021391 0.972542
425 0.264737 0.029497 1.2825
430 0.314679 0.038676 1.55348
435 0.357719 0.049602 1.7985
440 0.383734 0.062077 1.96728
445 0.386726 0.074704 2.0273
450 0.370702 0.089456 1.9948
455 0.342957 0.106256 1.9007
460 0.302273 0.128201 1.74537
465 0.254085 0.152761 1.5549
470 0.195618 0.18519 1.31756
475 0.132349 0.21994 1.0302
480 0.080507 0.253589 0.772125
485 0.041072 0.297665 0.57006
490 0.016172 0.339133 0.415254
495 0.005132 0.395379 0.302356
500 0.003816 0.460777 0.218502
505 0.015444 0.53136 0.159249
510 0.037465 0.606741 0.112044
515 0.071358 0.68566 0.082248
520 0.117749 0.761757 0.060709
525 0.172953 0.82333 0.04305
530 0.236491 0.875211 0.030451
535 0.304213 0.92381 0.020584
540 0.376772 0.961988 0.013676
545 0.451584 0.9822 0.007918
550 0.529826 0.991761 0.003988
555 0.616053 0.99911 0.001091
560 0.705224 0.99734 0
565 0.793832 0.98238 0
570 0.878655 0.955552 0
575 0.951162 0.915175 0
580 1.01416 0.868934 0
585 1.0743 0.825623 0
590 1.11852 0.777405 0
595 1.1343 0.720353 0
600 1.12399 0.658341 0
605 1.0891 0.593878 0
610 1.03048 0.527963 0
615 0.95074 0.461834 0
620 0.856297 0.398057 0
625 0.75493 0.339554 0
630 0.647467 0.283493 0
635 0.53511 0.228254 0
640 0.431567 0.179828 0
645 0.34369 0.140211 0
650 0.268329 0.107633 0
655 0.2043 0.081187 0
660 0.152568 0.060281 0
665 0.11221 0.044096 0
670 0.0812606 0.0318004 0
675 0.05793 0.0226017 0
680 0.0408508 0.0159051 0
685 0.028623 0.0111303 0
690 0.0199413 0.0077488 0
695 0.013842 0.0053751 0
700 0.00957688 0.00371774 0
705 0.0066052 0.00256456 0
710 0.00455263 0.00176847 0
715 0.0031447 0.00122239 0
720 0.00217496 0.00084619 0
725 0.0015057 0.00058644 0
730 0.00104476 0.00040741 0
735 0.00072745 0.000284041 0
740 0.000508258 0.00019873 0
745 0.00035638 0.00013955 0
750 0.000250969 9.8428e-05 0
755 0.00017773 6.9819e-05 0
760 0.00012639 4.9737e-05 0
765 9.0151e-05 3.55405e-05 0
770 6.45258e-05 2.5486e-05 0
775 4.6339e-05 1.83384e-05 0
780 3.34117e-05 1.3249e-05 0
"""

WL_RGB, CMF_RGB = _parse(CMF_RGB_1931)   # 380..780 nm, 5 nm
WL_64, CMF_64 = _parse(CMF_1964)         # 380..780 nm, 5 nm

# 原文给出的 RGB -> XYZ 变换（CIE 1931），已核对：作用于 r̄ ḡ b̄ 后与 x̄ ȳ z̄ 逐点一致
M_RGB2XYZ = np.array([[2.7689, 1.7517, 1.1302],
                      [1.0000, 4.5907, 0.0601],
                      [0.0000, 0.0565, 5.5943]])

PRIMARY_WL = {"R": 700.0, "G": 546.1, "B": 435.8}

# 公式用字体：Hiragino Sans GB 没有带上横线的 r̄ ḡ b̄、减号与 ⇒，
# 日文版 Hiragino Sans（ヒラギノ角ゴシック）有，公式片段改用它
MATH_FONT = "/System/Library/Fonts/ヒラギノ角ゴシック W6.ttc"
MATH_FONT_LIGHT = "/System/Library/Fonts/ヒラギノ角ゴシック W3.ttc"


def mfont(size, bold=True):
    from PIL import ImageFont
    path = MATH_FONT if bold else MATH_FONT_LIGHT
    if os.path.exists(path):
        return ImageFont.truetype(path, int(size * SS))
    return font(size, bold)


def formula(d, xy, tokens, size=16, fill=INK, anchor="mm"):
    """逐段排版一条公式。tokens 为 [(文字, 是否带上横线), ...]。

    PIL 不做字形合成，组合用的上横线（U+0304）会被当成独立字符排在字母后面，
    所以带横线的记号（r̄ ḡ b̄）这里用手工画线代替。
    """
    f = mfont(size)
    widths = [f.getlength(t) / SS for t, _ in tokens]
    total = sum(widths)
    x, y = xy
    if anchor[0] == "m":
        x -= total / 2
    elif anchor[0] == "r":
        x -= total
    for (t, bar), w in zip(tokens, widths):
        text(d, (x, y), t, f, fill=fill, anchor="l" + anchor[1])
        if bar:
            line(d, (x + 1, y - size * 0.62, x + w - 1, y - size * 0.62), fill=fill, width=1.6)
        x += w


def rg_locus(step=1):
    """RGB 表色系的光谱轨迹 (r, g)，1 nm 一点。

    Wright & Guild 的原表只有 5 nm 一档，画出来是折线。RGB 与 XYZ 之间只差一个
    已核对过的线性变换，所以这里用 1 nm 的 CIE 1931 x̄ȳz̄ 经矩阵求逆得到
    1 nm 的 r̄ḡb̄，再算色度。在 5 nm 的格点上它与原表的色度之差绝大多数 < 1e-3，
    只有 500 nm 附近因 r+g+b 接近 0 而放大到 0.01，可见光两端亦然，图上看不出来。
    """
    Mi = np.linalg.inv(M_RGB2XYZ)
    out = []
    for wl in range(380, 701, step):
        rgb = Mi @ cmf_at(wl)
        ssum = rgb.sum()
        if abs(ssum) < 1e-6:
            continue
        out.append((wl, rgb[0] / ssum, rgb[1] / ssum))
    return out


def xyz_primaries_in_rg():
    """XYZ 的三个虚拟原刺激在 rg 色度图上的位置。"""
    Mi = np.linalg.inv(M_RGB2XYZ)
    out = {}
    for name, v in zip("XYZ", np.eye(3)):
        rgb = Mi @ v
        out[name] = (rgb[0] / rgb.sum(), rgb[1] / rgb.sum())
    return out


# ------------------------------------------------------------ MacAdam 极限
def _d65_on(wl):
    return np.interp(wl, WL_D65, D65)


def macadam_contour(level, n=360, wl0=380, wl1=780):
    """反射率为 level（%）的物体色在 D65 下可达的色度边界（MacAdam 极限）。

    边界由最优颜色给出：光谱反射率只取 0 或 1、至多两次跳变。把波长看成
    首尾相接的圆，最优颜色就是圆上的一段弧取 1、其余取 0。对每个起点 λ1，
    弧长越长 Y 越大，用插值找出 Y 恰为 level 的弧长即可得到边界上的一点。
    """
    wl = np.arange(wl0, wl1 + 1, 1.0)
    c = np.array([cmf_at(w) for w in wl])            # N x 3
    s = _d65_on(wl)
    w = c * s[:, None]                               # 每个波长对 XYZ 的贡献
    k = 100.0 / w[:, 1].sum()
    w = w * k
    N = len(wl)
    ww = np.concatenate([w, w])                      # 环绕
    cum = np.concatenate([np.zeros((1, 3)), np.cumsum(ww, axis=0)])
    pts = []
    for i in range(0, N, max(1, N // n)):
        # 弧 [i, i+L)：XYZ = cum[i+L] - cum[i]，Y 随 L 单调增
        seg = cum[i:i + N + 1] - cum[i]
        Y = seg[:, 1]
        if level >= Y[-1]:
            continue
        L = np.searchsorted(Y, level)
        if L == 0:
            continue
        t = (level - Y[L - 1]) / max(1e-9, Y[L] - Y[L - 1])
        xyz = seg[L - 1] + t * (seg[L] - seg[L - 1])
        tot = xyz.sum()
        pts.append((xyz[0] / tot, xyz[1] / tot))
    return pts


def d65_white_xy():
    wl = np.arange(380, 781, 1.0)
    c = np.array([cmf_at(w) for w in wl])
    xyz = (c * _d65_on(wl)[:, None]).sum(axis=0)
    return xyz[0] / xyz.sum(), xyz[1] / xyz.sum()


# ==========================================================================
# 图 1：视感测色（等色实验）的装置（模式图）
# ==========================================================================
def _projector(d, xy, target, col, size=(64, 46)):
    """一台投影灯：朝着 target 方向的矩形机身 + 前端的小镜头，返回镜头位置。"""
    x, y = xy
    ang = math.atan2(target[1] - y, target[0] - x)
    c, sn = math.cos(ang), math.sin(ang)
    w, h = size

    def rot(dx, dy):
        return (x + dx * c - dy * sn, y + dx * sn + dy * c)

    body = [rot(-w / 2, -h / 2), rot(w / 2, -h / 2), rot(w / 2, h / 2), rot(-w / 2, h / 2)]
    poly(d, body, fill=(232, 234, 240), outline=INK, width=1.6)
    lens = [rot(w / 2, -8), rot(w / 2 + 10, -8), rot(w / 2 + 10, 8), rot(w / 2, 8)]
    poly(d, lens, fill=col, outline=INK, width=1.2)
    return rot(w / 2 + 10, 0)


def fig_apparatus(out):
    """等色实验的装置布置：按 Guild 与 Wright 实验的常见画法（白屏 + 隔板 + 狭缝）。"""
    W, H = 940, 560
    im, d = canvas(W, H)
    f = font(14)
    fb = font(15, bold=True)
    fs = font(12)
    # 右侧：白屏；中间一块隔板把屏分成上下两半视野
    sx = 720
    rect(d, (sx - 6, 70, sx + 6, 500), fill=WHITE, outline=INK, width=2)
    text(d, (sx, 50), "白屏", fb)
    top, bot = (sx - 6, 210), (sx - 6, 370)
    line(d, (520, 290, sx - 6, 290), fill=INK, width=6)
    text(d, (620, 306), "隔板", fs, fill=MUTED)
    # 左侧：带狭缝的挡板与观察者
    bx = 250
    rect(d, (bx - 5, 60, bx + 5, 520), fill=INK)
    rect(d, (bx - 7, 278, bx + 7, 302), fill=WHITE)
    text(d, (bx, 40), "带狭缝的挡板", fb)
    ex, ey = 150, 290
    ellipse(d, (ex - 26, ey - 18, ex + 26, ey + 18), fill=(236, 242, 250), outline=INK, width=1.6)
    ellipse(d, (ex - 8, ey - 8, ex + 8, ey + 8), fill=INK)
    text(d, (ex, ey + 40), "观察者", f)
    for tgt in (top, bot):
        dashed(d, (ex + 26, ey), tgt, fill=MUTED, width=1.2, dash=6, gap=5)
    # 三原色投影灯：都投向上半视野
    prim = [((520, 100), (206, 60, 55), "[R]"), ((440, 150), (70, 150, 80), "[G]"), ((370, 210), (60, 110, 210), "[B]")]
    for xy, col, lab in prim:
        lens = _projector(d, xy, top, col)
        line(d, (lens[0], lens[1], top[0], top[1]), fill=col, width=2.6)
        text(d, (xy[0] - 50, xy[1]), lab, fb, fill=col)
    text(d, (600, 60), "三原色（原刺激）", f, fill=MUTED)
    # 试料光：投向下半视野
    tcol = (240, 150, 40)
    lens = _projector(d, (420, 440), bot, tcol)
    line(d, (lens[0], lens[1], bot[0], bot[1]), fill=tcol, width=2.6)
    text(d, (370, 478), "试料光 F（待匹配的单色光）", f, fill=(190, 110, 20))
    # 屏上两半视野的说明
    text(d, (sx + 16, 210), "上半视野：三原色的混合光", fs, fill=MUTED, anchor="lm")
    text(d, (sx + 16, 370), "下半视野：试料光", fs, fill=MUTED, anchor="lm")
    text(d, (W / 2, 536), "观察者透过狭缝同时看到屏上的两半视野，调节三原色的强度直到两半颜色一致", fs, fill=MUTED)
    finish(im, os.path.join(out, "matching-apparatus.png"))


# ==========================================================================
# 图 2 / 图 3：等色实验的原理（模式图）
# ==========================================================================
def _draw_matching(out, name, negative):
    W, H = 940, 520
    im, d = canvas(W, H)
    f = font(14)
    fb = font(16, bold=True)
    fs = font(12)
    fi = ifont(17)
    # 比较视野：左右两半的圆
    cx, cy, r = 470, 250, 62
    lc = wavelength_rgb(500) if negative else (240, 150, 40)
    d.pieslice([(cx - r) * SS, (cy - r) * SS, (cx + r) * SS, (cy + r) * SS], 90, 270, fill=lc)
    d.pieslice([(cx - r) * SS, (cy - r) * SS, (cx + r) * SS, (cy + r) * SS], -90, 90, fill=lc)
    ellipse(d, (cx - r, cy - r, cx + r, cy + r), outline=INK, width=2)
    line(d, (cx, cy - r, cx, cy + r), fill=INK, width=2)
    text(d, (cx, cy - r - 18), "比较视野", fb)
    text(d, (cx - r / 2, cy + r + 16), "左", fs, fill=MUTED)
    text(d, (cx + r / 2, cy + r + 16), "右", fs, fill=MUTED)
    ftitle = font(16, bold=True)

    def lamp(x, y, col, lab, sub=None):
        ellipse(d, (x - 26, y - 20, x + 26, y + 20), fill=col, outline=INK, width=1.2)
        text(d, (x, y + 36), lab, fb)
        if sub:
            text(d, (x, y + 56), sub, fs, fill=MUTED)

    def dimmer(x, y, ang):
        # 调光器：一块带狭缝的挡板
        w, h = 26, 40
        c, s = math.cos(ang), math.sin(ang)
        pts = [(x + dx * c - dy * s, y + dx * s + dy * c) for dx, dy in
               ((-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2))]
        poly(d, pts, fill=(225, 228, 238), outline=INK, width=1)
        line(d, (x - 6 * c, y - 6 * s, x + 6 * c, y + 6 * s), fill=INK, width=2)

    # 左：试料色 F
    lamp(120, 250, lc, "试料色 F", "波长 λ 的单色光" if not negative else "λ = 500 nm 的单色光")
    arrow(d, (150, 250), (cx - r - 6, cy), fill=lc, width=4, head=12)
    # 右：三原色，各经调光器射向右半视野
    prim = [("[R]", (206, 60, 55), 820, 135), ("[G]", (70, 150, 80), 860, 250), ("[B]", (60, 110, 210), 820, 365)]
    right_target = (cx + r + 4, cy)
    for lab, col, x, y in prim:
        if negative and lab == "[R]":
            continue
        lamp(x, y, col, lab)
        ang = math.atan2(cy - y, right_target[0] - x)
        mx, my = (x - 28 + right_target[0]) / 2, (y + cy) / 2
        dimmer(mx, my, ang + math.pi / 2)
        arrow(d, (x - 28, y), right_target, fill=col, width=4, head=12)
    if negative:
        # 红原色移到左侧，与试料色一起射入左半视野
        lamp(120, 400, (206, 60, 55), "[R]", "移到试料色一侧")
        p0, p1 = (150, 400), (cx - r - 6, cy + 10)
        dimmer((p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2,
               math.atan2(p1[1] - p0[1], p1[0] - p0[0]) + math.pi / 2)
        arrow(d, p0, p1, fill=(206, 60, 55), width=4, head=12)
        text(d, (840, 436), "原刺激（三原色）", fs, fill=MUTED)
    else:
        text(d, (840, 436), "原刺激（三原色）", fs, fill=MUTED)
        # 调光器说明放在下方正中，指向 [B] 光路上的调光器
        bx_, by_ = (820 - 28 + right_target[0]) / 2, (365 + cy) / 2
        callout(d, (380, 440, 700, 496), "用调光器（狭缝）调节三原色的混色比", fs, tail=(bx_, by_ + 14))
        # 加法混色说明放在左上，指向右半视野的边缘
        callout(d, (60, 60, 380, 116), "三束光同时投到右半视野：\n同时加法混色", fs, tail=(cx + r + 6, cy - 30))
    # 观察者
    ex, ey = cx - 150, 430
    ellipse(d, (ex - 20, ey - 14, ex + 20, ey + 14), fill=(236, 242, 250), outline=INK, width=1.4)
    ellipse(d, (ex - 7, ey - 7, ex + 7, ey + 7), fill=INK)
    dashed(d, (ex + 16, ey - 10), (cx - 20, cy + r), fill=MUTED)
    dashed(d, (ex + 20, ey - 8), (cx + 20, cy + r), fill=MUTED)
    text(d, (ex, ey + 30), "观察者", fs, fill=MUTED)
    # 公式
    if negative:
        formula(d, (W / 2, 30), [("F(λ) + ", False), ("r", True), ("·[R] ≡ ", False), ("g", True), ("·[G] + ", False),
                                 ("b", True), ("·[B]    ⇒    F(λ) ≡ −", False), ("r", True), ("·[R] + ", False),
                                 ("g", True), ("·[G] + ", False), ("b", True), ("·[B]", False)], 17, CURVE)
    else:
        text(d, (W / 2 - 120, 30), "调到左右视野看起来一样时：", font(16, bold=True), fill=CURVE, anchor="rm")
        formula(d, (W / 2 - 120, 30), [("F ≡ ", False), ("r", True), ("·[R] + ", False), ("g", True), ("·[G] + ", False),
                                       ("b", True), ("·[B]", False)], 17, CURVE, anchor="lm")
    finish(im, os.path.join(out, name))


def fig_matching(out):
    _draw_matching(out, "matching-principle.png", negative=False)


def fig_matching_negative(out):
    _draw_matching(out, "matching-negative.png", negative=True)


# ==========================================================================
# 图 4：CIE 1931 RGB 表色系的等色函数
# ==========================================================================
def fig_rgb_cmf(out):
    W, H = 940, 600
    im, d = canvas(W, H)
    fx = font(13)
    ax = Axes(d, (90, 72, 900, 480), (380, 780), (-0.1, 0.4))
    ax.frame(list(range(380, 781, 40)), [-0.1, 0.0, 0.1, 0.2, 0.3, 0.4], fx,
             yfmt="%.1f", ylabel="三刺激值")
    # 零线加粗
    x0, y0 = ax.px(380, 0)
    x1, _ = ax.px(780, 0)
    line(d, (x0, y0, x1, y0), fill=MUTED, width=1.2)
    # 负值区域底色
    neg = [(wl, r) for wl, (r, g, b) in zip(WL_RGB, CMF_RGB) if r < 0]
    a, b = neg[0][0], neg[-1][0]
    pa, _ = ax.px(a, 0)
    pb, _ = ax.px(b, 0)
    rect(d, (pa, 72, pb, 480), fill=(250, 236, 232))
    ax.grid(list(range(380, 781, 40)), [-0.1, 0.0, 0.1, 0.2, 0.3, 0.4])
    line(d, (x0, y0, x1, y0), fill=MUTED, width=1.2)
    for i, col in enumerate((RED, GREEN, BLUE)):
        ax.plot(WL_RGB, CMF_RGB[:, i], fill=col, width=2.6)
    # 三原色波长
    # 三条虚线是三个原刺激（单色光）的波长；在各自的波长处，另外两条等色函数恰为 0
    for lab, wl, col in (("[B] 435.8", 435.8, BLUE), ("[G] 546.1", 546.1, GREEN), ("[R] 700.0", 700.0, RED)):
        px, py0 = ax.px(wl, 0)
        dashed(d, (px, 72), (px, 480), fill=col, width=1, dash=5, gap=4)
        text(d, (px, 58), lab, fx, fill=col)
        ellipse(d, (px - 4, py0 - 4, px + 4, py0 + 4), fill=WHITE, outline=col, width=1.6)
    text(d, (495, 30), "虚线：三个原刺激（单色光）的波长；圆圈：在原刺激的波长处，另外两条等色函数为 0", font(12), fill=MUTED)
    lab = [("b", 445, 0.36, BLUE, -40, -6), ("g", 546, 0.24, GREEN, 48, -6), ("r", 605, 0.36, RED, 46, -6)]
    for s, x, y, col, dx, dy in lab:
        px, py = ax.px(x, y)
        bar_label(d, (px + dx, py + dy), s, col)
    px, py = ax.px(500, 0.30)
    rect(d, (px - 112, py - 22, px + 112, py + 22), fill=(252, 250, 232), outline=(224, 214, 170), radius=8)
    formula(d, (px - 100, py), [("r", True), ("(λ)", False)], 14, RED, anchor="lm")
    text(d, (px + 26, py), "在这一段（底色）为负值", fx)
    tx, ty = ax.px(500, -0.05)
    line(d, (px, py + 22, tx, ty - 8), fill=(224, 214, 170), width=1.4)
    spectrum_strip(d, (90, 506, 900, 524))
    text(d, (495, 548), "波长 (nm)", font(15))
    finish(im, os.path.join(out, "cie1931-rgb-cmf.png"))


# ==========================================================================
# 图 5：2° 与 10° 视场的等色函数
# ==========================================================================
def fig_cmf_2_vs_10(out):
    W, H = 940, 600
    im, d = canvas(W, H)
    fx = font(13)
    ax = Axes(d, (90, 60, 900, 480), (380, 780), (0, 2.2))
    ax.frame(list(range(380, 781, 40)), [i * 0.2 for i in range(12)], fx, yfmt="%.1f", ylabel="三刺激值")
    m = (WL_CMF >= 380) & (WL_CMF <= 780)
    for i, col in enumerate((RED, GREEN, BLUE)):
        ax.plot(WL_CMF[m], CMF[m, i], fill=col, width=2.4)
        pts = [ax.px(x, y) for x, y in zip(WL_64, CMF_64[:, i])]
        for k in range(0, len(pts) - 1, 2):
            line(d, (pts[k][0], pts[k][1], pts[k + 1][0], pts[k + 1][1]), fill=col, width=2.0)
    # 图例
    lx, ly = 640, 90
    rect(d, (lx - 10, ly - 12, lx + 240, ly + 64), fill=WHITE, outline=BORDER, radius=6)
    line(d, (lx, ly + 6, lx + 40, ly + 6), fill=INK, width=2.4)
    text(d, (lx + 50, ly + 6), "实线：CIE 1931 2° 视场", fx, anchor="lm")
    for k in range(0, 40, 10):
        line(d, (lx + k, ly + 40, lx + k + 5, ly + 40), fill=INK, width=2.0)
    text(d, (lx + 50, ly + 40), "虚线：CIE 1964 10° 视场", fx, anchor="lm")
    for s, x, y, col, dx, dy in (("z", 445, 1.85, BLUE, 70, -4), ("y", 545, 1.02, GREEN, -50, -22), ("x", 600, 1.08, RED, 50, -22)):
        px, py = ax.px(x, y)
        bar_label(d, (px + dx, py + dy), s, col)
    spectrum_strip(d, (90, 506, 900, 524))
    text(d, (495, 548), "波长 (nm)", font(15))
    finish(im, os.path.join(out, "cmf-2deg-vs-10deg.png"))


# ==========================================================================
# 图 6 / 图 7：rg 色度图
# ==========================================================================
def _rg_diagram(out, name, with_xyz):
    W, H = 900, 820
    im, d = canvas(W, H)
    fx = font(13)
    fb = font(15, bold=True)
    fi = ifont(20)
    if with_xyz:
        xr, yr = (-2.0, 2.0), (-0.6, 3.0)
        xt = [-2.0, -1.5, -1.0, -0.5, 0.0, 0.5, 1.0, 1.5, 2.0]
        yt = [-0.5, 0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0]
    else:
        xr, yr = (-1.6, 1.6), (-0.6, 2.2)
        xt = [-1.5, -1.0, -0.5, 0.0, 0.5, 1.0, 1.5]
        yt = [-0.5, 0.0, 0.5, 1.0, 1.5, 2.0]
    ax = Axes(d, (80, 50, 860, 760), xr, yr)
    ax.frame(xt, yt, fx, xfmt="%.1f", yfmt="%.1f", grid=False)
    minor = (216, 220, 236)
    v = math.ceil(xr[0] * 10) / 10
    while v <= xr[1] + 1e-9:
        p0, p1 = ax.px(v, yr[0]), ax.px(v, yr[1])
        line(d, (p0[0], p0[1], p1[0], p1[1]), fill=GRID if abs(v * 2 - round(v * 2)) < 1e-9 else minor,
             width=1.2 if abs(v * 2 - round(v * 2)) < 1e-9 else 0.6)
        v = round(v + 0.1, 6)
    v = math.ceil(yr[0] * 10) / 10
    while v <= yr[1] + 1e-9:
        p0, p1 = ax.px(xr[0], v), ax.px(xr[1], v)
        line(d, (p0[0], p0[1], p1[0], p1[1]), fill=GRID if abs(v * 2 - round(v * 2)) < 1e-9 else minor,
             width=1.2 if abs(v * 2 - round(v * 2)) < 1e-9 else 0.6)
        v = round(v + 0.1, 6)
    rect(d, ax.box, outline=BORDER, width=1.2)
    # 坐标轴
    x0, yy = ax.px(xr[0], 0)
    x1, _ = ax.px(xr[1], 0)
    line(d, (x0, yy, x1, yy), fill=INK, width=1.6)
    xx, y0 = ax.px(0, yr[0])
    _, y1 = ax.px(0, yr[1])
    line(d, (xx, y0, xx, y1), fill=INK, width=1.6)
    text(d, (x1 - 14, yy + 18), "r", fi)
    text(d, (xx + 18, y1 + 14), "g", fi)
    # 光谱轨迹（1 nm 一点）
    loc = rg_locus(1)
    idx = {wl: k for k, (wl, _, _) in enumerate(loc)}
    pts = [ax.px(r, g) for _, r, g in loc]
    polyline(d, pts, fill=INK, width=1.8)
    # 纯紫轨迹
    line(d, (pts[0][0], pts[0][1], pts[-1][0], pts[-1][1]), fill=(150, 80, 170), width=1.8)
    # 每 10 nm 一个刻度，刻度线垂直于轨迹、朝外；部分刻度标波长
    labelled = {380, 470, 480, 490, 500, 510, 520, 530, 540, 550, 560, 570, 580, 600, 700}
    wx, wy = ax.px(1 / 3, 1 / 3)
    for wl in range(380, 701, 10):
        k = idx[wl]
        px, py = pts[k]
        pa, pb = pts[max(0, k - 3)], pts[min(len(pts) - 1, k + 3)]
        tx, ty = pb[0] - pa[0], pb[1] - pa[1]
        n = math.hypot(tx, ty) or 1.0
        nx, ny = -ty / n, tx / n
        if (px - wx) * nx + (py - wy) * ny < 0:      # 法线朝外（背离白点）
            nx, ny = -nx, -ny
        L = 7 if wl in labelled else 4
        line(d, (px, py, px + nx * L, py + ny * L), fill=INK, width=1.4)
        if wl == 380:
            text(d, (px - 6, py + 12), "380", fx, fill=MUTED, anchor="rt")
        elif wl in labelled:
            text(d, (px + nx * (L + 14), py + ny * (L + 10)), str(wl), fx, fill=MUTED)
    # 实际三原色与等能白
    for lab, (r, g), col in (("[R]", (1, 0), RED), ("[G]", (0, 1), GREEN), ("[B]", (0, 0), BLUE)):
        px, py = ax.px(r, g)
        rect(d, (px - 5, py - 5, px + 5, py + 5), fill=col)
        box = {"[R]": (px + 30, py + 12, px + 80, py + 36), "[G]": (px + 24, py - 30, px + 74, py - 6),
               "[B]": (px - 84, py + 10, px - 34, py + 34)}[lab]
        callout(d, box, lab, fb, text_fill=col, tail=(px, py))
    tri = [ax.px(1, 0), ax.px(0, 1), ax.px(0, 0)]
    poly(d, tri + [tri[0]], outline=MUTED, width=1.0)
    wx, wy = ax.px(1 / 3, 1 / 3)
    ellipse(d, (wx - 4, wy - 4, wx + 4, wy + 4), fill=INK)
    text(d, (wx + 10, wy + 4), "W (1/3, 1/3)", fx, anchor="lt")
    text(d, ax.px(xr[0] + 0.08, yr[0] + 0.12), "灰色三角形：实际的三原色 [R] [G] [B] 围成的范围", fx, fill=MUTED, anchor="lm")
    if with_xyz:
        P = xyz_primaries_in_rg()
        tp = [ax.px(*P[k]) for k in "XYZ"]
        for k in range(3):
            a, b = tp[k], tp[(k + 1) % 3]
            dashed(d, a, b, fill=ACCENT, width=1.6, dash=8, gap=5)
        for k, (lab, off) in zip("XYZ", (("[X]", (36, 26)), ("[Y]", (40, -10)), ("[Z]", (-42, 26)))):
            px, py = ax.px(*P[k])
            ellipse(d, (px - 6, py - 6, px + 6, py + 6), fill=ACCENT)
            text(d, (px + off[0], py + off[1]), lab, fb, fill=ACCENT)
            text(d, (px + off[0], py + off[1] + 18), "(%.2f, %.2f)" % P[k], fx, fill=ACCENT)
        callout(d, (560, 90, 850, 146), "虚拟的三原色 [X] [Y] [Z]\n三角形把整个光谱轨迹包在里面", fx,
                tail=((tp[0][0] + tp[1][0]) / 2, (tp[0][1] + tp[1][1]) / 2))
    finish(im, os.path.join(out, name))


def fig_rg_chromaticity(out):
    _rg_diagram(out, "rg-chromaticity.png", with_xyz=False)


def fig_rg_xyz_triangle(out):
    _rg_diagram(out, "rg-chromaticity-xyz-triangle.png", with_xyz=True)


# ==========================================================================
# 图 8：RGB 与 XYZ 两套等色函数并排
# ==========================================================================
def fig_rgb_vs_xyz(out):
    W, H = 940, 460
    im, d = canvas(W, H)
    fx = font(12)
    fb = font(14, bold=True)
    for k, (box, title) in enumerate((((70, 60, 450, 360), "RGB 表色系的等色函数"),
                                      ((530, 60, 910, 360), "XYZ 表色系的等色函数"))):
        if k == 0:
            ax = Axes(d, box, (380, 780), (-0.1, 0.4))
            ax.frame([400, 500, 600, 700], [-0.1, 0, 0.1, 0.2, 0.3, 0.4], fx, yfmt="%.1f")
            x0, y0 = ax.px(380, 0)
            x1, _ = ax.px(780, 0)
            line(d, (x0, y0, x1, y0), fill=MUTED, width=1.2)
            for i, col in enumerate((RED, GREEN, BLUE)):
                ax.plot(WL_RGB, CMF_RGB[:, i], fill=col, width=2.2)
            text(d, (260, 386), "红色曲线有一段负值；三条曲线的峰值高低不一", fx, fill=MUTED)
        else:
            ax = Axes(d, box, (380, 780), (0, 2.0))
            ax.frame([400, 500, 600, 700], [0, 0.5, 1.0, 1.5, 2.0], fx, yfmt="%.1f")
            m = (WL_CMF >= 380) & (WL_CMF <= 780)
            for i, col in enumerate((RED, GREEN, BLUE)):
                ax.plot(WL_CMF[m], CMF[m, i], fill=col, width=2.2)
            px, py = ax.px(555, 1.0)
            dashed(d, (box[0], py), (px, py), fill=GREEN, width=1)
            dashed(d, (px, py), (px, box[3]), fill=GREEN, width=1)
            text(d, (px + 6, py - 14), "峰值 1.0 在 555 nm", fx, fill=GREEN, anchor="lm")
            text(d, (720, 386), "全部非负；绿色曲线即光谱光视效率 V(λ)", fx, fill=MUTED)
        text(d, ((box[0] + box[2]) / 2, 40), title, fb)
        text(d, ((box[0] + box[2]) / 2, 410), "波长 (nm)", fx, fill=MUTED)
    finish(im, os.path.join(out, "rgb-vs-xyz-cmf.png"))


# ==========================================================================
# 图 9：MacAdam 极限（物体色在各反射率下可达的色度范围）
# ==========================================================================
LEVELS = (10, 20, 30, 40, 50, 60, 70, 80, 90, 95)


def fig_macadam(out):
    W, H = 760, 800
    im, d = canvas(W, H)
    fx = font(13)
    fb = font(14, bold=True)
    ax = Axes(d, (80, 40, 720, 760), (0, 0.8), (0, 0.9))
    ax.frame([i / 10 for i in range(9)], [i / 10 for i in range(10)], fx, xfmt="%.1f", yfmt="%.1f")
    text(d, (W / 2, 786), "x", ifont(18))
    text(d, (30, 40), "y", ifont(18))
    loc = spectral_locus(1)
    pts = [ax.px(x, y) for _, x, y in loc]
    polyline(d, pts + [pts[0]], fill=INK, width=1.8)
    for wl in (380, 460, 480, 500, 520, 540, 560, 580, 600, 620, 700):
        X, Yv, Z = cmf_at(wl)
        s = X + Yv + Z
        px, py = ax.px(X / s, Yv / s)
        cx, cy = ax.px(0.33, 0.33)
        ang = math.atan2(py - cy, px - cx)
        text(d, (px + 16 * math.cos(ang), py + 16 * math.sin(ang)), str(wl), font(11), fill=MUTED)
    wx, wy = d65_white_xy()
    for lv in LEVELS:
        c = macadam_contour(lv)
        p = [ax.px(x, y) for x, y in c]
        polyline(d, p + [p[0]], fill=CURVE, width=1.6)
        # 低层沿右下（345°）的射线标，高层等高线挤在白点附近，改沿右上（70°）的尖端标
        ray = math.radians(345 if lv <= 60 else 70)
        best = min(c, key=lambda q: abs((math.atan2(q[1] - wy, q[0] - wx) - ray + math.pi) % (2 * math.pi) - math.pi))
        px, py = ax.px(*best)
        if lv <= 60:
            text(d, (px + 8, py + 6), str(lv), fx, fill=CURVE, anchor="lm")
        else:
            text(d, (px + 8, py - 2), str(lv), fx, fill=CURVE, anchor="lm")
    px, py = ax.px(wx, wy)
    ellipse(d, (px - 5, py - 5, px + 5, py + 5), fill=INK)
    text(d, (px + 10, py + 4), "100（D65 白点）", fb, anchor="lt")
    callout(d, (400, 620, 700, 700), "曲线上的数字为视感反射率 Y (%)\n反射率越高，可达的色度范围越小", fx)
    finish(im, os.path.join(out, "macadam-limits.png"))


# ==========================================================================
# 图 10：物体色的色立体（MacAdam 极限的三维形状）
# ==========================================================================
def _solid_frame(theta, contours, base, wxy, W=720, H=560):
    """色立体绕通过白点的竖直轴旋转 theta（弧度）后的一帧（已抗锯齿缩小）。"""
    im, d = canvas(W, H)
    fx = font(12)
    fi = ifont(17)
    wx, wy = wxy
    ct, st = math.cos(theta), math.sin(theta)
    S, SZ, EL = 520, 3.6, 0.42

    def proj(x, y, Y):
        u = (x - wx) * ct - (y - wy) * st       # 屏幕左右
        v = (x - wx) * st + (y - wy) * ct       # 深度：越大越靠近观察者
        return (W / 2 + u * S, 400 + v * S * EL - Y * SZ)

    # 底面网格与 x、y 轴（跟着一起转）
    for k in range(0, 9):
        a, b = proj(k / 10, 0, 0), proj(k / 10, 0.9, 0)
        line(d, (a[0], a[1], b[0], b[1]), fill=GRID)
    for k in range(0, 10):
        a, b = proj(0, k / 10, 0), proj(0.8, k / 10, 0)
        line(d, (a[0], a[1], b[0], b[1]), fill=GRID)
    o = proj(0, 0, 0)
    for vec, lab in (((0.85, 0, 0), "x"), ((0, 0.95, 0), "y")):
        p = proj(*vec)
        arrow(d, o, p, fill=MUTED, width=1.2, head=8)
        text(d, (p[0] + (12 if lab == "x" else 0), p[1] + (0 if lab == "x" else -12)), lab, fi, fill=MUTED)
    # 竖直的 Y 轴（过白点）
    b0, b1 = proj(wx, wy, 0), proj(wx, wy, 100)
    line(d, (b0[0], b0[1], b1[0], b1[1]), fill=BORDER, width=1)
    # 各层：先画底面的光谱轨迹，再由低到高画等高线（高层盖住低层）
    pts = [proj(x, y, 0) for x, y in base]
    polyline(d, pts + [pts[0]], fill=INK, width=1.3)
    for lv, c in contours:
        p = [proj(x, y, lv) for x, y in c]
        g = int(200 - lv * 0.9)
        poly(d, p, fill=(238, 240, 247))
        polyline(d, p + [p[0]], fill=(g, g + 6, g + 40), width=1.3)
    top = proj(wx, wy, 100)
    ellipse(d, (top[0] - 4, top[1] - 4, top[0] + 4, top[1] + 4), fill=INK)
    text(d, (top[0] + 10, top[1] - 6), "Y = 100", fx, anchor="lm")
    # Y 轴刻度放在画面左侧固定位置
    for Yv in (0, 25, 50, 75, 100):
        yy = 400 - Yv * SZ
        line(d, (56, yy, 62, yy), fill=INK)
        text(d, (50, yy), str(Yv), fx, fill=MUTED, anchor="rm")
    line(d, (62, 400, 62, 400 - 100 * SZ), fill=INK, width=1.2)
    text(d, (62, 400 - 100 * SZ - 14), "Y", fi)
    text(d, (W / 2, H - 22), "物体色的色立体：各反射率 Y 下可达的色度范围（D65）", font(14, bold=True))
    return im.resize((W, H), Image.LANCZOS)


def fig_optimal_solid(out, frames=30, duration=120):
    """绕竖直轴旋转一周的 GIF。"""
    levels = (5,) + LEVELS
    contours = [(lv, macadam_contour(lv, n=180)) for lv in levels]
    base = [(x, y) for _, x, y in spectral_locus(2)]
    wxy = d65_white_xy()
    ims = [_solid_frame(2 * math.pi * k / frames, contours, base, wxy) for k in range(frames)]
    first = ims[0].quantize(colors=64, method=Image.Quantize.MEDIANCUT)
    frames_q = [first] + [im.quantize(palette=first) for im in ims[1:]]
    path = os.path.join(out, "optimal-color-solid.gif")
    frames_q[0].save(path, save_as=True, save_all=True, append_images=frames_q[1:],
                     duration=duration, loop=0, optimize=True)
    print("  %-40s %dx%d  %d 帧  %d KB" % (os.path.basename(path), ims[0].width, ims[0].height,
                                         frames, os.path.getsize(path) // 1024))


FIGURES = {
    "apparatus": fig_apparatus,
    "matching": fig_matching,
    "matching-negative": fig_matching_negative,
    "rgb-cmf": fig_rgb_cmf,
    "cmf-2-vs-10": fig_cmf_2_vs_10,
    "rg-chromaticity": fig_rg_chromaticity,
    "rg-xyz-triangle": fig_rg_xyz_triangle,
    "rgb-vs-xyz": fig_rgb_vs_xyz,
    "macadam": fig_macadam,
    "optimal-solid": fig_optimal_solid,
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", nargs="*", help="只生成这些图")
    ap.add_argument("--out", default="assets/resource/CIE-RGB-XYZ")
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)
    for n in (args.only or list(FIGURES)):
        FIGURES[n](args.out)


if __name__ == "__main__":
    main()
