#!/usr/bin/env python3
"""生成《色温的刻度：倒数色温》一文的插图。

依赖 Pillow 与 numpy；绘图工具与 CIE 1931 数据从同目录的
generate_cie_xyz_figures.py 导入，uv 变换与色度图填色从
generate_uniform_color_space_figures.py 导入，黑体轨迹与相关色温的
计算从 generate_color_temperature_figures.py 导入。

用法：
    python3 tools/generate_reciprocal_color_temperature_figures.py              # 全部
    python3 tools/generate_reciprocal_color_temperature_figures.py --only scale
    python3 tools/generate_reciprocal_color_temperature_figures.py --check      # 打印正文引用的数值

图里的数据：
    - 黑体辐射：普朗克公式，常数取 2019 年 SI 定义值（同《照明光的色味》一文）
    - 色度：普朗克光谱对 CIE 1931 2° 等色函数（1 nm）积分；
      uv 为 CIE 1960 UCS，u'v' 为 CIE 1976 UCS（v' = 1.5 v）
    - 转换滤镜：理想化的滤镜 τ(λ) = exp(-c2·ΔM·1e-6 / λ)，
      在维恩近似下恰好把倒数色温平移 ΔM；c2 = hc/k
    - Robertson 法：等色温线表的倒数色温取 Robertson (1968) 的 31 个值，
      表中各行的 u、v 与等色温线斜率由普朗克公式重新算出
"""

import argparse
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from generate_cie_xyz_figures import (  # noqa: E402
    SS, WHITE, PANEL, GRID, BORDER, INK, MUTED, CURVE, ACCENT, RED, GREEN, BLUE,
    spectral_locus, font, ifont, canvas, finish, text, rect, line, polyline, poly,
    ellipse, arrow, dashed, callout, Axes, spectrum_strip,
)
from generate_uniform_color_space_figures import (  # noqa: E402
    xy_to_uv, uv_to_xy, diagram_image, lighten,
)
from generate_color_temperature_figures import (  # noqa: E402
    H_PLANCK, C_LIGHT, K_BOLTZ, _WL, _CMF, planck, bb_uv, isotherm_normal, cct_duv,
    clipped_polyline, clip_segment,
)

C2 = H_PLANCK * C_LIGHT / K_BOLTZ          # 第二辐射常数 c2 = hc/k，单位 m·K
ORANGE = (214, 130, 40)

# Robertson (1968) 等色温线表所取的倒数色温（mired）
ROBERTSON_M = (0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 125, 150, 175, 200, 225, 250, 275, 300,
               325, 350, 375, 400, 425, 450, 475, 500, 525, 550, 575, 600)

T_A, T_D65 = 2856.0, 6504.0


# ---------------------------------------------------------------- 计算
def mired(T):
    return 1e6 / T


def kelvin(M):
    return 1e6 / M if M > 0 else 1e9


def spd_uv(L):
    """光谱（与 _WL 对齐）→ CIE 1960 uv。"""
    X, Y, Z = (_CMF * L[:, None]).sum(axis=0)
    s = X + Y + Z
    return xy_to_uv(X / s, Y / s)


def filter_tau(wl_nm, dM):
    """理想化的转换滤镜：维恩近似下把倒数色温平移 dM（mired）。"""
    return np.exp(-C2 * dM * 1e-6 / (np.asarray(wl_nm, dtype=float) * 1e-9))


def filtered(T, dM):
    """色温 T 的黑体光透过 dM 滤镜之后的相关色温与 duv。"""
    u, v = spd_uv(planck(_WL, T) * filter_tau(_WL, dM))
    return cct_duv(u, v)


def step_uv(T, dT=None, dM=None, prime=False):
    """黑体轨迹上，从 T 出发升温 dT（K）或倒数色温降低 dM（mired）走过的色度距离。"""
    T2 = T + dT if dT is not None else kelvin(mired(T) - dM)
    a, b = np.array(bb_uv(T)), np.array(bb_uv(T2))
    if prime:
        a, b = a * (1, 1.5), b * (1, 1.5)
    return float(np.linalg.norm(b - a))


def robertson_table():
    """[(M, u, v, t)]：t 为等色温线在 uv 图上的斜率 dv/du（与轨迹正交）。"""
    rows = []
    for M in ROBERTSON_M:
        T = kelvin(M)
        u, v = bb_uv(T)
        a, b = np.array(bb_uv(T * 0.999)), np.array(bb_uv(T * 1.001))
        du, dv = b - a
        rows.append((M, u, v, -du / dv))
    return rows


def robertson(u, v, table, in_mired=True):
    """Robertson 法求相关色温：按到相邻两条等色温线的距离插值。"""
    ds = [((v - vi) - ti * (u - ui)) / math.sqrt(1 + ti * ti) for _, ui, vi, ti in table]
    for i in range(len(table) - 1):
        if ds[i] * ds[i + 1] <= 0 and ds[i] != ds[i + 1]:
            f = ds[i] / (ds[i] - ds[i + 1])
            M0, M1 = table[i][0], table[i + 1][0]
            if in_mired:
                return kelvin(M0 + f * (M1 - M0))
            T0, T1 = kelvin(M0), kelvin(M1)
            return T0 + f * (T1 - T0)
    return None


# ---------------------------------------------------------------- 作图小工具
def uv_panel(d, im, box, ir, jr, fx, step=0.02, fmt="%.2f", tint=150):
    """局部的 uv 色度图：填色底 + 坐标框。"""
    ax = Axes(d, box, ir, jr)
    xt = [round(ir[0] + k * step, 4) for k in range(int(round((ir[1] - ir[0]) / step)) + 1)]
    yt = [round(jr[0] + k * step, 4) for k in range(int(round((jr[1] - jr[0]) / step)) + 1)]
    ax.frame(xt, yt, fx, xfmt=fmt, yfmt=fmt)
    loc = [xy_to_uv(x, y) for _, x, y in spectral_locus(1)]
    w, h = int((box[2] - box[0]) * SS), int((box[3] - box[1]) * SS)
    img = diagram_image(w, h, ir, jr, uv_to_xy, loc)
    im.paste(img, (int(box[0] * SS), int(box[1] * SS)), img)
    lighten(im, box, tint)
    ax.grid(xt, yt)
    return ax


def locus_pts(T0, T1, n=300):
    return [bb_uv(T) for T in np.exp(np.linspace(math.log(T0), math.log(T1), n))]


def pix_normal(T):
    """黑体轨迹在 T 处朝绿色一侧的单位法向量，换成像素方向（y 向下）。"""
    nx, ny = isotherm_normal(T)
    return nx, -ny


# ==========================================================================
# 图 1：黑体轨迹上的两种刻度
# ==========================================================================

def fig_scale(out):
    W, H = 900, 720
    im, d = canvas(W, H)
    fx, fs = font(13), font(12)
    ir, jr = (0.17, 0.33), (0.25, 0.37)
    box = (90, 50, 850, 620)
    ax = uv_panel(d, im, box, ir, jr, fx)
    clipped_polyline(d, ax, locus_pts(1800, 1e6), INK, 2.4)

    # 上侧（绿色一侧）：每 1000 K 一个刻度
    for T in range(2000, 20001, 1000):
        px, py = ax.px(*bb_uv(T))
        nx, ny = pix_normal(T)
        line(d, (px, py, px + nx * 11, py + ny * 11), fill=ACCENT, width=1.8)
        if T in (2000, 3000, 4000, 5000, 6000, 8000, 10000, 20000):
            lab = "%d K" % T
            text(d, (px + nx * 18, py + ny * 18), lab, fs, fill=ACCENT,
                 anchor="lb" if T <= 3000 else ("mb" if T <= 5000 else "rb"))
    # 下侧（红紫一侧）：每 25 mired 一个刻度
    for M in range(500, -1, -25):
        px, py = ax.px(*bb_uv(kelvin(M)))
        nx, ny = pix_normal(kelvin(M))
        line(d, (px, py, px - nx * 11, py - ny * 11), fill=CURVE, width=1.8)
        if M % 100 == 0:
            text(d, (px - nx * 18, py - ny * 18), "%d" % M, fs, fill=CURVE, anchor="mt" if M >= 300 else "lt")
    px, py = ax.px(*bb_uv(kelvin(0.5)))
    text(d, (px - 4, py + 22), "(T → ∞)", fs, fill=CURVE, anchor="rt")

    callout(d, (470, 470, 836, 544), "上侧（橙）：每 1000 K 一个刻度，色温越高越密，\n10000 K 以上几乎挤成一团。\n下侧（蓝）：每 25 mired 一个刻度，间距大致相等",
            fs)
    px, py = ax.px(*bb_uv(kelvin(8)))
    text(d, (px + 24, py + 4), "黑体轨迹", font(13, bold=True), anchor="lm")
    text(d, ((box[0] + box[2]) / 2, 650), "u", ifont(18))
    text(d, (36, 50), "v", ifont(18))
    text(d, (W / 2, 24), "CIE 1960 uv 色度图上黑体轨迹的两种刻度：开尔文与倒数色温（mired）", fx)
    text(d, (W / 2, 690), "下侧数字为倒数色温（mired）；色度由普朗克光谱对 CIE 1931 等色函数积分得到", fs, fill=MUTED)
    finish(im, os.path.join(out, "locus-scale-uv.png"))


# ==========================================================================
# 图 2：光谱的倾斜只取决于倒数色温之差
# ==========================================================================

def _ratio(wl, T1, T2):
    r = planck(wl, T2) / planck(wl, T1)
    return r / (planck(555.0, T2) / planck(555.0, T1))


def fig_tilt(out):
    W, H = 960, 550
    im, d = canvas(W, H)
    fx, fs = font(13), font(12)
    fb = font(13, bold=True)
    wl = np.linspace(380, 780, 401)
    panels = (
        ((80, 96, 455, 436), "色温各升高 500 K",
         ((2000, 2500, ACCENT), (6000, 6500, CURVE))),
        ((560, 96, 935, 436), "倒数色温各降低 100 mired",
         ((2000, 2500, ACCENT), (5000, 10000, CURVE))),
    )
    for box, title, pairs in panels:
        ax = Axes(d, box, (380, 780), (0, 3.0))
        ax.frame(list(range(380, 781, 80)), [0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0], fx, yfmt="%.1f",
                 xlabel="波长（nm）")
        text(d, ((box[0] + box[2]) / 2, box[1] - 18), title, fb)
        for k, (T1, T2, col) in enumerate(pairs):
            r = _ratio(wl, T1, T2)
            clipped_polyline(d, ax, list(zip(wl, r)), col, 2.6 if k == 0 else 2.2,
                             dash=None if k == 0 else (8, 5))
            lab = "%d → %d K（%d → %d mired）" % (T1, T2, round(mired(T1)), round(mired(T2)))
            lx, ly = box[2] - 250, box[1] + 22 + 22 * k
            if k == 0:
                line(d, (lx, ly, lx + 28, ly), fill=col, width=2.6)
            else:
                dashed(d, (lx, ly), (lx + 28, ly), fill=col, width=2.2, dash=8, gap=5)
            text(d, (lx + 36, ly), lab, fs, fill=col, anchor="lm")
        px, py = ax.px(555, 1.0)
        ellipse(d, (px - 3.5, py - 3.5, px + 3.5, py + 3.5), fill=INK)
        spectrum_strip(d, (box[0], box[3] + 4, box[2], box[3] + 14))
    text(d, (W / 2, 24), "升温前后的光谱之比 L(λ, 升温后) / L(λ, 升温前)，在 555 nm 处取 1", fx)
    text(d, (W / 2, 514), "左：同样升高 500 K，2000 K 处光谱的倾斜远大于 6000 K 处；右：倒数色温变化相同，倾斜几乎一样",
         fs, fill=MUTED)
    finish(im, os.path.join(out, "spectral-tilt.png"))


# ==========================================================================
# 图 3：转换滤镜
# ==========================================================================

FILTER_DM = -131
FILTER_SRC = (2000, 2856, 4000)


def fig_filter(out):
    W, H = 980, 590
    im, d = canvas(W, H)
    fx, fs = font(13), font(12)
    fb = font(13, bold=True)

    # 左：透射率
    box = (70, 96, 400, 456)
    ax = Axes(d, box, (380, 780), (0, 1.0))
    ax.frame(list(range(380, 781, 80)), [0, 0.2, 0.4, 0.6, 0.8, 1.0], fx, yfmt="%.1f", xlabel="波长（nm）")
    text(d, ((box[0] + box[2]) / 2, box[1] - 18), "理想化的转换滤镜的透射率", fb)
    wl = np.linspace(380, 780, 401)
    for k, (dM, col, lab) in enumerate(((-131, BLUE, "-131 mired（蓝，升色温）"),
                                        (131, ORANGE, "+131 mired（琥珀，降色温）"))):
        tau = filter_tau(wl, dM)
        tau = tau / tau.max()
        clipped_polyline(d, ax, list(zip(wl, tau)), col, 2.4)
        lx, ly = box[0] + 96, box[1] + 22 + 22 * k
        line(d, (lx, ly, lx + 28, ly), fill=col, width=2.4)
        text(d, (lx + 36, ly), lab, fs, fill=col, anchor="lm")
    spectrum_strip(d, (box[0], box[3] + 4, box[2], box[3] + 14))

    # 右：uv 图上的位移
    ir, jr = (0.18, 0.32), (0.26, 0.37)
    box = (480, 96, 942, 459)
    ax = uv_panel(d, im, box, ir, jr, fx)
    text(d, ((box[0] + box[2]) / 2, box[1] - 18), "同一块 -131 mired 滤镜，罩在三种光源上", fb)
    clipped_polyline(d, ax, locus_pts(1800, 1e6), INK, 2.0)
    for k, T in enumerate(FILTER_SRC):
        T2, _ = filtered(T, FILTER_DM)
        p0, p1 = ax.px(*bb_uv(T)), ax.px(*bb_uv(T2))
        ellipse(d, (p0[0] - 4, p0[1] - 4, p0[0] + 4, p0[1] + 4), fill=WHITE, outline=INK, width=1.5)
        nx, ny = pix_normal(math.sqrt(T * T2))
        off = 18 + 20 * (k % 2)
        a0 = (p0[0] - nx * off, p0[1] - ny * off)
        a1 = (p1[0] - nx * off, p1[1] - ny * off)
        dashed(d, p0, a0, fill=MUTED, width=1)
        dashed(d, p1, a1, fill=MUTED, width=1)
        arrow(d, a0, a1, fill=BLUE, width=2, head=9)
        ellipse(d, (p1[0] - 4, p1[1] - 4, p1[0] + 4, p1[1] + 4), fill=BLUE)
        mx, my = (a0[0] + a1[0]) / 2 - nx * 12, (a0[1] + a1[1]) / 2 - ny * 12
        text(d, (mx, my), "%d → %d K" % (T, round(T2, -1)), fs, fill=BLUE, anchor="lt")
    text(d, ((box[0] + box[2]) / 2, 489), "u", ifont(17))
    text(d, (box[0] - 40, box[1]), "v", ifont(17))
    text(d, (W / 2, 24), "色温转换滤镜：透射率与色度的位移", fx)
    text(d, (W / 2, 536), "三支箭头在 uv 图上的长度相近：开尔文的变化各不相同（+710、+1720、+4760 K），倒数色温的变化都在 -131 mired 左右",
         fs, fill=MUTED)
    text(d, (W / 2, 560), "透射率按最大值归一；理想化的滤镜 τ(λ) = exp(-c₂ ΔM / λ) 在维恩近似下恰好把倒数色温平移 ΔM".replace("₂", "2"),
         fs, fill=MUTED)
    finish(im, os.path.join(out, "conversion-filter.png"))


# ==========================================================================
# 图 4：Robertson 法
# ==========================================================================

def fig_robertson(out):
    W, H = 900, 680
    im, d = canvas(W, H)
    fx, fs = font(13), font(12)
    fb = font(13, bold=True)
    ir, jr = (0.21, 0.29), (0.30, 0.36)
    box = (90, 50, 850, 620)
    ax = uv_panel(d, im, box, ir, jr, fx, step=0.01, fmt="%.2f", tint=170)
    table = {r[0]: r for r in robertson_table()}
    clipped_polyline(d, ax, locus_pts(2000, 8000), INK, 2.4)
    L = 0.022
    for M in (250, 275, 300, 325, 350):
        _, u0, v0, t = table[M]
        n = math.hypot(1, t)
        a = (u0 - L / n, v0 - L * t / n)
        b = (u0 + L / n, v0 + L * t / n)
        seg = clip_segment(a, b, ir, jr)
        hi = 0 if seg[0][1] > seg[1][1] else 1
        p0, p1 = ax.px(*seg[0]), ax.px(*seg[1])
        col = ACCENT if M in (300, 325) else MUTED
        line(d, (p0[0], p0[1], p1[0], p1[1]), fill=col, width=2.0 if col == ACCENT else 1.4)
        pt = (p0, p1)[hi]
        text(d, (pt[0] + 4, pt[1] + 6), "%d mired" % M, fs, fill=col, anchor="lt")
        px, py = ax.px(u0, v0)
        ellipse(d, (px - 3.5, py - 3.5, px + 3.5, py + 3.5), fill=WHITE, outline=INK, width=1.5)

    # 待测色度点：倒数色温 310 mired、duv = +0.010
    Ts = kelvin(310)
    u0, v0 = bb_uv(Ts)
    nx, ny = isotherm_normal(Ts)
    us, vs = u0 + 0.010 * nx, v0 + 0.010 * ny
    ps = ax.px(us, vs)
    for M, lab in ((300, "d₁"), (325, "d₂")):
        _, ui, vi, t = table[M]
        # 垂足：点到直线 v - vi = t (u - ui)
        k = ((us - ui) + t * (vs - vi)) / (1 + t * t)
        fu, fv = ui + k, vi + k * t
        pf = ax.px(fu, fv)
        dashed(d, ps, pf, fill=INK, width=1.6, dash=6, gap=4)
        ellipse(d, (pf[0] - 2.5, pf[1] - 2.5, pf[0] + 2.5, pf[1] + 2.5), fill=INK)
        mx, my = (ps[0] + pf[0]) / 2, (ps[1] + pf[1]) / 2
        text(d, (mx, my - 8), lab.replace("₁", "1").replace("₂", "2"), ifont(17), anchor="mb")
    ellipse(d, (ps[0] - 6, ps[1] - 6, ps[0] + 6, ps[1] + 6), fill=BLUE, outline=WHITE, width=1.5)
    callout(d, (610, 196, 760, 228), "待测色度点", fb, text_fill=BLUE, tail=ps)

    px, py = ax.px(*bb_uv(kelvin(230)))
    text(d, (px + 6, py + 30), "黑体轨迹", fb, anchor="lt")
    callout(d, (470, 470, 830, 600),
            "表中预先列出一组等色温线：\n每行给出倒数色温、轨迹上的 u、v 与线的斜率。\n找到夹住待测点的两条线，\n按 d1 : d2 在倒数色温上线性插值",
            fs)
    text(d, ((box[0] + box[2]) / 2, 650), "u", ifont(18))
    text(d, (36, 50), "v", ifont(18))
    text(d, (W / 2, 24), "Robertson 法：在两条相邻等色温线之间，按距离在倒数色温上插值", fx)
    finish(im, os.path.join(out, "robertson.png"))


FIGURES = {
    "scale": fig_scale,
    "tilt": fig_tilt,
    "filter": fig_filter,
    "robertson": fig_robertson,
}


def check():
    print("黑体轨迹的间距（uv 与 u'v'）")
    print("   T(K)   mired  Δuv/100K  Δuv/10mired  5.5mired:Δuv  Δu'v'")
    for T in (2000, 2500, 2856, 3000, 4000, 5000, 6504, 8000, 10000, 15000, 20000):
        print("  %6d  %6.1f   %.5f    %.5f      %.4f    %.4f" % (
            T, mired(T), step_uv(T, dT=100), step_uv(T, dM=10), step_uv(T, dM=5.5), step_uv(T, dM=5.5, prime=True)))
    print("\n理想 -131 mired 滤镜")
    for T in (2000, 2856, 3200, 4000, 5000):
        T2, duv = filtered(T, FILTER_DM)
        print("  %5d K -> %7.0f K  ΔM = %6.1f  ΔT = %+6.0f K  duv = %+.4f" % (
            T, T2, mired(T2) - mired(T), T2 - T, duv))
    print("\nRobertson 法（表由普朗克公式重算）与逐点搜索的差")
    table = robertson_table()
    for in_m in (True, False):
        worst = (0, None)
        for T in np.exp(np.linspace(math.log(1700), math.log(25000), 60)):
            u0, v0 = bb_uv(T)
            nx, ny = isotherm_normal(T)
            for duv in (-0.02, -0.01, 0, 0.01, 0.02):
                u, v = u0 + nx * duv, v0 + ny * duv
                Tr, _ = cct_duv(u, v)
                e = robertson(u, v, table, in_m) - Tr
                if abs(e) > abs(worst[0]):
                    worst = (e, (round(T), duv, round(mired(Tr) - mired(Tr + e), 3)))
        print("  %s 插值：最大误差 %+.1f K（at T, duv, ΔM = %s）" % ("倒数色温" if in_m else "开尔文", *worst))
    print("\nA = %.1f mired, D65 = %.1f mired" % (mired(T_A), mired(T_D65)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", nargs="*", help="只生成这些图")
    ap.add_argument("--out", default="assets/resource/Reciprocal-Color-Temperature")
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
