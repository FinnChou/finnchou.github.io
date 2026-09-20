#!/usr/bin/env python3
"""重绘《Geometric Transform : 几何学变换与图像配准》的示意图。

原文（2013 年 CSDN）的四张示意图是分辨率很低的 JPEG 截图，这里按
What-is-Color / Fixed-Point-Arithmetic 那两批图的配色与版式重画。
实验结果图（旋转、倾斜、配准）仍沿用原文，未重跑。

配色约定沿用原文：输入图像 g(u,v) 的格子用蓝色，输出图像 f(x,y)
的格子用红色。

用法:
    python3 tools/generate_geometric_transform_figures.py            # 写入 assets/resource/Geometric-Transform/
    python3 tools/generate_geometric_transform_figures.py --out DIR  # 指定输出目录
"""

import argparse
import math
import os

from PIL import Image, ImageDraw, ImageFont

SS = 2                                   # 先按 2 倍画再缩回去，给直线补上抗锯齿

WHITE = (255, 255, 255)
INK = (40, 44, 52)
MUTED = (110, 118, 130)
RED = (214, 72, 72)
BLUE = (66, 122, 210)
RED_PALE = (231, 158, 158)
BLUE_PALE = (150, 182, 233)
DOT_FILL = (226, 232, 240)

FONT_PATH = "/System/Library/Fonts/Hiragino Sans GB.ttc"
FONT_FALLBACK = "/System/Library/Fonts/STHeiti Medium.ttc"
MATH_PATH = "/System/Library/Fonts/Supplemental/Times New Roman Italic.ttf"


def font(size, bold=False):
    path = FONT_PATH if os.path.exists(FONT_PATH) else FONT_FALLBACK
    try:
        return ImageFont.truetype(path, size * SS, index=2 if bold else 0)
    except OSError:
        return ImageFont.truetype(path, size * SS)


def mfont(size):
    """数学符号用衬线斜体，和正文里 MathJax 的观感接近。"""
    if os.path.exists(MATH_PATH):
        return ImageFont.truetype(MATH_PATH, size * SS)
    return font(size)


def canvas(w, h):
    im = Image.new("RGB", (w * SS, h * SS), WHITE)
    return im, ImageDraw.Draw(im)


def finish(im, path):
    out = im.resize((im.width // SS, im.height // SS), Image.LANCZOS)
    out.save(path)
    print("%s  %dx%d" % (path, out.width, out.height))


def text(d, xy, s, f, fill=INK, anchor="mm"):
    d.text((xy[0] * SS, xy[1] * SS), s, font=f, fill=fill, anchor=anchor)


def line(d, p0, p1, fill=INK, width=2):
    d.line([p0[0] * SS, p0[1] * SS, p1[0] * SS, p1[1] * SS],
           fill=fill, width=width * SS)


def dashed(d, p0, p1, fill=INK, width=2, dash=9, gap=7):
    dx, dy = p1[0] - p0[0], p1[1] - p0[1]
    length = math.hypot(dx, dy)
    if length < 1e-6:
        return
    ux, uy = dx / length, dy / length
    pos = 0.0
    while pos < length:
        end = min(pos + dash, length)
        line(d, (p0[0] + ux * pos, p0[1] + uy * pos),
             (p0[0] + ux * end, p0[1] + uy * end), fill=fill, width=width)
        pos = end + gap


def dot(d, p, r=7, outline=INK, fill=DOT_FILL, width=2, dashed_ring=False):
    box = [(p[0] - r) * SS, (p[1] - r) * SS, (p[0] + r) * SS, (p[1] + r) * SS]
    d.ellipse(box, fill=fill, outline=None if dashed_ring else outline,
              width=width * SS)
    if dashed_ring:
        # 虚线圆环：用短弧拼出来，表示「不在格点上」
        for a in range(0, 360, 40):
            d.arc(box, a, a + 22, fill=outline, width=width * SS)


def arrow(d, p0, p1, fill=INK, width=2, head=11):
    line(d, p0, p1, fill=fill, width=width)
    ang = math.atan2(p1[1] - p0[1], p1[0] - p0[0])
    for sign in (1, -1):
        a = ang + sign * math.radians(154)
        line(d, p1, (p1[0] + head * math.cos(a), p1[1] + head * math.sin(a)),
             fill=fill, width=width)



def sym(d, xy, letter, sub="", prime=False, color=INK, size=26, align="left"):
    """排一个像 A'₂ 这样的数学符号：主字母 + 上标撇 + 下标数字。"""
    fb, fs = mfont(size), mfont(int(size * 0.72))
    wb = d.textlength(letter, font=fb) / SS
    wp = (d.textlength("'", font=fb) / SS) if prime else 0.0
    ws = (d.textlength(sub, font=fs) / SS) if sub else 0.0
    total = wb + wp + ws
    x = xy[0] if align == "left" else xy[0] - total
    y = xy[1]
    d.text((x * SS, y * SS), letter, font=fb, fill=color, anchor="lm")
    if prime:
        d.text(((x + wb) * SS, (y - size * 0.30) * SS), "'", font=fb,
               fill=color, anchor="lm")
    if sub:
        d.text(((x + wb + wp) * SS, (y + size * 0.28) * SS), sub, font=fs,
               fill=color, anchor="lm")
    return total


def lattice(origin, eu, ev):
    """返回 (i, j) → 屏幕坐标 的取点函数。i、j 可以是小数。"""
    def at(i, j):
        return (origin[0] + i * eu[0] + j * ev[0],
                origin[1] + i * eu[1] + j * ev[1])
    return at


def draw_lattice(d, at, i_range, j_range, color, width=2, is_dashed=False,
                 lo=-0.42, hi=1.62):
    """画出格线：沿 u 方向 len(j_range) 条，沿 v 方向 len(i_range) 条。"""
    draw = dashed if is_dashed else line
    for j in j_range:
        draw(d, at(lo, j), at(hi, j), fill=color, width=width)
    for i in i_range:
        draw(d, at(i, lo), at(i, hi), fill=color, width=width)


# --------------------------------------------------------------------------
# 图 1：向前映射
# --------------------------------------------------------------------------
# 基向量是照着原图的点位反解出来的：A' 与 B 的相对位置、以及「离 B2 最近的
# 四个 A' 是 A'1 / A'2 / A'4 / A'5」这一点，都与原文一致。
EU = (186, -34)
EV = (-58, 165)
OFF = (-12, -8)
SPACING = 150
A5_IJ = (1.85, 1.45)
CORNERS = [(0, 0), (1, 0), (0, 1), (1, 1)]


def draw_f_panel(d, bx, by):
    """输出图像 f(x,y) 的正交红格，叠上变换过去的蓝色虚线格。"""
    fb = lattice((bx, by), (SPACING, 0), (0, SPACING))
    draw_lattice(d, fb, [0, 1], [0, 1], RED_PALE, width=2, lo=-0.38, hi=1.52)

    fa = lattice((bx + OFF[0], by + OFF[1]), EU, EV)
    draw_lattice(d, fa, [0, 1], [0, 1], BLUE_PALE, width=2, is_dashed=True,
                 lo=-0.38, hi=1.92)
    dashed(d, fa(1, 1), fa(*A5_IJ), fill=BLUE_PALE, width=2)

    for idx, (i, j) in enumerate(CORNERS):
        p = fb(i, j)
        hot = idx == 1
        dot(d, p, r=8, outline=RED if hot else MUTED,
            fill=RED if hot else DOT_FILL)
        sym(d, (p[0] + 16, p[1] + 26), "B", str(idx + 1))

    for idx, (i, j) in enumerate(CORNERS + [A5_IJ]):
        p = fa(i, j)
        hot = idx == 1
        dot(d, p, r=7, outline=BLUE, fill=BLUE if hot else WHITE,
            dashed_ring=not hot)
        # A'5 在最右侧，标签放右边才不会压到 B4
        if idx == 4:
            sym(d, (p[0] + 16, p[1] + 4), "A", "5", prime=True, color=BLUE)
        else:
            sym(d, (p[0] - 14, p[1] - 18), "A", str(idx + 1), prime=True,
                color=BLUE, align="right")
    return fb, fa


def fig_forward_mapping(out_dir):
    W, H = 1060, 440
    im, d = canvas(W, H)

    # 左：输入图像 g(u,v) 的正交蓝格
    gx, gy = 150, 108
    ga = lattice((gx, gy), (SPACING, 0), (0, SPACING))
    draw_lattice(d, ga, [0, 1], [0, 1], BLUE_PALE, width=2, lo=-0.38, hi=1.52)
    dashed(d, ga(1, 1), ga(*A5_IJ), fill=BLUE_PALE, width=2)

    for idx, (i, j) in enumerate(CORNERS + [A5_IJ]):
        p = ga(i, j)
        hot = idx == 1
        dot(d, p, r=8, outline=BLUE if hot else MUTED,
            fill=BLUE if hot else DOT_FILL)
        sym(d, (p[0] - 14, p[1] - 18), "A", str(idx + 1), align="right")
    text(d, (gx + SPACING / 2, gy + 276), "g(u, v)", mfont(28), fill=MUTED)

    arrow(d, (500, 186), (576, 186), fill=INK, width=3, head=13)

    # 右：输出图像 f(x,y)
    bx, by = 690, 108
    _, fa = draw_f_panel(d, bx, by)
    text(d, (bx + SPACING / 2, by + 276), "f(x, y)", mfont(28), fill=MUTED)

    # A'2 四舍五入到最近的格点 B2
    p_a, p_b = fa(1, 0), (bx + SPACING, by)
    ang = math.atan2(p_b[1] - p_a[1], p_b[0] - p_a[0])
    arrow(d, (p_a[0] + 12 * math.cos(ang), p_a[1] + 12 * math.sin(ang)),
          (p_b[0] - 13 * math.cos(ang), p_b[1] - 13 * math.sin(ang)),
          fill=BLUE, width=3, head=11)

    text(d, (W / 2, H - 26),
         "向前映射：遍历 g 的每个格点，算出它落到 f 上的位置，再四舍五入到最近的格点",
         font(23), fill=MUTED)
    finish(im, os.path.join(out_dir, "forward-mapping.png"))


# --------------------------------------------------------------------------
# 图 2：向前映射下，由最近的四个 A' 共同确定 B2
# --------------------------------------------------------------------------
def fig_forward_spread(out_dir):
    W, H = 860, 480
    im, d = canvas(W, H)
    bx, by = 330, 128
    fb, fa = draw_f_panel(d, bx, by)

    target = fb(1, 0)
    for i, j in [(0, 0), (1, 0), (1, 1), A5_IJ]:
        p = fa(i, j)
        ang = math.atan2(target[1] - p[1], target[0] - p[0])
        arrow(d, (p[0] + 13 * math.cos(ang), p[1] + 13 * math.sin(ang)),
              (target[0] - 14 * math.cos(ang), target[1] - 14 * math.sin(ang)),
              fill=BLUE, width=3, head=11)
    text(d, (bx + SPACING / 2, by + 276), "f(x, y)", mfont(28), fill=MUTED)

    text(d, (W / 2, H - 26),
         "换个分配方式：由最接近的四个 A' 共同决定 B2 的值，就不会留下空穴",
         font(23), fill=MUTED)
    finish(im, os.path.join(out_dir, "forward-mapping-spread.png"))


# --------------------------------------------------------------------------
# 图 3：向后映射
# --------------------------------------------------------------------------
FU = (150, 22)
FV = (-32, 154)
FOFF = (26, 20)


def fig_inverse_mapping(out_dir):
    W, H = 1060, 440
    im, d = canvas(W, H)

    # 左：输入图像 g(u,v)，叠上从 f 反算回来的红色虚线格
    gx, gy = 190, 104
    ga = lattice((gx, gy), (SPACING, 0), (0, SPACING))
    draw_lattice(d, ga, [0, 1], [0, 1], BLUE_PALE, width=2, lo=-0.38, hi=1.52)

    gb = lattice((gx + FOFF[0], gy + FOFF[1]), FU, FV)
    draw_lattice(d, gb, [0, 1], [0, 1], RED_PALE, width=2, is_dashed=True,
                 lo=-0.38, hi=1.58)

    for idx, (i, j) in enumerate(CORNERS):
        p = ga(i, j)
        dot(d, p, r=8, outline=MUTED)
        sym(d, (p[0] - 14, p[1] - 18), "A", str(idx + 1), align="right")

    for idx, (i, j) in enumerate(CORNERS):
        p = gb(i, j)
        hot = idx == 0
        dot(d, p, r=7, outline=RED, fill=RED if hot else WHITE,
            dashed_ring=not hot)
        sym(d, (p[0] + 15, p[1] + 24), "B", str(idx + 1), prime=True, color=RED)
    text(d, (gx + SPACING / 2, gy + 276), "g(u, v)", mfont(28), fill=MUTED)

    arrow(d, (576, 186), (500, 186), fill=INK, width=3, head=13)

    # 右：输出图像 f(x,y) 的正交红格
    bx, by = 730, 104
    fb = lattice((bx, by), (SPACING, 0), (0, SPACING))
    draw_lattice(d, fb, [0, 1], [0, 1], RED_PALE, width=2, lo=-0.38, hi=1.52)
    for idx, (i, j) in enumerate(CORNERS):
        p = fb(i, j)
        hot = idx == 0
        dot(d, p, r=8, outline=RED if hot else MUTED,
            fill=RED if hot else DOT_FILL)
        sym(d, (p[0] + 16, p[1] + 26), "B", str(idx + 1))
    text(d, (bx + SPACING / 2, by + 276), "f(x, y)", mfont(28), fill=MUTED)

    text(d, (W / 2, H - 26),
         "向后映射：遍历 f 的每个格点，反算它在 g 上的来源 B'1，"
         "再由周围的 A 插值定出灰度",
         font(23), fill=MUTED)
    finish(im, os.path.join(out_dir, "inverse-mapping.png"))


# --------------------------------------------------------------------------
# 图 4：双线性插值
# --------------------------------------------------------------------------
def fig_bilinear(out_dir):
    """把灰度值画成高度：四个邻点的高度决定目标点的高度。"""
    W, H = 880, 520
    im, d = canvas(W, H)

    O = (470, 330)
    AU, AV, AH = (230, -38), (-116, 74), (0, -150)

    def P(u, v, h=0.0):
        return (O[0] + u * AU[0] + v * AV[0] + h * AH[0],
                O[1] + u * AU[1] + v * AV[1] + h * AH[1])

    hA = {(0, 0): 0.58, (1, 0): 1.00, (0, 1): 0.22, (1, 1): 0.44}
    t, s = 0.40, 0.46
    hR1 = hA[(0, 0)] + t * (hA[(1, 0)] - hA[(0, 0)])
    hR2 = hA[(0, 1)] + t * (hA[(1, 1)] - hA[(0, 1)])
    hB = hR1 + s * (hR2 - hR1)

    # 高度方向单独画在左侧，免得坐标轴横穿示意图
    arrow(d, (150, 400), (150, 200), fill=INK, width=3, head=13)
    text(d, (150, 176), "g(u, v)", mfont(28))
    text(d, (150, 424), "灰度值", font(22), fill=MUTED)

    # 底面上的单位格，两条邻边各引出一个方向箭头
    ring = [(0, 0), (1, 0), (1, 1), (0, 1)]
    for k in range(4):
        line(d, P(*ring[k]), P(*ring[(k + 1) % 4]), fill=BLUE_PALE, width=2)
    arrow(d, P(1.04, 0), P(1.38, 0), fill=MUTED, width=2, head=10)
    text(d, P(1.52, 0.02), "u", mfont(28), fill=MUTED)
    arrow(d, P(0, 1.04), P(0, 1.38), fill=MUTED, width=2, head=10)
    text(d, P(0.02, 1.54), "v", mfont(28), fill=MUTED)

    tops = {}
    for idx, (i, j) in enumerate(CORNERS):
        base, top = P(i, j), P(i, j, hA[(i, j)])
        line(d, base, top, fill=BLUE_PALE, width=2)
        dot(d, base, r=5, outline=BLUE_PALE, fill=WHITE, width=2)
        dot(d, top, r=7, outline=BLUE, fill=BLUE, width=2)
        tops[(i, j)] = top
        sym(d, (top[0] - 13, top[1] - 17), "A", str(idx + 1), align="right")

    # 先沿 u 方向插值：A1—A2 得 R1，A3—A4 得 R2
    dashed(d, tops[(0, 0)], tops[(1, 0)], fill=BLUE, width=2)
    dashed(d, tops[(0, 1)], tops[(1, 1)], fill=BLUE, width=2)

    R1, R2, B = P(t, 0, hR1), P(t, 1, hR2), P(t, s, hB)
    dashed(d, R1, R2, fill=RED, width=2)
    for p, name in ((R1, "1"), (R2, "2")):
        dot(d, p, r=7, outline=RED, fill=RED, width=2)
        sym(d, (p[0] - 13, p[1] - 17), "R", name, color=RED, align="right")

    line(d, P(t, s), B, fill=RED_PALE, width=2)
    dot(d, P(t, s), r=5, outline=RED_PALE, fill=WHITE, width=2)
    dot(d, B, r=8, outline=RED, fill=RED, width=2)
    sym(d, (B[0] + 16, B[1] - 12), "B", "1", prime=True, color=RED)

    text(d, (W / 2, H - 26),
         "双线性插值：先沿 u 方向插出 R1 与 R2，再在两者之间沿 v 方向插一次",
         font(23), fill=MUTED)
    finish(im, os.path.join(out_dir, "bilinear-interpolation.png"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="assets/resource/Geometric-Transform")
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)
    fig_forward_mapping(args.out)
    fig_forward_spread(args.out)
    fig_inverse_mapping(args.out)
    fig_bilinear(args.out)


if __name__ == "__main__":
    main()
