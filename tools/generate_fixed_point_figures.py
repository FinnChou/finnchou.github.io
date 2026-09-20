#!/usr/bin/env python3
"""重绘《[番外2]定点计算与浮点计算》的位域示意图。

原文（2013 年 CSDN）的三张图是 BMP 截图，分辨率与观感都停在当年，
这里按 What-is-Color 那批图的配色与版式重画一遍。

用法:
    python3 tools/generate_fixed_point_figures.py            # 写入 assets/resource/Fixed-Point-Arithmetic/
    python3 tools/generate_fixed_point_figures.py --out DIR  # 指定输出目录
"""

import argparse
import os

from PIL import Image, ImageDraw, ImageFont

# 先按 2 倍画再缩回去：PIL 的直线没有抗锯齿，降采样是最省事的补救
SS = 2

WHITE = (255, 255, 255)
PANEL = (252, 252, 253)
BORDER = (200, 207, 218)
INK = (40, 44, 52)
MUTED = (110, 118, 130)
RED = (214, 72, 72)
BLUE = (66, 122, 210)

FONT_PATH = "/System/Library/Fonts/Hiragino Sans GB.ttc"
FONT_FALLBACK = "/System/Library/Fonts/STHeiti Medium.ttc"


def font(size, bold=False):
    path = FONT_PATH if os.path.exists(FONT_PATH) else FONT_FALLBACK
    # Hiragino Sans GB.ttc 的 face 顺序：0 = W3, 2 = W6(粗)
    try:
        return ImageFont.truetype(path, size * SS, index=2 if bold else 0)
    except OSError:
        return ImageFont.truetype(path, size * SS)


def canvas(w, h):
    im = Image.new("RGB", (w * SS, h * SS), WHITE)
    return im, ImageDraw.Draw(im)


def finish(im, path):
    out = im.resize((im.width // SS, im.height // SS), Image.LANCZOS)
    out.save(path)
    print("%s  %dx%d" % (path, out.width, out.height))


def text(d, xy, s, f, fill=INK, anchor="mm"):
    d.text((xy[0] * SS, xy[1] * SS), s, font=f, fill=fill, anchor=anchor)


def rect(d, box, outline=BORDER, fill=None, width=2, radius=0):
    box = [v * SS for v in box]
    if radius:
        d.rounded_rectangle(box, radius=radius * SS, outline=outline, fill=fill,
                            width=width * SS)
    else:
        d.rectangle(box, outline=outline, fill=fill, width=width * SS)


def line(d, xy, fill=BORDER, width=2):
    d.line([v * SS for v in xy], fill=fill, width=width * SS)


def bit_row(d, x0, y, bits, cell_w, cell_h, sign_cell=True):
    """画一排位单元格；最高位（符号位）用红框标出。"""
    f = font(30)
    for i, b in enumerate(bits):
        x = x0 + i * cell_w
        is_sign = sign_cell and i == 0
        rect(d, (x, y, x + cell_w, y + cell_h), fill=PANEL,
             outline=RED if is_sign else INK, width=2)
        text(d, (x + cell_w / 2, y + cell_h / 2), b, f)
    return x0 + len(bits) * cell_w


def weight_row(d, x0, y, weights, cell_w, d_circle=52):
    """在位单元格下方画一排权重圆圈。"""
    f = font(24)
    for i, w in enumerate(weights):
        cx = x0 + i * cell_w + cell_w / 2
        d.ellipse([(cx - d_circle / 2) * SS, y * SS,
                   (cx + d_circle / 2) * SS, (y + d_circle) * SS],
                  outline=RED, width=2 * SS)
        text(d, (cx, y + d_circle / 2), w, f, fill=RED)


def point_marker(d, x, y0, y1):
    """在两列之间画一条虚拟小数点。"""
    for yy in range(int(y0), int(y1), 10):
        line(d, (x, yy, x, min(yy + 5, y1)), fill=BLUE, width=2)


# --------------------------------------------------------------------------
# 图 1：4-bit 有符号数的位权重
# --------------------------------------------------------------------------
def fig_sign_bit(out_dir):
    W, H = 1000, 420
    im, d = canvas(W, H)
    cw, ch, x0 = 118, 66, 264

    f_label = font(26)
    for i, name in enumerate(["bit3", "bit2", "bit1", "bit0"]):
        text(d, (x0 + i * cw + cw / 2, 36), name, f_label, fill=MUTED)

    x1 = bit_row(d, x0, 62, ["0", "1", "1", "0"], cw, ch)
    text(d, (x1 + 44, 62 + ch / 2), "= +6", font(30), anchor="lm")

    text(d, (x0 + cw / 2, 164), "符号位", font(22), fill=RED)
    bit_row(d, x0, 186, ["1", "0", "1", "0"], cw, ch)
    text(d, (x1 + 44, 186 + ch / 2), "= -6", font(30), anchor="lm")

    weight_row(d, x0, 274, ["-8", "4", "2", "1"], cw)

    text(d, (W / 2, 366), "最高位是符号位，它的权重是负的：+6 = 4 + 2，-6 = -8 + 2",
         font(24), fill=MUTED)
    finish(im, os.path.join(out_dir, "sign-bit-weights.png"))


# --------------------------------------------------------------------------
# 图 2：符号位扩展不改变数值
# --------------------------------------------------------------------------
def fig_sign_extension(out_dir):
    W, H = 1000, 500
    im, d = canvas(W, H)
    cw, ch = 118, 66
    x_right = 264 + 5 * cw          # 两组按 bit0 右对齐
    x4 = x_right - 4 * cw
    x5 = x_right - 5 * cw

    f_label = font(26)
    for i, name in enumerate(["bit3", "bit2", "bit1", "bit0"]):
        text(d, (x4 + i * cw + cw / 2, 34), name, f_label, fill=MUTED)
    text(d, (x4 + cw / 2, 68), "符号位", font(22), fill=RED)
    bit_row(d, x4, 90, ["1", "0", "1", "0"], cw, ch)
    text(d, (x_right + 36, 90 + ch / 2), "= -6", font(30), anchor="lm")
    weight_row(d, x4, 176, ["-8", "4", "2", "1"], cw)

    for i, name in enumerate(["bit4", "bit3", "bit2", "bit1", "bit0"]):
        text(d, (x5 + i * cw + cw / 2, 268), name, f_label, fill=MUTED)
    text(d, (x5 + cw / 2, 302), "符号位", font(22), fill=RED)
    bit_row(d, x5, 324, ["1", "1", "0", "1", "0"], cw, ch)
    text(d, (x_right + 36, 324 + ch / 2), "= -6", font(30), anchor="lm")
    weight_row(d, x5, 410, ["-16", "8", "4", "2", "1"], cw)

    text(d, (W / 2, 478), "在符号位前面补多少个 1 都一样：-16 + 8 + 2 = -8 + 2 = -6",
         font(24), fill=MUTED)
    finish(im, os.path.join(out_dir, "sign-extension.png"))


# --------------------------------------------------------------------------
# 图 3：Q3 × Q3 的竖式乘法
# --------------------------------------------------------------------------
def fig_q3_multiply(out_dir):
    W, H = 1060, 700
    im, d = canvas(W, H)
    cw, ch = 84, 62
    x0 = 130                        # 部分积区左边界
    x_right = x0 + 8 * cw
    x_top = x_right - 4 * cw        # 被乘数/乘数右对齐到最低位

    f_bit = font(28)
    f_note = font(24)

    def row(x, y, bits, sign=True, point_after=None):
        for i, b in enumerate(bits):
            bx = x + i * cw
            is_sign = sign and i == 0
            rect(d, (bx, y, bx + cw, y + ch), fill=PANEL,
                 outline=RED if is_sign else INK, width=2)
            text(d, (bx + cw / 2, y + ch / 2), b, f_bit)
        if point_after is not None:
            point_marker(d, x + point_after * cw, y - 8, y + ch + 8)

    # 被乘数与乘数，小数点在符号位之后
    row(x_top, 24, ["0", "1", "1", "0"], point_after=1)
    text(d, (x_top - 24, 24 + ch / 2), "+3/4", font(26), fill=BLUE, anchor="rm")
    row(x_top, 110, ["1", "1", "0", "0"], point_after=1)
    text(d, (x_top - 24, 110 + ch / 2), "-1/2", font(26), fill=BLUE, anchor="rm")
    text(d, (x_top - 110, 110 + ch / 2), "×", font(34), fill=INK)

    line(d, (x0 - 20, 194, x_right + 10, 194), fill=INK, width=2)

    # 部分积：乘数每高一位，部分积就左移一格，所以行越靠下越短
    partials = [
        (["0", "0", "0", "0", "0", "0", "0", "0"], False),
        (["0", "0", "0", "0", "0", "0", "0"], False),
        (["0", "0", "0", "1", "1", "0"], False),
        (["1", "1", "0", "1", "0"], False),
    ]
    y = 212
    for bits, sign in partials:
        row(x0, y, bits, sign=sign)
        y += ch + 8
    y_last = y - ch - 8

    text(d, (x0 - 34, y_last + ch / 2), "+", font(34), fill=INK)
    # 最后一行是符号位那一路：乘的是权重 -1 的位，所以取被乘数的补码
    rect(d, (x0 - 6, y_last - 6, x0 + 5 * cw + 6, y_last + ch + 6),
         outline=RED, width=2)
    text(d, (x0 + 5 * cw + 24, y_last + ch / 2), "符号位这一路取补码",
         f_note, fill=RED, anchor="lm")

    line(d, (x0 - 20, y + 6, x_right + 10, y + 6), fill=INK, width=2)

    y_sum = y + 24
    row(x0, y_sum, ["1", "1", "1", "0", "1", "0", "0", "0"],
        sign=False, point_after=2)
    text(d, (x_right + 24, y_sum + ch / 2), "Q6", font(26), fill=MUTED, anchor="lm")

    # 结果按 Q3 取：留一个符号位 + 3 位小数
    rect(d, (x0 + cw - 6, y_sum - 6, x0 + 5 * cw + 6, y_sum + ch + 6),
         outline=BLUE, width=2)
    text(d, (W / 2, y_sum + ch + 40),
         "按 Q3 取出结果：1.101 = -1 + 1/2 + 1/8 = -3/8", font(24), fill=BLUE)

    text(d, (W / 2, H - 28),
         "两个 Q3 相乘得到 Q6；高位多出来的符号位丢掉，就回到 Q3",
         font(24), fill=MUTED)
    finish(im, os.path.join(out_dir, "q3-multiplication.png"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="assets/resource/Fixed-Point-Arithmetic")
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)
    fig_sign_bit(args.out)
    fig_sign_extension(args.out)
    fig_q3_multiply(args.out)


if __name__ == "__main__":
    main()
