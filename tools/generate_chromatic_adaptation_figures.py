#!/usr/bin/env python3
"""生成《白点切换：色适应与 Bradford 变换》一文的插图。

依赖 Pillow 与 numpy；绘图工具与 CIE 1931 数据从同目录的
generate_cie_xyz_figures.py 导入，u'v' 变换与色度图填色从
generate_uniform_color_space_figures.py 导入，黑体轨迹从
generate_color_temperature_figures.py 导入。

用法：
    python3 tools/generate_chromatic_adaptation_figures.py              # 全部
    python3 tools/generate_chromatic_adaptation_figures.py --only luther
    python3 tools/generate_chromatic_adaptation_figures.py --check      # 打印正文引用的数值

图里的数据：
    - CIE 1931 2° 等色函数：同 generate_cie_xyz_figures.py（1 nm）
    - Nikon D5100 的光谱灵敏度：英国国家物理实验室（NPL）实测，
      经开源库 colour-science (BSD-3-Clause) 内置数据表导出后原样嵌入（5 nm）
    - Breneman (1987) 对应色实验：同样取自 colour-science 内置数据表，
      只保留以照明光为适应条件的 9 组实验（1、2、3、4、6、8、9、11、12），
      每行为 测试照明下的 u'v'、参照照明下实测对应色的 u'v'
    - 标准白点：A、D50、D65 取 CIE 15:2004 表值（2°）；
      E 为等能白 (1/3, 1/3)；DCI 白取 SMPTE RP 431-2 的 (0.314, 0.351)
    - 适应矩阵：Bradford（Lam, 1985）、Hunt-Pointer-Estévez（按 D65 归一，
      CIECAM02 所用）、CAT02（CIE 159:2004）
"""

import argparse
import math
import os
import sys

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from generate_cie_xyz_figures import (  # noqa: E402
    SS, WHITE, PANEL, GRID, BORDER, INK, MUTED, CURVE, ACCENT, RED, GREEN, BLUE,
    WL_CMF, CMF, cmf_at, spectral_locus,
    font, ifont, canvas, finish, text, rect, line, polyline, poly, ellipse,
    arrow, dashed, callout, Axes, spectrum_strip,
)
from generate_uniform_color_space_figures import (  # noqa: E402
    xy_to_upvp, upvp_to_xy, diagram_image, lighten,
)
from generate_color_temperature_figures import bb_xy, clipped_polyline  # noqa: E402

# ---------------------------------------------------------------- 矩阵与白点
M_BFD = np.array([[0.8951, 0.2664, -0.1614],
                  [-0.7502, 1.7135, 0.0367],
                  [0.0389, -0.0685, 1.0296]])
M_HPE = np.array([[0.38971, 0.68898, -0.07868],
                  [-0.22981, 1.18340, 0.04641],
                  [0.0, 0.0, 1.0]])
M_CAT02 = np.array([[0.7328, 0.4296, -0.1624],
                    [-0.7036, 1.6975, 0.0061],
                    [0.0030, 0.0136, 0.9834]])
WHITES = {
    "A": (0.4476, 0.4074),
    "D50": (0.3457, 0.3585),
    "D65": (0.3127, 0.3290),
    "E": (1 / 3, 1 / 3),
    "DCI": (0.314, 0.351),
}

# sRGB（IEC 61966-2-1）的 RGB -> XYZ(D65)
M_SRGB_D65 = np.array([[0.4124, 0.3576, 0.1805],
                       [0.2126, 0.7152, 0.0722],
                       [0.0193, 0.1192, 0.9505]])

ORANGE = (214, 140, 40)

# ---------------------------------------------------------------- 嵌入的数据
# Nikon D5100，NPL 实测，各通道以自身峰值归一：波长  R  G  B
NIKON_D5100 = """
380 0.00156 0.00012 0.00181
385 0.00190 0.00152 0.00049
390 0.00000 0.00057 0.00088
395 0.00000 0.00000 0.00000
400 0.00000 0.00000 0.00153
405 0.00072 0.00120 0.00570
410 0.00292 0.00134 0.01661
415 0.01294 0.01319 0.07879
420 0.04960 0.06497 0.36171
425 0.07607 0.11510 0.65970
430 0.07659 0.13707 0.75534
435 0.06833 0.15243 0.81045
440 0.06132 0.16864 0.87494
445 0.05473 0.18330 0.92671
450 0.04886 0.19603 0.96314
455 0.04285 0.21734 0.98065
460 0.04023 0.25424 1.00000
465 0.04341 0.30865 0.99640
470 0.04762 0.37347 0.98897
475 0.05077 0.42916 0.95660
480 0.05280 0.45965 0.90496
485 0.05257 0.47106 0.83941
490 0.04789 0.48886 0.75146
495 0.04824 0.53715 0.66010
500 0.05023 0.61649 0.56707
505 0.05508 0.70701 0.47935
510 0.06370 0.80096 0.39406
515 0.08039 0.88137 0.31427
520 0.10039 0.93888 0.24982
525 0.11861 0.98447 0.20182
530 0.12361 1.00000 0.16163
535 0.10306 0.99084 0.13516
540 0.07634 0.96155 0.10999
545 0.05278 0.92814 0.08639
550 0.04119 0.88910 0.06525
555 0.03904 0.83494 0.04786
560 0.04254 0.77632 0.03414
565 0.06021 0.70731 0.02402
570 0.11180 0.63580 0.01977
575 0.26967 0.56551 0.01635
580 0.56450 0.49275 0.01382
585 0.85360 0.42476 0.01195
590 0.98103 0.35179 0.01001
595 1.00000 0.27818 0.00759
600 0.96307 0.21167 0.00646
605 0.90552 0.15672 0.00523
610 0.83428 0.11804 0.00366
615 0.76799 0.08885 0.00396
620 0.70367 0.07010 0.00397
625 0.63916 0.05691 0.00349
630 0.57081 0.04730 0.00404
635 0.49582 0.04120 0.00419
640 0.43834 0.03525 0.00555
645 0.38897 0.03069 0.00546
650 0.34296 0.02680 0.00597
655 0.29279 0.02352 0.00631
660 0.23771 0.02035 0.00610
665 0.16491 0.01546 0.00484
670 0.09129 0.00944 0.00303
675 0.04206 0.00508 0.00172
680 0.02058 0.00291 0.00078
685 0.01029 0.00163 0.00057
690 0.00541 0.00092 0.00028
695 0.00272 0.00050 0.00030
700 0.00128 0.00041 0.00025
705 0.00078 0.00032 0.00009
710 0.00048 0.00026 0.00042
715 0.00049 0.00000 0.00015
720 0.00017 0.00024 0.00002
725 0.00012 0.00006 0.00000
730 0.00000 0.00000 0.00034
735 0.00006 0.00000 0.00000
740 0.00000 0.00000 0.00000
745 0.00000 0.00002 0.00017
750 0.00031 0.00005 0.00018
755 0.00000 0.00009 0.00000
760 0.00000 0.00000 0.00002
765 0.00000 0.00000 0.00006
770 0.00009 0.00014 0.00026
775 0.00014 0.00018 0.00028
780 0.00004 0.00004 0.00000
"""

# Breneman (1987)：实验号  色样  测试照明下 u' v'  实测对应色 u' v'
# 每组第一行（Illuminant）为两种照明光本身的色度
BRENEMAN = """
 1 Illuminant       0.259 0.526 0.200 0.475
 1 Gray             0.259 0.524 0.199 0.487
 1 Red              0.459 0.522 0.420 0.509
 1 Skin             0.307 0.526 0.249 0.497
 1 Orange           0.360 0.544 0.302 0.548
 1 Brown            0.350 0.541 0.290 0.537
 1 Yellow           0.318 0.550 0.257 0.554
 1 Foliage          0.258 0.542 0.192 0.529
 1 Green            0.193 0.542 0.129 0.521
 1 Blue-green       0.180 0.516 0.133 0.469
 1 Blue             0.186 0.445 0.158 0.340
 1 Sky              0.226 0.491 0.178 0.426
 1 Purple           0.278 0.456 0.231 0.365
 2 Illuminant       0.222 0.521 0.204 0.479
 2 Gray             0.227 0.517 0.207 0.486
 2 Red              0.464 0.520 0.449 0.511
 2 Skin             0.286 0.526 0.263 0.505
 2 Orange           0.348 0.546 0.322 0.545
 2 Brown            0.340 0.543 0.316 0.537
 2 Yellow           0.288 0.554 0.265 0.553
 2 Foliage          0.244 0.547 0.221 0.538
 2 Green            0.156 0.548 0.135 0.532
 2 Blue-green       0.159 0.511 0.145 0.472
 2 Blue             0.160 0.406 0.163 0.331
 2 Sky              0.190 0.481 0.176 0.431
 2 Purple           0.258 0.431 0.244 0.349
 3 Illuminant       0.223 0.521 0.206 0.478
 3 Gray             0.228 0.517 0.211 0.494
 3 Red              0.462 0.519 0.448 0.505
 3 Skin             0.285 0.524 0.267 0.507
 3 Orange           0.346 0.546 0.325 0.541
 3 Brown            0.338 0.543 0.321 0.532
 3 Yellow           0.287 0.554 0.267 0.548
 3 Foliage          0.244 0.547 0.226 0.531
 3 Green            0.157 0.548 0.141 0.528
 3 Blue-green       0.160 0.510 0.151 0.486
 3 Blue             0.162 0.407 0.158 0.375
 3 Sky              0.191 0.482 0.179 0.452
 3 Purple           0.258 0.432 0.238 0.396
 4 Illuminant       0.258 0.523 0.199 0.467
 4 Gray             0.257 0.524 0.205 0.495
 4 Red              0.460 0.521 0.416 0.501
 4 Skin             0.308 0.526 0.253 0.503
 4 Orange           0.360 0.544 0.303 0.541
 4 Brown            0.350 0.541 0.296 0.527
 4 Yellow           0.317 0.550 0.260 0.547
 4 Foliage          0.258 0.543 0.203 0.520
 4 Green            0.193 0.543 0.142 0.516
 4 Blue-green       0.180 0.516 0.140 0.484
 4 Blue             0.185 0.445 0.151 0.394
 4 Sky              0.225 0.490 0.180 0.448
 4 Purple           0.278 0.455 0.229 0.388
 6 Illuminant       0.257 0.525 0.201 0.482
 6 Gray             0.267 0.521 0.207 0.485
 6 Red              0.457 0.521 0.398 0.516
 6 Skin             0.316 0.526 0.253 0.503
 6 Orange           0.358 0.545 0.287 0.550
 6 Brown            0.350 0.541 0.282 0.540
 6 Yellow           0.318 0.551 0.249 0.556
 6 Foliage          0.256 0.547 0.188 0.537
 6 Green            0.193 0.542 0.133 0.520
 6 Blue-green       0.180 0.516 0.137 0.466
 6 Blue             0.186 0.445 0.156 0.353
 6 Sky              0.225 0.492 0.178 0.428
 6 Purple           0.276 0.456 0.227 0.369
 8 Illuminant       0.258 0.524 0.195 0.469
 8 Gray             0.257 0.525 0.200 0.494
 8 Red              0.458 0.522 0.410 0.508
 8 Skin             0.308 0.526 0.249 0.502
 8 Orange           0.359 0.545 0.299 0.545
 8 Brown            0.349 0.540 0.289 0.532
 8 Yellow           0.317 0.550 0.256 0.549
 8 Foliage          0.260 0.545 0.198 0.529
 8 Green            0.193 0.543 0.137 0.520
 8 Blue-green       0.182 0.516 0.139 0.477
 8 Blue             0.184 0.444 0.150 0.387
 8 Sky              0.224 0.489 0.177 0.439
 8 Purple           0.277 0.454 0.226 0.389
 9 Illuminant       0.254 0.525 0.195 0.465
 9 Gray             0.256 0.524 0.207 0.496
 9 Red              0.459 0.521 0.415 0.489
 9 Skin             0.307 0.525 0.261 0.500
 9 Orange           0.359 0.545 0.313 0.532
 9 Brown            0.349 0.540 0.302 0.510
 9 Yellow           0.317 0.550 0.268 0.538
 9 Foliage          0.259 0.544 0.212 0.510
 9 Green            0.193 0.542 0.150 0.506
 9 Blue-green       0.181 0.517 0.144 0.487
 9 Blue             0.184 0.444 0.155 0.407
 9 Sky              0.225 0.490 0.183 0.458
 9 Purple           0.276 0.454 0.233 0.404
 9 (Gray)h          0.256 0.525 0.208 0.498
 9 (Red)h           0.456 0.521 0.416 0.501
 9 (Brown)h         0.349 0.539 0.306 0.526
 9 (Foliage)h       0.260 0.545 0.213 0.528
 9 (Green)h         0.193 0.543 0.149 0.525
 9 (Blue)h          0.184 0.444 0.156 0.419
 9 (Purple)h        0.277 0.456 0.236 0.422
11 Illuminant       0.208 0.482 0.174 0.520
11 Gray             0.209 0.483 0.176 0.513
11 Red              0.450 0.512 0.419 0.524
11 Skin             0.268 0.506 0.240 0.528
11 Orange           0.331 0.547 0.293 0.553
11 Brown            0.323 0.542 0.290 0.552
11 Yellow           0.266 0.549 0.236 0.557
11 Foliage          0.227 0.538 0.194 0.552
11 Green            0.146 0.534 0.118 0.551
11 Blue-green       0.160 0.475 0.130 0.513
11 Blue             0.177 0.340 0.133 0.427
11 Sky              0.179 0.438 0.146 0.482
11 Purple           0.245 0.366 0.216 0.419
12 Illuminant       0.205 0.482 0.174 0.519
12 Gray             0.208 0.482 0.181 0.507
12 Red              0.451 0.512 0.422 0.526
12 Skin             0.268 0.506 0.244 0.525
12 Orange           0.331 0.548 0.292 0.553
12 Brown            0.324 0.542 0.286 0.554
12 Yellow           0.266 0.548 0.238 0.558
12 Foliage          0.227 0.538 0.196 0.555
12 Green            0.145 0.534 0.124 0.551
12 Blue-green       0.160 0.474 0.135 0.505
12 Blue             0.178 0.339 0.149 0.392
12 Sky              0.179 0.440 0.150 0.473
12 Purple           0.246 0.366 0.222 0.404
"""



def text_runs(d, center, runs, fill=INK):
    """居中画一行由几段组成的文字；每段为 (文字, 字体, 上移量)。
    字体里没有 ²，单位 cd/m² 的平方用小号的 2 上移代替。"""
    w = sum(d.textlength(s, font=f) for s, f, _ in runs) / SS
    x, y = center[0] - w / 2, center[1]
    for s, f, up in runs:
        text(d, (x, y - up), s, f, fill=fill, anchor="lm")
        x += d.textlength(s, font=f) / SS


def _rows(block):
    return [ln.split() for ln in block.strip().splitlines() if ln.strip()]


def nikon():
    a = np.array([[float(v) for v in r] for r in _rows(NIKON_D5100)])
    return a[:, 0], a[:, 1:]


def breneman():
    """{实验号: (白点 u'v' 测试, 白点 u'v' 参照, [(名称, uv_t, uv_m), ...])}"""
    out = {}
    for k, name, ut, vt, um, vm in _rows(BRENEMAN):
        k = int(k)
        rec = (name.replace("_", " "), np.array([float(ut), float(vt)]), np.array([float(um), float(vm)]))
        if name == "Illuminant":
            out[k] = (rec[1], rec[2], [])
        else:
            out[k][2].append(rec)
    return out


# ---------------------------------------------------------------- 色度换算
def xy_to_XYZ(x, y):
    return np.array([x / y, 1.0, (1 - x - y) / y])


def upvp_to_XYZ(uv):
    return xy_to_XYZ(*upvp_to_xy(*uv))


def XYZ_to_upvp(X):
    s = X[0] + 15 * X[1] + 3 * X[2]
    return np.array([4 * X[0] / s, 9 * X[1] / s])


def adapt_matrix(XYZ_w1, XYZ_w2, M=M_BFD, D=1.0):
    """von Kries 型色适应：M^-1 · diag(g) · M，g = D·(w2/w1) + (1 - D)"""
    g = D * (M @ XYZ_w2) / (M @ XYZ_w1) + (1 - D)
    return np.linalg.inv(M) @ np.diag(g) @ M


def breneman_error(M, D=1.0, data=None):
    """全部色样（或 data 中给定的几组实验）的平均 Δu'v'"""
    data = data or breneman()
    errs = []
    for wt, wm, samples in data.values():
        B = adapt_matrix(upvp_to_XYZ(wt), upvp_to_XYZ(wm), M, D)
        for _, ut, um in samples:
            errs.append(np.linalg.norm(XYZ_to_upvp(B @ upvp_to_XYZ(ut)) - um))
    return float(np.mean(errs)), len(errs)


def best_D(M=M_BFD, data=None):
    """黄金分割搜索 [0, 1] 内使平均误差最小的 D"""
    data = data or breneman()
    lo, hi = 0.0, 1.0
    r = (math.sqrt(5) - 1) / 2
    for _ in range(60):
        a, b = hi - r * (hi - lo), lo + r * (hi - lo)
        if breneman_error(M, a, data)[0] < breneman_error(M, b, data)[0]:
            hi = b
        else:
            lo = a
    D = (lo + hi) / 2
    return D, breneman_error(M, D, data)[0]



# ---------------------------------------------------------------- Luther：相机 vs 等色函数
def luther_fit():
    """在 400～700 nm 上用最小二乘求把相机灵敏度变换到等色函数的 3×3 矩阵"""
    wl, cam = nikon()
    cmf = np.array([cmf_at(w) for w in wl])
    m = (wl >= 400) & (wl <= 700)
    T, *_ = np.linalg.lstsq(cam[m], cmf[m], rcond=None)
    fit = cam @ T
    resid = np.linalg.norm(fit[m] - cmf[m]) / np.linalg.norm(cmf[m])
    return wl, cam, cmf, fit, resid


# ---------------------------------------------------------------- 适应空间的光谱灵敏度
def space_sensitivities(M, wl0=380, wl1=720):
    m = (WL_CMF >= wl0) & (WL_CMF <= wl1)
    s = CMF[m] @ M.T
    return WL_CMF[m], s / s.max(axis=0)


def sens_stats(wl, s):
    out = []
    for i in range(3):
        c = s[:, i]
        half = wl[c >= 0.5]
        out.append((wl[c.argmax()], half.max() - half.min(), c.min(), wl[c.argmin()]))
    return out


# ==========================================================================
# 图 1：各种「白」在 xy 色度图上的位置
# ==========================================================================
def fig_white_points(out):
    W, H = 920, 640
    im, d = canvas(W, H)
    fx = font(13)
    fs = font(12)
    fb = font(14, bold=True)
    xr, yr = (0.27, 0.49), (0.28, 0.44)
    box = (80, 50, 900, 586)
    ax = Axes(d, box, xr, yr)
    xt = [0.28, 0.30, 0.32, 0.34, 0.36, 0.38, 0.40, 0.42, 0.44, 0.46, 0.48]
    yt = [0.28, 0.30, 0.32, 0.34, 0.36, 0.38, 0.40, 0.42, 0.44]
    ax.frame(xt, yt, fx, xfmt="%.2f", yfmt="%.2f")
    w, h = int((box[2] - box[0]) * SS), int((box[3] - box[1]) * SS)
    locus = [(x, y) for _, x, y in spectral_locus(1)]
    img = diagram_image(w, h, xr, yr, lambda i, j: (i, j), locus)
    im.paste(img, (int(box[0] * SS), int(box[1] * SS)), img)
    lighten(im, box, 150)
    ax.grid(xt, yt)
    # 黑体轨迹
    Ts = np.exp(np.linspace(math.log(2200), math.log(20000), 300))
    clipped_polyline(d, ax, [bb_xy(T) for T in Ts], INK, 2.0)
    for T in (2500, 3000, 4000, 5000, 6500, 10000):
        px, py = ax.px(*bb_xy(T))
        ellipse(d, (px - 3, py - 3, px + 3, py + 3), fill=WHITE, outline=INK, width=1.4)
        if T == 2500:
            text(d, (px - 4, py + 8), "%d K" % T, fs, fill=MUTED, anchor="rt")
        else:
            text(d, (px + 4, py + 8), "%d K" % T, fs, fill=MUTED, anchor="lt")
    px, py = ax.px(*bb_xy(3500))
    text(d, (px - 10, py - 12), "黑体轨迹", fb, fill=INK, anchor="rb")

    def dot(name, col):
        px, py = ax.px(*WHITES[name])
        ellipse(d, (px - 6, py - 6, px + 6, py + 6), fill=col, outline=WHITE, width=1.5)
        return px, py

    p = dot("D65", CURVE)
    callout(d, (170, 478, 430, 554), "D65（约 6500 K 日光）\nsRGB、Rec. 709、Rec. 2020、\nAdobe RGB、Display P3", fs,
            text_fill=CURVE, tail=p)
    p = dot("E", MUTED)
    callout(d, (420, 372, 640, 428), "等能白 E\nCIE XYZ 的中性点（X = Y = Z）", fs, text_fill=INK, tail=p)
    p = dot("DCI", GREEN)
    callout(d, (96, 196, 320, 252), "DCI 白\nDCI-P3（数字影院放映）", fs, text_fill=GREEN, tail=p)
    p = dot("D50", ACCENT)
    callout(d, (330, 66, 590, 142), "D50（约 5000 K 日光）\nICC 的 PCS、ProPhoto RGB、\n印刷品看样（ISO 3664）", fs,
            text_fill=ACCENT, tail=p)
    p = dot("A", ORANGE)
    callout(d, (640, 470, 880, 526), "标准照明体 A（约 2856 K）\n白炽灯；拍摄时的场景光之一", fs,
            text_fill=ORANGE, tail=p)
    text(d, ((box[0] + box[2]) / 2, 618), "x", ifont(18))
    text(d, (36, 50), "y", ifont(18))
    text(d, (W / 2, 24), "各种「白」在 xy 色度图上的位置（局部）", fx)
    finish(im, os.path.join(out, "white-points-xy.png"))


# ==========================================================================
# 图 2：Luther 条件：相机灵敏度与等色函数
# ==========================================================================
def fig_luther(out):
    wl, cam, cmf, fit, resid = luther_fit()
    W, H = 960, 490
    im, d = canvas(W, H)
    fx = font(13)
    fs = font(12)
    cols = (RED, GREEN, BLUE)
    # 左：相机原始灵敏度
    axl = Axes(d, (70, 60, 450, 370), (380, 720), (0, 1.05))
    axl.frame(list(range(400, 721, 50)), [0, 0.2, 0.4, 0.6, 0.8, 1.0], fx, yfmt="%.1f")
    for i, c in enumerate(cols):
        axl.plot(wl[wl <= 720], cam[wl <= 720, i], fill=c, width=2.4)
    spectrum_strip(d, (70, 404, 450, 414), 380, 720)
    text(d, (260, 440), "波长 (nm)", fx)
    text(d, (260, 34), "Nikon D5100 的光谱灵敏度（各通道峰值归一）", fx)
    for i, (lab, x, y) in enumerate((("R", 610, 0.80), ("G", 535, 1.0), ("B", 455, 0.92))):
        px, py = axl.px(x, y)
        text(d, (px + 16, py - 6), lab, font(14, bold=True), fill=cols[i])
    # 右：最优 3×3 变换后与等色函数
    axr = Axes(d, (550, 60, 930, 370), (380, 720), (0, 2.0))
    axr.frame(list(range(400, 721, 50)), [0, 0.5, 1.0, 1.5, 2.0], fx, yfmt="%.1f")
    m = (WL_CMF >= 380) & (WL_CMF <= 720)
    for i, c in enumerate(cols):
        axr.plot(WL_CMF[m], CMF[m, i], fill=c, width=2.4)
    mm = wl <= 720
    for i, c in enumerate(cols):
        pts = [axr.px(x, y) for x, y in zip(wl[mm], fit[mm, i])]
        for a, b in zip(pts[:-1], pts[1:]):
            dashed(d, a, b, fill=tuple(int(v * 0.7) for v in c), width=1.8, dash=4, gap=3)
    spectrum_strip(d, (550, 404, 930, 414), 380, 720)
    text(d, (740, 440), "波长 (nm)", fx)
    text(d, (740, 34), "实线：CIE 1931 等色函数　虚线：相机灵敏度经最优 3×3 变换", fx)
    callout(d, (735, 118, 925, 174), "400～700 nm 内\n相对残差约 %d%%" % round(resid * 100), fs, tail=axr.px(600, 1.06))
    finish(im, os.path.join(out, "luther-camera-vs-cmf.png"))


# ==========================================================================
# 共用：流程图的方框与箭头
# ==========================================================================
def _node(d, box, title, sub, fb, fs, fill=PANEL, outline=BORDER, title_fill=INK):
    rect(d, box, fill=fill, outline=outline, width=1.4, radius=8)
    x0, y0, x1, y1 = box
    cx = (x0 + x1) / 2
    lines = sub.split("\n") if sub else []
    th = 20 + 17 * len(lines)
    cy = (y0 + y1) / 2 - th / 2 + 9
    text(d, (cx, cy), title, fb, fill=title_fill)
    for i, ln in enumerate(lines):
        text(d, (cx, cy + 22 + 17 * i), ln, fs, fill=MUTED)


def _harrow(d, x0, x1, y, label=None, f=None, fill=INK):
    arrow(d, (x0, y), (x1, y), fill=fill, width=2, head=9)
    if label:
        text(d, ((x0 + x1) / 2, y - 12), label, f, fill=fill)


# ==========================================================================
# 图 3：从传感器到 sRGB 的色彩链路（模式图）
# ==========================================================================
def fig_isp_chain(out):
    W, H = 980, 330
    im, d = canvas(W, H)
    fb = font(14, bold=True)
    fs = font(12)
    fx = font(13)
    y0, y1 = 70, 170
    boxes = [(20, "传感器 RAW", "各通道 = 滤光片后的光量\n设备相关，没有白点"),
             (215, "白平衡", "三个通道各乘一个增益\n使中性色 R = G = B"),
             (410, "色彩校正矩阵", "3×3，换算到标准空间\n只能近似（Luther 条件）"),
             (605, "线性 sRGB", "标准色彩空间\n白点 D65"),
             (800, "传递函数", "伽马编码\n→ sRGB 输出")]
    bw = 160
    for i, (x, t, s) in enumerate(boxes):
        hl = i in (1, 2)
        _node(d, (x, y0, x + bw, y1), t, s, fb, fs,
              fill=(252, 244, 236) if hl else PANEL, outline=(226, 190, 160) if hl else BORDER)
        if i < len(boxes) - 1:
            _harrow(d, x + bw + 4, boxes[i + 1][0] - 4, (y0 + y1) / 2)
    # 下方：所在的空间
    yb = 214
    rect(d, (20, yb, 570, yb + 34), fill=(244, 244, 248), outline=BORDER, radius=6)
    text(d, (295, yb + 17), "相机自己的 RGB（设备相关，各家、各机型不同）", fx, fill=MUTED)
    rect(d, (605, yb, 960, yb + 34), fill=(236, 240, 252), outline=(190, 200, 230), radius=6)
    text(d, (782, yb + 17), "标准色彩空间 sRGB（设备无关，D65）", fx, fill=CURVE)
    text(d, (W / 2, 286), "白平衡相当于在传感器空间里做的 von Kries 式缩放；色彩校正矩阵在保持中性色的前提下完成其余换算",
         fs, fill=INK)
    text(d, (W / 2, 30), "模式图：相机内部从传感器 RAW 到 sRGB 的色彩链路（省略降噪、去马赛克等与颜色换算无关的步骤）", fx)
    finish(im, os.path.join(out, "isp-color-chain.png"))


# ==========================================================================
# 图 4：DNG 与 ICC 中的两次白点切换（模式图）
# ==========================================================================
def fig_white_switch(out):
    W, H = 980, 340
    im, d = canvas(W, H)
    fb = font(14, bold=True)
    fs = font(12)
    fx = font(13)
    y0, y1 = 110, 196
    bw = 130
    nodes = [(20, "相机 RAW", "场景白点"),
             (255, "XYZ", "场景白点"),
             (490, "PCS（XYZ）", "白点 D50"),
             (830, "sRGB", "白点 D65")]
    for x, t, s in nodes:
        _node(d, (x, y0, x + bw, y1), t, s, fb, fs)
    yc = (y0 + y1) / 2
    ops = [(20 + bw, 255, "相机矩阵", "按色温插值", INK),
           (255 + bw, 490, "Bradford", "场景白 → D50", ACCENT),
           (490 + bw, 830, "Bradford", "D50 → D65\n再换算为 sRGB", ACCENT)]
    for xa, xb, t, s, col in ops:
        arrow(d, (xa + 6, yc), (xb - 6, yc), fill=col, width=2.2, head=10)
        text(d, ((xa + xb) / 2, yc - 16), t, font(13, bold=True), fill=col)
        for k, ln in enumerate(s.split("\n")):
            text(d, ((xa + xb) / 2, yc + 18 + 17 * k), ln, fs, fill=col)
    # 上方括号：DNG / ICC
    def bracket(xa, xb, y, label, col):
        line(d, (xa, y + 10, xa, y, xb, y, xb, y + 10), fill=col, width=1.6)
        text(d, ((xa + xb) / 2, y - 14), label, fx, fill=col)
    bracket(20, 620, 70, "DNG 处理：把相机的颜色送进 PCS", INK)
    bracket(490, 960, 250, "", MUTED)
    text(d, (725, 276), "ICC 色彩管理：从 PCS 输出到 sRGB 显示器", fx, fill=MUTED)
    text(d, (W / 2, 312), "橙色箭头即白点切换：一张 DNG 照片显示到 sRGB 屏幕上，至少要切换两次白点", fs, fill=ACCENT)
    text(d, (W / 2, 26), "模式图：DNG 与 ICC 色彩管理中的白点切换", fx)
    finish(im, os.path.join(out, "white-switch-flow.png"))


# ==========================================================================
# 图 5：Bradford 空间与视锥 LMS 的光谱灵敏度
# ==========================================================================
def fig_bradford_vs_lms(out):
    W, H = 940, 520
    im, d = canvas(W, H)
    fx = font(13)
    fs = font(12)
    wl, sb = space_sensitivities(M_BFD)
    _, sl = space_sensitivities(M_HPE)
    ax = Axes(d, (80, 60, 900, 410), (380, 720), (-0.25, 1.05))
    ax.frame(list(range(400, 721, 20)), [-0.2, 0, 0.2, 0.4, 0.6, 0.8, 1.0], fx, yfmt="%.1f")
    text(d, (80, 50), "相对灵敏度（各通道峰值 = 1）", fs, fill=INK, anchor="lb")
    x0, _ = ax.px(380, 0)
    x1, yz = ax.px(720, 0)
    line(d, (x0, yz, x1, yz), fill=MUTED, width=1.4)
    cols = (RED, GREEN, BLUE)
    for i, c in enumerate(cols):
        pts = [ax.px(x, y) for x, y in zip(wl, sl[:, i])]
        for a, b in zip(pts[:-1:3], pts[3::3]):
            dashed(d, a, b, fill=c, width=1.6, dash=5, gap=4)
        ax.plot(wl, sb[:, i], fill=c, width=2.6)
    spectrum_strip(d, (80, 436, 900, 448), 380, 720)
    text(d, (490, 470), "波长 (nm)", fx)
    # 图例
    lx, ly = 640, 92
    line(d, (lx, ly, lx + 34, ly), fill=INK, width=2.6)
    text(d, (lx + 44, ly), "Bradford 空间 R、G、B", fs, anchor="lm")
    dashed(d, (lx, ly + 24), (lx + 34, ly + 24), fill=INK, width=1.6, dash=5, gap=4)
    text(d, (lx + 44, ly + 24), "视锥 L、M、S（HPE）", fs, anchor="lm")
    st = sens_stats(wl, sb)
    gmin_wl = st[1][3]
    callout(d, (300, 368, 760, 398), "Bradford 的 G 通道在 %d nm 附近降到 %.2f：真实的传感器不可能有负的灵敏度"
            % (gmin_wl, st[1][2]), fs, tail=ax.px(gmin_wl, st[1][2]))
    text(d, (W / 2, 28), "Bradford 空间三个通道与视锥 LMS 的光谱灵敏度（由 CIE 1931 等色函数算出）", fx)
    finish(im, os.path.join(out, "bradford-vs-lms.png"))


# ==========================================================================
# 附录图：Breneman 对应色实验的检验
# ==========================================================================
def fig_breneman(out):
    data = breneman()
    W, H = 1000, 560
    im, d = canvas(W, H)
    fx = font(13)
    fs = font(12)
    # ---- 左：实验 1（A → D65）的实测与预测
    ir, jr = (0.10, 0.48), (0.30, 0.58)
    box = (70, 60, 560, 440)
    ax = Axes(d, box, ir, jr)
    xt = [0.15, 0.20, 0.25, 0.30, 0.35, 0.40, 0.45]
    yt = [0.30, 0.34, 0.38, 0.42, 0.46, 0.50, 0.54, 0.58]
    ax.frame(xt, yt, fx, xfmt="%.2f", yfmt="%.2f")
    w, h = int((box[2] - box[0]) * SS), int((box[3] - box[1]) * SS)
    loc = [xy_to_upvp(x, y) for _, x, y in spectral_locus(1)]
    img = diagram_image(w, h, ir, jr, upvp_to_xy, loc)
    im.paste(img, (int(box[0] * SS), int(box[1] * SS)), img)
    lighten(im, box, 170)
    ax.grid(xt, yt)
    wt, wm, samples = data[1]
    Bx = adapt_matrix(upvp_to_XYZ(wt), upvp_to_XYZ(wm), np.eye(3))
    Bb = adapt_matrix(upvp_to_XYZ(wt), upvp_to_XYZ(wm), M_BFD)
    for _, ut, um in samples:
        pm = ax.px(*um)
        for B, col in ((Bx, ORANGE), (Bb, CURVE)):
            pp = ax.px(*XYZ_to_upvp(B @ upvp_to_XYZ(ut)))
            line(d, (pm[0], pm[1], pp[0], pp[1]), fill=col, width=1.4)
            ellipse(d, (pp[0] - 4, pp[1] - 4, pp[0] + 4, pp[1] + 4), fill=WHITE, outline=col, width=1.8)
        ellipse(d, (pm[0] - 4.5, pm[1] - 4.5, pm[0] + 4.5, pm[1] + 4.5), fill=INK)
    for uv, lab in ((wt, "A 的白"), (wm, "D65 的白")):
        px, py = ax.px(*uv)
        poly(d, [(px, py - 8), (px + 8, py), (px, py + 8), (px - 8, py)], fill=WHITE, outline=INK, width=1.6)
        text(d, (px + 10, py + 10), lab, fs, anchor="lt")
    lx, ly = 90, 500
    ellipse(d, (lx - 4.5, ly - 4.5, lx + 4.5, ly + 4.5), fill=INK)
    text(d, (lx + 12, ly), "实测对应色（D65 下）", fs, anchor="lm")
    ellipse(d, (lx + 176, ly - 4, lx + 184, ly + 4), fill=WHITE, outline=ORANGE, width=1.8)
    text(d, (lx + 192, ly), "XYZ 直接缩放的预测", fs, fill=ORANGE, anchor="lm")
    ellipse(d, (lx + 346, ly - 4, lx + 354, ly + 4), fill=WHITE, outline=CURVE, width=1.8)
    text(d, (lx + 362, ly), "Bradford 的预测", fs, fill=CURVE, anchor="lm")
    text(d, (lx - 6, ly + 26), "连线长度即预测误差。", fs, fill=MUTED, anchor="lm")
    text_runs(d, ((box[0] + box[2]) / 2, 30),
              [("实验 1（A → D65，1500 cd/m", fx, 0), ("2", font(9), 4), ("，12 个色样）", fx, 0)])
    text(d, ((box[0] + box[2]) / 2, 476), "u'", ifont(17))
    text(d, (36, 42), "v'", ifont(17))
    # ---- 右：9 组实验的平均误差
    D, eD = best_D(M_BFD)
    bars = [("XYZ\n直接缩放", breneman_error(np.eye(3))[0], ORANGE),
            ("LMS\n(HPE)", breneman_error(M_HPE)[0], MUTED),
            ("Bradford", breneman_error(M_BFD)[0], CURVE),
            ("CAT02", breneman_error(M_CAT02)[0], GREEN),
            ("Bradford\nD = %.2f" % D, eD, (120, 90, 170))]
    bx = Axes(d, (650, 60, 970, 440), (0, len(bars)), (0, 0.032))
    bx.frame([], [0, 0.005, 0.010, 0.015, 0.020, 0.025, 0.030], fx, yfmt="%.3f", grid=True)
    for i, (lab, v, col) in enumerate(bars):
        xa, ya = bx.px(i + 0.18, v)
        xb, yb = bx.px(i + 0.82, 0)
        rect(d, (xa, ya, xb, yb), fill=col)
        text(d, ((xa + xb) / 2, ya - 6), "%.4f" % v, fs, anchor="mb")
        for k, ln in enumerate(lab.split("\n")):
            text(d, ((xa + xb) / 2, 452 + 16 * k), ln, fs, anchor="mt")
    text(d, (810, 30), "9 组实验、115 个色样的平均误差 Δu'v'", fx)
    text(d, (810, 510), "前四项均按完全适应（D = 1）计算", fs, fill=MUTED)
    finish(im, os.path.join(out, "breneman-prediction.png"))


FIGURES = {
    "white-points": fig_white_points,
    "luther": fig_luther,
    "isp-chain": fig_isp_chain,
    "white-switch": fig_white_switch,
    "bradford-vs-lms": fig_bradford_vs_lms,
    "breneman": fig_breneman,
}


def check():
    np.set_printoptions(precision=4, suppress=True)
    *_, resid = luther_fit()
    print("Luther：Nikon D5100 最优 3×3 的相对残差（400～700 nm）= %.3f" % resid)
    for name, M in (("HPE", M_HPE), ("Bradford", M_BFD)):
        wl, s = space_sensitivities(M)
        for ch, (pk, fw, mn, mnwl) in zip("123", sens_stats(wl, s)):
            print("  %-8s 通道%s 峰值 %d nm  半高宽 %d nm  最小值 %+.3f（%d nm）" % (name, ch, pk, fw, mn, mnwl))
    B = adapt_matrix(xy_to_XYZ(*WHITES["D65"]), xy_to_XYZ(*WHITES["D50"]))
    print("D65 → D50:\n", B, "\n  sRGB D50 矩阵:\n", B @ M_SRGB_D65)
    data = breneman()
    print("Breneman：%d 组实验，%d 个色样" % (len(data), sum(len(v[2]) for v in data.values())))
    for name, M in (("XYZ", np.eye(3)), ("HPE", M_HPE), ("Bradford", M_BFD), ("CAT02", M_CAT02)):
        print("  %-9s Δu'v' = %.4f" % (name, breneman_error(M)[0]))
    D, e = best_D()
    print("  Bradford 最优 D = %.3f  Δu'v' = %.4f" % (D, e))

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", nargs="*", help="只生成这些图")
    ap.add_argument("--out", default="assets/resource/Chromatic-Adaptation")
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
